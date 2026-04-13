#!/usr/bin/env python3
"""
将信息价 indexed JSON 文件导入 material_prices 表
- 读取 data/信息价/indexed/价格索引/ 下的 JSON 文件（每城市每月一个）
- 解析材料名称、规格、单位、单价
- 批量 INSERT（ON CONFLICT DO UPDATE）
- 输出导入统计
"""
import json
import os
import sys
import psycopg2
import argparse
from pathlib import Path
from urllib.parse import urlparse
from datetime import datetime
from typing import Dict, List, Any

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


def parse_date_from_filename(filename: str) -> str:
    """从文件名如 2026-01.json 提取日期"""
    try:
        date_str = filename.replace('.json', '')
        dt = datetime.strptime(date_str, '%Y-%m')
        return dt.strftime('%Y-%m-%d')
    except ValueError:
        return datetime.now().strftime('%Y-%m-%d')


def import_info_prices(indexed_dir: str, price_type: str = "信息价"):
    """
    导入信息价 JSON 文件到 material_prices 表
    
    JSON 格式：
    {
        "材料名称": [
            {"name": "...", "spec": "...", "unit": "...", "code": "...", "city": "...", "price": 123.45, "price_naked": 123.45},
            ...
        ]
    }
    """
    indexed_path = Path(indexed_dir)
    if not indexed_path.exists():
        raise FileNotFoundError(f"目录不存在: {indexed_dir}")

    # 收集所有待导入记录
    all_records: List[Dict[str, Any]] = []
    json_files = sorted(indexed_path.glob("*.json"))
    
    print(f"📂 扫描目录: {indexed_path}")
    print(f"   找到 {len(json_files)} 个月份文件")

    for json_file in json_files:
        publication_date = parse_date_from_filename(json_file.name)
        print(f"\n📄 处理: {json_file.name} (发布日期: {publication_date})")
        
        with open(json_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        for material_name, price_list in data.items():
            for item in price_list:
                all_records.append({
                    "name": item.get("name", material_name),
                    "specification": item.get("spec", ""),
                    "unit": item.get("unit", ""),
                    "unit_price": num(item.get("price")),
                    "price_type": price_type,
                    "region": item.get("city", "武汉市"),
                    "publication_date": publication_date,
                    "source": item.get("code", ""),
                    "is_active": True,
                    "remarks": f"价税合计: {item.get('price')}, 不含税: {item.get('price_naked')}",
                })

    print(f"\n📊 共收集 {len(all_records)} 条价格记录")

    if len(all_records) == 0:
        print("⚠️  没有找到任何价格数据")
        return

    # 批量导入
    conn = get_connection()
    imported = 0
    updated = 0
    errors = 0
    batch_size = 500

    print(f"\n🔄 开始批量导入 (每批 {batch_size} 条)...")

    for i in range(0, len(all_records), batch_size):
        batch = all_records[i:i + batch_size]
        batch_num = i // batch_size + 1
        
        try:
            with conn.cursor() as cur:
                for record in batch:
                    # 使用 name + specification + unit + region + price_type + publication_date 作为唯一键
                    cur.execute("""
                        INSERT INTO material_prices (
                            name, specification, unit, unit_price,
                            price_type, region, publication_date,
                            source, is_active, remarks
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (name, specification, unit, region, price_type, publication_date) 
                        DO UPDATE SET
                            unit_price = EXCLUDED.unit_price,
                            source = EXCLUDED.source,
                            remarks = EXCLUDED.remarks,
                            is_active = EXCLUDED.is_active
                    """, (
                        record["name"],
                        record["specification"],
                        record["unit"],
                        record["unit_price"],
                        record["price_type"],
                        record["region"],
                        record["publication_date"],
                        record["source"],
                        record["is_active"],
                        record["remarks"],
                    ))
                    
                    if cur.rowcount > 0:
                        # ON CONFLICT DO UPDATE 时，rowcount 为 1 表示更新了已存在的记录
                        # 我们需要用另一个查询来判断是插入还是更新
                        pass

            conn.commit()
            
            # 判断插入还是更新（通过查询刚插入的记录）
            with conn.cursor() as cur:
                for record in batch:
                    cur.execute("""
                        SELECT id FROM material_prices 
                        WHERE name = %s AND specification = %s AND unit = %s 
                        AND region = %s AND price_type = %s AND publication_date = %s
                    """, (
                        record["name"],
                        record["specification"],
                        record["unit"],
                        record["region"],
                        record["price_type"],
                        record["publication_date"],
                    ))
                    result = cur.fetchone()
                    if result:
                        # 检查是否是本次导入新加的（通过 source 匹配）
                        if record["source"] in (result[0] or ""):
                            imported += 1
                        else:
                            updated += 1

            print(f"   批次 {batch_num}: 已处理 {min(i + batch_size, len(all_records))}/{len(all_records)} 条")

        except Exception as e:
            errors += len(batch)
            conn.rollback()
            print(f"   ❌ 批次 {batch_num} 错误: {e}")

    conn.close()

    print(f"\n✅ 导入完成！")
    print(f"   总记录数: {len(all_records)}")
    print(f"   导入成功: {imported} 条")
    print(f"   更新成功: {updated} 条")
    print(f"   错误: {errors} 条")


# ===== CLI =====
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="导入信息价 JSON 数据到 material_prices 表")
    parser.add_argument(
        "--dir", "-d",
        default=str(_PROJECT_ROOT / "data" / "信息价" / "indexed" / "价格索引"),
        help="信息价 JSON 文件目录"
    )
    parser.add_argument(
        "--type", "-t",
        default="信息价",
        choices=["信息价", "企业价"],
        help="价格类型"
    )
    args = parser.parse_args()

    if not os.path.exists(args.dir):
        print(f"❌ 目录不存在: {args.dir}")
        sys.exit(1)

    conn_test = get_connection()
    print(f"✅ 数据库连接成功（budget_system）")
    conn_test.close()

    import_info_prices(args.dir, args.type)
