#!/usr/bin/env python3
"""
从 quota_costs.json 回填费用字段到数据库（增量版）

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
import psycopg2
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.dirname(SCRIPT_DIR)
PROJECT_DIR = os.path.dirname(BACKEND_DIR)
DATA_DIR = os.path.join(PROJECT_DIR, "data", "定额", "parsed", "装饰", "quota_costs.json")


def get_connection():
    return psycopg2.connect(host="localhost", port=5432, dbname="budget_system", user="kis")


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
    stats = {f: {"updated": 0, "skipped": 0} for f in ["labor_fee", "material_fee",
                                                         "machinery_fee", "management_fee",
                                                         "tax", "total_cost"]}

    # 字段映射：DB字段 → quota_costs.json字段
    field_map = {
        "labor_fee": "人工费",
        "material_fee": "材料费",
        "machinery_fee": "机械费",
        "management_fee": "费用",
        "tax": "增值税",
        "total_cost": "全费用",
    }

    updated_total = 0

    for quota_id, cost_data in costs.items():
        updates = {}
        for field, json_key in field_map.items():
            # 只更新 DB 中该字段为 NULL 的记录
            cur = conn.cursor()
            cur.execute(f"SELECT {field} FROM quotas WHERE quota_id = %s", (quota_id,))
            row = cur.fetchone()
            cur.close()

            if row is None:
                continue  # 定额不在 DB 中
            if row[0] is not None:
                stats[field]["skipped"] += 1
                continue  # 已有值，跳过

            value = cost_data.get(json_key)
            if value is None:
                continue  # quota_costs 中也没有

            new_val = num(value)
            if new_val is not None:
                updates[field] = new_val

        if not updates:
            continue

        set_clause = ", ".join([f"{k} = %s" for k in updates.keys()])
        values = list(updates.values()) + [quota_id]
        cur = conn.cursor()
        cur.execute(f"UPDATE quotas SET {set_clause} WHERE quota_id = %s", values)
        cur.close()

        for f in updates:
            stats[f]["updated"] += 1
        updated_total += len(updates)

    conn.commit()
    conn.close()

    # 报告
    print("=" * 50)
    print(f"{'字段':<16} {'回填':>8} {'已跳过':>8}")
    print("-" * 50)
    for field, s in stats.items():
        print(f"  {field:<14} {s['updated']:>8} {s['skipped']:>8}")
    print("=" * 50)
    print(f"\n总更新字段数: {updated_total}")

    if updated_total == 0:
        print("\n⚠️  所有空值在 quota_costs.json 中均无数据，属正常数据缺失：")
        print("  · machinery_fee 空 875 条 → 装饰/拆除工艺本身无机械台班")
        print("  · labor_fee/material_fee/management_fee/tax 空 54~128 条 → 源头 PDF 无此数据")
        print("  · total_cost 空 11 条 → 拆除定额（A14/A15）源头无综合单价")


if __name__ == "__main__":
    main()
