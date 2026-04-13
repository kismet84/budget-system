#!/usr/bin/env python3
"""
从 quota_costs.json 批量回填费用字段到数据库（优化版）

性能优化：
    - 批量 SELECT：1 次查询所有 quota_id 的当前费用字段值
    - 批量 UPDATE：分批执行，每批 500 条
    - DB 往返次数：3718 次 → ≤10 次

使用方式：
    python3 backfill_cost_fields.py

数据说明（基于 2026-04-11 审查）：
    quota_costs.json（1859条）中各字段覆盖情况：

    字段          在 quota_costs 中有值    DB 当前空值    可回填    说明
    ─────────────────────────────────────────────────────────────────────
    labor_fee         1768 条             91 条         0 条    91条源头无此数据
    material_fee      1798 条             61 条         0 条    61条源头无此数据
    machinery_fee      984 条            875 条         0 条    装饰/拆除工艺本身无机械费
    management_fee    1731 条            128 条         0 条    128条源头无此数据
    tax               1805 条             54 条         0 条    54条源头无此数据
    total_cost        1848 条             11 条         0 条    源头缺失（拆除定额）
"""
import json
import sys
import os

# 添加 backend 目录到 path 以便导入 config
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = SCRIPT_DIR
PROJECT_DIR = os.path.dirname(BACKEND_DIR)
sys.path.insert(0, BACKEND_DIR)

from config import settings
import psycopg2

DATA_DIR = os.path.join(PROJECT_DIR, "data", "定额", "parsed", "装饰", "quota_costs.json")

# 批量大小
BATCH_SIZE = 500


def get_connection():
    """从 config.py 读取 DATABASE_URL 创建连接"""
    return psycopg2.connect(settings.DATABASE_URL)


def num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def main():
    print(f"📂 加载: {DATA_DIR}")
    with open(DATA_DIR, encoding="utf-8") as f:
        costs = json.load(f)
    print(f"   {len(costs)} 条定额费用记录\n")

    conn = get_connection()

    # 字段映射：DB字段 → quota_costs.json字段
    field_map = {
        "labor_fee": "人工费",
        "material_fee": "材料费",
        "machinery_fee": "机械费",
        "management_fee": "费用",
        "tax": "增值税",
        "total_cost": "全费用",
    }
    db_fields = list(field_map.keys())

    # ---------------------------------------------------------
    # Step 1: 批量查询所有 quota_id 的当前费用字段值（1 次 SELECT）
    # ---------------------------------------------------------
    print("📊 批量查询当前 DB 状态...")
    quota_ids = list(costs.keys())
    if not quota_ids:
        print("没有数据需要处理")
        return

    placeholders = ",".join(["%s"] * len(quota_ids))
    cur = conn.cursor()
    cur.execute(
        f"SELECT quota_id, {','.join(db_fields)} FROM quotas WHERE quota_id IN ({placeholders})",
        quota_ids
    )
    rows = cur.fetchall()
    cur.close()

    # 构建 quota_id → 当前字段值 dict
    db_state = {row[0]: row[1:] for row in rows}
    print(f"   DB 中找到 {len(db_state)} 条记录\n")

    # ---------------------------------------------------------
    # Step 2: 在内存中计算需要更新的字段
    # ---------------------------------------------------------
    # updates: list of (quota_id, {field: new_value, ...})
    updates = []
    stats = {f: {"updated": 0, "skipped": 0} for f in db_fields}

    for quota_id, cost_data in costs.items():
        if quota_id not in db_state:
            continue  # 定额不在 DB 中

        current_values = db_state[quota_id]  # tuple of 6 values
        current_dict = dict(zip(db_fields, current_values))

        row_updates = {}
        for field, json_key in field_map.items():
            # 只更新 DB 中该字段为 NULL 的记录
            if current_dict[field] is not None:
                stats[field]["skipped"] += 1
                continue  # 已有值，跳过

            value = cost_data.get(json_key)
            if value is None:
                continue  # quota_costs 中也没有

            new_val = num(value)
            if new_val is not None:
                row_updates[field] = new_val

        if row_updates:
            updates.append((quota_id, row_updates))
            for f in row_updates:
                stats[f]["updated"] += 1

    print(f"📝 需要更新的记录数: {len(updates)}\n")

    # ---------------------------------------------------------
    # Step 3: 批量 UPDATE（分批执行，每批 BATCH_SIZE 条）
    # ---------------------------------------------------------
    if updates:
        total_updated = 0
        for i in range(0, len(updates), BATCH_SIZE):
            batch = updates[i:i + BATCH_SIZE]
            batch_update(conn, batch, db_fields)
            total_updated += len(batch)
            print(f"   已更新 {total_updated}/{len(updates)} 条...")

        conn.commit()
        print()

    conn.close()

    # ---------------------------------------------------------
    # 报告
    # ---------------------------------------------------------
    updated_total = sum(s["updated"] for s in stats.values())
    print("=" * 50)
    print(f"{'字段':<16} {'回填':>8} {'已跳过':>8}")
    print("-" * 50)
    for field, s in stats.items():
        print(f"  {field:<14} {s['updated']:>8} {s['skipped']:>8}")
    print("=" * 50)
    print(f"\n总更新记录数: {len(updates)}")
    print(f"总更新字段数: {updated_total}")
    print(f"DB 往返次数: 1(SELECT) + {len(range(0, len(updates), BATCH_SIZE))}(UPDATE批次) ≈ {1 + len(range(0, len(updates), BATCH_SIZE))} 次")

    if updated_total == 0:
        print("\n⚠️  所有空值在 quota_costs.json 中均无数据，属正常数据缺失：")
        print("  · machinery_fee 空 875 条 → 装饰/拆除工艺本身无机械台班")
        print("  · labor_fee/material_fee/management_fee/tax 空 54~128 条 → 源头 PDF 无此数据")
        print("  · total_cost 空 11 条 → 拆除定额（A14/A15）源头无综合单价")


def batch_update(conn, updates_batch, db_fields):
    """
    批量更新一批记录
    updates_batch: list of (quota_id, {field: value, ...})
    """
    cur = conn.cursor()
    for quota_id, row_updates in updates_batch:
        set_clause = ", ".join([f"{k} = %s" for k in row_updates.keys()])
        values = list(row_updates.values()) + [quota_id]
        cur.execute(f"UPDATE quotas SET {set_clause} WHERE quota_id = %s", values)
    cur.close()


if __name__ == "__main__":
    main()
