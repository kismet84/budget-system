from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_, text, func
from typing import List

from database import get_db
from models.quota import Quota
from models.price import MaterialPrice
from schemas.quota import QuotaResponse, QuotaSearchRequest

router = APIRouter(prefix="/quota", tags=["定额管理"])


@router.get("/", response_model=List[QuotaResponse])
async def list_quotas(skip: int = 0, limit: int = 20, db: Session = Depends(get_db)):
    """获取定额列表"""
    quotas = db.query(Quota).offset(skip).limit(limit).all()
    return quotas


@router.get("/sections")
def get_sections(db: Session = Depends(get_db)):
    """获取所有分部（第一级分类路径）"""
    all_sections = db.query(Quota.section).distinct().all()
    prefixes = sorted(set(
        s[0].split(' / ')[0] for s in all_sections if s[0]
    ))
    return [{"value": p, "label": p} for p in prefixes]


@router.get("/{quota_id}/materials")
def get_quota_materials(quota_id: str, db: Session = Depends(get_db)):
    """获取指定定额的材料清单"""
    result = db.execute(
        text("SELECT name, mat_type, unit, unit_price, consumption FROM materials WHERE quota_id = :quota_id"),
        {"quota_id": quota_id}
    ).fetchall()
    return [
        {
            "name": row.name,
            "mat_type": row.mat_type,
            "unit": row.unit,
            "unit_price": row.unit_price,
            "consumption": row.consumption,
        }
        for row in result
    ]


@router.get("/{quota_id}", response_model=QuotaResponse)
def get_quota(quota_id: str, db: Session = Depends(get_db)):
    """根据定额编号获取定额详情"""
    quota = db.query(Quota).filter(Quota.quota_id == quota_id).first()
    if not quota:
        raise HTTPException(status_code=404, detail="定额不存在")
    return quota


@router.post("/search", response_model=List[QuotaResponse])
def search_quotas(body: QuotaSearchRequest, db: Session = Depends(get_db)):
    """关键词搜索定额"""
    quotas = (
        db.query(Quota)
        .filter(
            or_(
                Quota.quota_id.contains(body.keyword),
                Quota.work_content.contains(body.keyword),
                Quota.category.contains(body.keyword),
                Quota.section.contains(body.keyword),
            )
        )
        .limit(body.limit)
        .all()
    )
    return quotas


@router.get("/stats")
def get_stats(db: Session = Depends(get_db)):
    """获取系统统计信息"""
    quota_count = db.query(func.count(Quota.id)).scalar() or 0
    price_count = db.query(func.count(MaterialPrice.id)).scalar() or 0
    
    return {
        "quota_count": quota_count,
        "price_count": price_count,
        "vector_index_status": "已构建" if quota_count > 0 else "未构建",
    }

