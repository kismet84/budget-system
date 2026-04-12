"""
价格聚合服务
从 materials 表聚合材料单价，结合信息价做参考报价
"""
import psycopg2
from typing import List, Optional
from config import settings


def get_connection():
    return psycopg2.connect(settings.DATABASE_URL)


def aggregate_material_prices(quota_id: str) -> dict:
    """
    聚合指定定额的材料单价

    Args:
        quota_id: 定额编号

    Returns:
        dict: {
            "materials": [...],
            "total_material_cost": float,
            "unit": str
        }
    """
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT
            m.name,
            m.unit,
            m.unit_price,
            m.consumption,
            m.mat_type,
            q.unit as quota_unit
        FROM materials m
        JOIN quotas q ON m.quota_id = q.quota_id
        WHERE m.quota_id = %s
        ORDER BY m.mat_type, m.name
        """,
        (quota_id,)
    )
    rows = cur.fetchall()

    materials = []
    total_cost = 0.0

    for row in rows:
        name, unit, unit_price, consumption, mat_type, quota_unit = row
        cost = float(unit_price or 0) * float(consumption or 0)
        total_cost += cost
        materials.append({
            "name": name,
            "unit": unit,
            "unit_price": float(unit_price or 0),
            "consumption": float(consumption or 0),
            "cost": round(cost, 2),
            "type": mat_type
        })

    cur.close()
    conn.close()

    return {
        "quota_id": quota_id,
        "materials": materials,
        "total_material_cost": round(total_cost, 2),
        "quota_unit": rows[0][5] if rows else None
    }


def aggregate_top_quotas(quota_results: List[dict]) -> List[dict]:
    """
    对多个定额结果批量聚合材料价格（N+1 查询优化：单次 JOIN）

    Args:
        quota_results: 向量搜索返回的定额列表

    Returns:
        List[dict]: 每个定额加上材料价格聚合结果
    """
    if not quota_results:
        return []

    # 收集所有 quota_id，一次查询
    quota_ids = [q["quota_id"] for q in quota_results]

    conn = get_connection()
    cur = conn.cursor()

    # 批量 JOIN 查询
    cur.execute("""
        SELECT
            m.quota_id,
            m.name,
            m.unit,
            m.unit_price,
            m.consumption,
            m.mat_type,
            q.unit as quota_unit
        FROM materials m
        JOIN quotas q ON m.quota_id = q.quota_id
        WHERE m.quota_id = ANY(%s)
        ORDER BY m.quota_id, m.mat_type, m.name
    """, (quota_ids,))

    rows = cur.fetchall()
    cur.close()
    conn.close()

    # 按 quota_id 分组
    materials_by_quota: dict[str, list] = {}
    quota_units: dict[str, str] = {}

    for row in rows:
        qid, name, unit, unit_price, consumption, mat_type, quota_unit = row
        if qid not in materials_by_quota:
            materials_by_quota[qid] = []
            quota_units[qid] = quota_unit
        cost = float(unit_price or 0) * float(consumption or 0)
        materials_by_quota[qid].append({
            "name": name,
            "unit": unit,
            "unit_price": float(unit_price or 0),
            "consumption": float(consumption or 0),
            "cost": round(cost, 2),
            "type": mat_type
        })

    # 聚合到每个定额
    enriched = []
    for q in quota_results:
        qid = q["quota_id"]
        materials = materials_by_quota.get(qid, [])
        total_material_cost = round(sum(m["cost"] for m in materials), 2)
        has_materials = len(materials) > 0
        material_price_missing = has_materials and total_material_cost == 0

        if material_price_missing:
            reference_price = None
        else:
            reference_price = total_material_cost

        enriched.append({
            **q,
            "materials": materials,
            "total_material_cost": total_material_cost,
            "quota_unit": quota_units.get(qid),
            "reference_price": reference_price,
            "material_price_missing": material_price_missing,
        })

    return enriched


def format_quota_response(quota: dict) -> dict:
    """格式化定额响应，用于 API 返回"""
    result = {
        "quota_id": quota["quota_id"],
        "category": quota["category"],
        "work_content": quota["work_content"],
        "section": quota["section"],
        "unit": quota.get("quota_unit") or quota.get("unit"),
        "total_cost": quota["total_cost"],
        "labor_fee": quota.get("labor_fee"),
        "material_fee": quota.get("material_fee"),
        "machinery_fee": quota.get("machinery_fee"),
        "management_fee": quota.get("management_fee"),
        "tax": quota.get("tax"),
        "project_name": quota.get("project_name"),
        "similarity": quota.get("similarity"),
        "materials_count": len(quota.get("materials", [])),
        "total_material_cost": quota.get("total_material_cost"),
        "reference_price": quota.get("reference_price"),
        "material_price_missing": quota.get("material_price_missing", False),
    }
    return result
