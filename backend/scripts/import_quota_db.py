#!/usr/bin/env python3
"""
将合并后的定额数据（装饰_合并定额.json）导入 PostgreSQL 数据库
- quotas 表：主定额记录
- materials 表：材料明细 + 机械台班
"""
import json
import os
import sys
import psycopg2
import argparse
from pathlib import Path
from urllib.parse import urlparse

# ===== 项目根目录（scripts/ → backend/ → 项目根）=====
_SCRIPT_DIR = Path(__file__).parent.resolve()
_BACKEND_DIR = _SCRIPT_DIR.parent
_PROJECT_ROOT = _BACKEND_DIR.parent
sys.path.insert(0, str(_BACKEND_DIR))

from config import settings

# ===== 数据库连接 =====
def get_connection():
    """解析 DATABASE_URL 构建 psycopg2 连接参数"""
    parsed = urlparse(settings.DATABASE_URL)
    if parsed.hostname in (None, "localhost", "127.0.0.1"):
        # Unix socket 连接（macOS Postgres.app 默认）
        return psycopg2.connect(
            host="/tmp" if Path("/tmp/.s.PGSQL.5432").exists() else None,
            port=None,
            database=parsed.path.lstrip("/") or "budget_system",
            user=parsed.username or "kis",
            password=parsed.password or "",
        )
    return psycopg2.connect(
        host=parsed.hostname,
        port=parsed.port or 5432,
        database=parsed.path.lstrip("/") or "budget_system",
        user=parsed.username or "kis",
        password=parsed.password or "",
    )

# ===== 辅助函数 =====
def num(v):
    """安全转浮点数"""
    try:
        return float(v)
    except (TypeError, ValueError):
        return None

# ===== 主导入逻辑 =====
def import_data(json_path: str):
    conn = get_connection()
    print(f"📂 加载: {json_path}")

    with open(json_path, "r", encoding="utf-8") as f:
        records = json.load(f)

    print(f"   共 {len(records)} 条记录")

    imported = 0
    skipped = 0
    quota_errors = 0
    mat_imported = 0

    for r in records:
        quota_id = r.get("定额编号")
        if not quota_id:
            continue

        try:
            with conn.cursor() as cur:
                # ---- 插入 quotas 表 ----
                cur.execute("""
                    INSERT INTO quotas (
                        quota_id, category, unit, quantity, project_name, work_content, section,
                        total_cost, labor_fee, material_fee, machinery_fee,
                        management_fee, tax,
                        source_file
                    ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    ON CONFLICT (quota_id) DO NOTHING
                """, (
                    quota_id,
                    r.get("category"),
                    r.get("计量单位"),
                    r.get("计量数量"),
                    r.get("项目名称"),
                    r.get("工作内容"),
                    r.get("section"),
                    num(r.get("全费用")),
                    num(r.get("其中人工费")),
                    num(r.get("材料费")),
                    num(r.get("机械费")),
                    num(r.get("费用")),
                    num(r.get("增值税")),
                    r.get("source_file"),
                ))

                if cur.rowcount == 0:
                    skipped += 1
                    continue

                # ---- 插入 materials 表（材料明细）----
                for m in r.get("材料明细") or []:
                    mat_name = m.get("名称", "").replace("【机械】", "").strip()
                    cur.execute("""
                        INSERT INTO materials
                            (quota_id, name, unit, unit_price, consumption, mat_type)
                        VALUES (%s,%s,%s,%s,%s,%s)
                    """, (
                        quota_id,
                        mat_name,
                        m.get("单位"),
                        num(m.get("单价(元)")),
                        num(m.get("消耗量")),
                        "材料",
                    ))
                    mat_imported += 1

                # ---- 插入 materials 表（机械台班）----
                for m in r.get("机械明细") or []:
                    mat_name = m.get("名称", "").replace("【机械】", "").replace("【机械台班】", "").strip()
                    cur.execute("""
                        INSERT INTO materials
                            (quota_id, name, unit, unit_price, consumption, mat_type)
                        VALUES (%s,%s,%s,%s,%s,%s)
                    """, (
                        quota_id,
                        mat_name,
                        m.get("单位"),
                        num(m.get("单价(元)")),
                        num(m.get("消耗量")),
                        "机械",
                    ))
                    mat_imported += 1

            conn.commit()
            imported += 1

        except Exception as e:
            quota_errors += 1
            conn.rollback()
            if quota_errors <= 5:
                print(f"   ❌ {quota_id}: {e}")

    conn.close()

    print(f"\n✅ 导入完成！")
    print(f"   quotas:   {imported} 条导入，{skipped} 条跳过（已存在）")
    print(f"   materials: {mat_imported} 条导入")
    if quota_errors > 0:
        print(f"   错误: {quota_errors} 条")

# ===== CLI =====
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="导入合并定额数据到 PostgreSQL")
    parser.add_argument(
        "json_path",
        nargs="?",
        default=str(Path(__file__).parent.parent.parent
                    / "data" / "定额" / "imported" / "装饰_合并定额.json"),
        help="合并后的 JSON 文件路径"
    )
    args = parser.parse_args()

    if not os.path.exists(args.json_path):
        print(f"❌ 文件不存在: {args.json_path}")
        sys.exit(1)

    conn_test = get_connection()
    print(f"✅ 数据库连接成功（budget_system）")
    conn_test.close()

    import_data(args.json_path)
