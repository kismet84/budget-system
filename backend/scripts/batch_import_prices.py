#!/usr/bin/env python3
"""
批量导入信息价 Excel 到数据库
用法: python batch_import_prices.py [--dry-run]
"""
import sys, json, os
from pathlib import Path
from urllib.parse import urlparse

SCRIPT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = SCRIPT_DIR.parent
PROJECT_DIR = BACKEND_DIR.parent

sys.path.insert(0, str(BACKEND_DIR))
from scripts.parse_info_price import parse_xlsx
from config import settings
import psycopg2

# 数据库连接
parsed = urlparse(settings.DATABASE_URL)
DB = {
    "host": parsed.hostname or "localhost",
    "port": parsed.port or 5432,
    "database": parsed.path.lstrip("/") or "budget_system",
    "user": parsed.username or "kis",
    "password": parsed.password or "",
}

RAW_DIR = PROJECT_DIR / "data" / "信息价" / "raw"


def import_file(filepath: Path, dry_run: bool = False):
    """解析并导入单个 Excel 文件"""
    month_str = filepath.stem
    print(f"\n{'[DRY-RUN] ' if dry_run else ''}处理: {filepath.name}")

    try:
        records = parse_xlsx(str(filepath))
    except Exception as e:
        print(f"  解析失败: {e}")
        return 0, 0, 0

    if not records:
        print("  ⚠️ 无数据")
        return 0, 0, 0

    print(f"  解析出 {len(records)} 条记录")

    if dry_run:
        return len(records), 0, 0

    conn = psycopg2.connect(**DB)
    cur = conn.cursor()

    imported = 0
    skipped = 0
    errors = []

    for i, row in enumerate(records):
        try:
            # 正确字段名：含税价（不是含税信息价）
            unit_price = row.get("含税价")
            if unit_price is None or unit_price <= 0:
                skipped += 1
                continue

            pub_date = row.get("月份", "")
            if pub_date:
                # "2025-02" → date
                try:
                    pub_date = f"{pub_date[:4]}-{pub_date[5:7]}-01"
                except Exception:
                    pub_date = None
            else:
                pub_date = None

            cur.execute(
                """
                INSERT INTO material_prices
                  (name, specification, unit, unit_price, price_type, region, publication_date, source)
                VALUES
                  (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT DO NOTHING
                """,
                (
                    row.get("材料名称", "").strip(),
                    row.get("规格及型号", "").strip(),
                    row.get("单位", "").strip(),
                    unit_price,
                    "信息价",
                    row.get("城市", "武汉市").strip(),
                    pub_date,
                    f"湖北数字造价平台/{filepath.name}",
                ),
            )
            if cur.rowcount > 0:
                imported += 1
            else:
                skipped += 1

        except Exception as e:
            errors.append(f"行{i+1}: {e}")
            skipped += 1

    conn.commit()
    conn.close()

    print(f"  ✅ 导入: {imported}, 跳过: {skipped}, 错误: {len(errors)}")
    if errors[:5]:
        for e in errors[:5]:
            print(f"    {e}")

    return len(records), imported, skipped


def main():
    dry_run = "--dry-run" in sys.argv
    if dry_run:
        print("=== DRY RUN 模式 ===\n")

    xlsx_files = sorted(RAW_DIR.glob("*.xlsx"))
    if not xlsx_files:
        print(f"未找到 Excel 文件: {RAW_DIR}")
        return

    print(f"共 {len(xlsx_files)} 个文件")

    grand_total = 0
    grand_imported = 0
    grand_skipped = 0

    for fp in xlsx_files:
        total, imported, skipped = import_file(fp, dry_run=dry_run)
        grand_total += total
        grand_imported += imported
        grand_skipped += skipped

    print(f"\n{'='*50}")
    print(f"总计: 解析 {grand_total}, 导入 {grand_imported}, 跳过 {grand_skipped}")
    if dry_run:
        print("(dry-run 模式，未实际写入)")


if __name__ == "__main__":
    main()
