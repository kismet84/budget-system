"""
数据质量报告路由
提供定额和材料价格的数据覆盖率、缺失字段、价格有效期等统计
"""
from fastapi import APIRouter, Depends
from sqlalchemy import func, text, case
from sqlalchemy.orm import Session
from datetime import date, timedelta
from typing import List, Dict, Any

from database import get_db
from models.quota import Quota
from models.price import MaterialPrice

router = APIRouter(prefix="/admin", tags=["管理功能"])


@router.get("/report")
async def get_data_report(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    返回数据质量报告 JSON
    包含：数据覆盖率、缺失字段统计、分部统计、价格统计、有效期标注
    """
    today = date.today()
    thirty_days_ago = today - timedelta(days=30)

    # ── 1. 数据覆盖率 ──────────────────────────────────────
    quota_total = db.query(func.count(Quota.id)).scalar() or 0
    material_price_total = db.query(func.count(MaterialPrice.id)).scalar() or 0

    # ── 2. 定额缺失字段统计 ────────────────────────────────
    missing_fields = {
        "quota_id": db.query(func.count(Quota.id)).filter(Quota.quota_id == None).scalar(),
        "unit": db.query(func.count(Quota.id)).filter(Quota.unit == None).scalar(),
        "total_cost": db.query(func.count(Quota.id)).filter(Quota.total_cost == None).scalar(),
        "labor_fee": db.query(func.count(Quota.id)).filter(Quota.labor_fee == None).scalar(),
        "material_fee": db.query(func.count(Quota.id)).filter(Quota.material_fee == None).scalar(),
        "machinery_fee": db.query(func.count(Quota.id)).filter(Quota.machinery_fee == None).scalar(),
        "section": db.query(func.count(Quota.id)).filter(Quota.section == None).scalar(),
    }

    # ── 3. 定额分部统计 ────────────────────────────────────
    section_stats = db.query(
        Quota.section,
        func.count(Quota.id).label("count"),
    ).group_by(Quota.section).order_by(func.count(Quota.id).desc()).all()

    section_breakdown = [
        {"section": row[0] or "(未分类)", "count": row[1]}
        for row in section_stats
    ]

    # ── 4. 材料价格统计 ────────────────────────────────────
    # 按地区统计
    region_stats = db.query(
        MaterialPrice.region,
        func.count(MaterialPrice.id).label("count"),
    ).group_by(MaterialPrice.region).order_by(func.count(MaterialPrice.id).desc()).all()

    region_breakdown = [
        {"region": row[0] or "(未填)", "count": row[1]}
        for row in region_stats
    ]

    # 按月份统计（publication_date 的年月）
    month_stats_raw = db.query(
        func.to_char(MaterialPrice.publication_date, "YYYY-MM").label("month"),
        func.count(MaterialPrice.id).label("count"),
    ).filter(
        MaterialPrice.publication_date != None
    ).group_by(
        func.to_char(MaterialPrice.publication_date, "YYYY-MM")
    ).order_by(
        func.to_char(MaterialPrice.publication_date, "YYYY-MM").desc()
    ).limit(12).all()

    month_breakdown = [
        {"month": row[0] or "(未知)", "count": row[1]}
        for row in month_stats_raw
    ]

    # ── 5. 价格有效期（超过30天标红）─────────────────────────
    # 统计即将过期（30天内）和已过期
    expiring_soon = db.query(func.count(MaterialPrice.id)).filter(
        MaterialPrice.publication_date != None,
        MaterialPrice.is_active == True,
        MaterialPrice.publication_date < thirty_days_ago,
    ).scalar() or 0

    active_prices = db.query(func.count(MaterialPrice.id)).filter(
        MaterialPrice.is_active == True,
    ).scalar() or 0

    # 按价格类型统计
    price_type_stats = db.query(
        MaterialPrice.price_type,
        func.count(MaterialPrice.id).label("count"),
    ).group_by(MaterialPrice.price_type).all()

    price_type_breakdown = [
        {"price_type": row[0] or "(未填)", "count": row[1]}
        for row in price_type_stats
    ]

    return {
        "coverage": {
            "quota_total": quota_total,
            "material_price_total": material_price_total,
        },
        "quota_missing_fields": missing_fields,
        "quota_section_breakdown": section_breakdown,
        "material_region_breakdown": region_breakdown,
        "material_month_breakdown": month_breakdown,
        "material_price_type_breakdown": price_type_breakdown,
        "price_expiry": {
            "active_total": active_prices,
            "expiring_soon": expiring_soon,  # 超过30天未更新
            "threshold_days": 30,
        },
        "generated_at": today.isoformat(),
    }
