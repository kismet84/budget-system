"""
市场价重算服务
给定一个定额的材料明细，按当前市场价重新计算材料费
"""
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional


def match_market_price(
    db: Session,
    material_name: str,
    unit: str,
    region: str = "武汉市",
    price_type: str = "信息价",
) -> Optional[dict]:
    """
    在 material_prices 中匹配材料的当前市场价。

    匹配策略（优先级递减）：
    1. 名称完全一致 + 单位一致 → 最新一条
    2. 名称包含匹配 + 单位一致 → 最新一条
    3. 名称模糊匹配（ILIKE） → 取相似度最高的

    Returns: {"name", "specification", "unit_price", "publication_date"} 或 None
    """
    # 策略1：名称精确匹配
    row = db.execute(
        text("""
            SELECT name, specification, unit, unit_price, publication_date
            FROM material_prices
            WHERE name = :name
              AND unit = :unit
              AND region = :region
              AND price_type = :price_type
              AND is_active = true
            ORDER BY publication_date DESC
            LIMIT 1
        """),
        {"name": material_name, "unit": unit, "region": region, "price_type": price_type},
    ).fetchone()

    if row:
        return {"name": row[0], "specification": row[1], "unit_price": row[3], "publication_date": row[4]}

    # 策略2：名称包含匹配
    row = db.execute(
        text("""
            SELECT name, specification, unit, unit_price, publication_date
            FROM material_prices
            WHERE name LIKE :name_like
              AND unit = :unit
              AND region = :region
              AND price_type = :price_type
              AND is_active = true
            ORDER BY publication_date DESC
            LIMIT 1
        """),
        {"name_like": f"%{material_name}%", "unit": unit, "region": region, "price_type": price_type},
    ).fetchone()

    if row:
        return {"name": row[0], "specification": row[1], "unit_price": row[3], "publication_date": row[4]}

    return None


def analyze_quota_market_price(
    db: Session,
    quota_id: str,
    region: str = "武汉市",
    price_type: str = "信息价",
) -> dict:
    """
    分析一个定额的当前市场价材料费 vs PDF 标准材料费。

    Returns:
    {
        "quota_id": str,
        "region": str,
        "price_type": str,
        "pdf_material_fee": float,          # PDF 标准材料费
        "market_material_fee": float,       # 市场价重算材料费
        "variance": float,                  # 差额（市场价 - PDF）
        "variance_pct": float,              # 涨跌幅度 %
        "materials": [
            {
                "name": str,
                "unit": str,
                "pdf_price": float,         # PDF 定额单价
                "market_price": float | None,# 市场价（未找到为 null）
                "consumption": float,
                "pdf_cost": float,           # pdf_price × consumption
                "market_cost": float | None, # market_price × consumption
                "matched": bool,             # 是否匹配到市场价
                "market_name": str | None,   # 匹配到的市场材料名
            },
            ...
        ],
        "unmatched_count": int,
    }
    """
    # 取定额的标准材料费
    quota_row = db.execute(
        text("SELECT material_fee FROM quotas WHERE quota_id = :quota_id"),
        {"quota_id": quota_id},
    ).fetchone()

    pdf_material_fee = quota_row[0] if quota_row else 0.0

    # 取材料明细
    material_rows = db.execute(
        text("""
            SELECT name, unit, unit_price, consumption
            FROM materials
            WHERE quota_id = :quota_id
        """),
        {"quota_id": quota_id},
    ).fetchall()

    if not material_rows:
        return {
            "quota_id": quota_id,
            "region": region,
            "price_type": price_type,
            "pdf_material_fee": pdf_material_fee,
            "market_material_fee": 0.0,
            "variance": 0.0,
            "variance_pct": 0.0,
            "materials": [],
            "unmatched_count": 0,
        }

    materials = []
    total_market_cost = 0.0
    unmatched = 0

    for row in material_rows:
        name, unit, pdf_price, consumption = row[0], row[1], row[2] or 0.0, row[3] or 0.0
        pdf_cost = pdf_price * consumption

        matched_price = match_market_price(db, name, unit, region, price_type)
        if matched_price:
            market_cost = matched_price["unit_price"] * consumption
            total_market_cost += market_cost
            materials.append({
                "name": name,
                "unit": unit,
                "pdf_price": pdf_price,
                "market_price": matched_price["unit_price"],
                "consumption": consumption,
                "pdf_cost": round(pdf_cost, 4),
                "market_cost": round(market_cost, 4),
                "matched": True,
                "market_name": matched_price["name"],
            })
        else:
            unmatched += 1
            materials.append({
                "name": name,
                "unit": unit,
                "pdf_price": pdf_price,
                "market_price": None,
                "consumption": consumption,
                "pdf_cost": round(pdf_cost, 4),
                "market_cost": None,
                "matched": False,
                "market_name": None,
            })

    variance = total_market_cost - (pdf_material_fee or 0.0)
    variance_pct = (variance / pdf_material_fee * 100) if pdf_material_fee else 0.0

    return {
        "quota_id": quota_id,
        "region": region,
        "price_type": price_type,
        "pdf_material_fee": pdf_material_fee,
        "market_material_fee": round(total_market_cost, 4),
        "variance": round(variance, 4),
        "variance_pct": round(variance_pct, 2),
        "materials": materials,
        "unmatched_count": unmatched,
    }
