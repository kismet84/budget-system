"""
信息价管理路由（US-3：信息价双轨管理）
支持材料价格的手动录入、批量导入和查询
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from database import get_db
from models.price import MaterialPrice
from schemas.price import (
    MaterialPriceCreate,
    MaterialPriceUpdate,
    MaterialPriceResponse,
)

router = APIRouter(prefix="/price", tags=["信息价管理"])


@router.get("/", response_model=List[MaterialPriceResponse])
def list_prices(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=200),
    name: Optional[str] = None,
    price_type: Optional[str] = None,
    region: Optional[str] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
):
    """
    查询材料信息价列表，支持过滤：
    - name: 按材料名称模糊搜索
    - price_type: 信息价 / 企业价
    - region: 地区
    - is_active: 是否有效
    """
    q = db.query(MaterialPrice)

    if name:
        q = q.filter(MaterialPrice.name.ilike(f"%{name}%"))
    if price_type:
        q = q.filter(MaterialPrice.price_type == price_type)
    if region:
        q = q.filter(MaterialPrice.region == region)
    if is_active is not None:
        q = q.filter(MaterialPrice.is_active == is_active)

    return q.order_by(MaterialPrice.publication_date.desc()).offset(skip).limit(limit).all()


@router.get("/{price_id}", response_model=MaterialPriceResponse)
def get_price(price_id: int, db: Session = Depends(get_db)):
    """根据 ID 获取单条信息价"""
    price = db.query(MaterialPrice).filter(MaterialPrice.id == price_id).first()
    if not price:
        raise HTTPException(status_code=404, detail="信息价记录不存在")
    return price


@router.post("/", response_model=MaterialPriceResponse, status_code=201)
def create_price(body: MaterialPriceCreate, db: Session = Depends(get_db)):
    """新增一条材料信息价记录"""
    record = MaterialPrice(**body.model_dump())
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.post("/batch", response_model=List[MaterialPriceResponse], status_code=201)
def create_prices_batch(
    body: List[MaterialPriceCreate],
    db: Session = Depends(get_db),
):
    """批量新增材料信息价记录"""
    records = [MaterialPrice(**item.model_dump()) for item in body]
    db.add_all(records)
    db.commit()
    for r in records:
        db.refresh(r)
    return records


@router.put("/{price_id}", response_model=MaterialPriceResponse)
def update_price(
    price_id: int,
    body: MaterialPriceUpdate,
    db: Session = Depends(get_db),
):
    """更新单条信息价（支持部分更新）"""
    record = db.query(MaterialPrice).filter(MaterialPrice.id == price_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="信息价记录不存在")

    update_data = body.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(record, key, value)

    db.commit()
    db.refresh(record)
    return record


@router.delete("/{price_id}", status_code=204)
def delete_price(price_id: int, db: Session = Depends(get_db)):
    """删除单条信息价（物理删除）"""
    record = db.query(MaterialPrice).filter(MaterialPrice.id == price_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="信息价记录不存在")
    db.delete(record)
    db.commit()
    return None


@router.get("/lookup/{material_name}", response_model=List[MaterialPriceResponse])
def lookup_price(
    material_name: str,
    region: str = Query("武汉市"),
    price_type: str = Query("信息价"),
    db: Session = Depends(get_db),
):
    """
    根据材料名称查询最新信息价（供 price_agg 调用）
    优先返回最新日期的有效记录
    """
    records = (
        db.query(MaterialPrice)
        .filter(
            MaterialPrice.name.ilike(f"%{material_name}%"),
            MaterialPrice.region == region,
            MaterialPrice.price_type == price_type,
            MaterialPrice.is_active == True,
        )
        .order_by(MaterialPrice.publication_date.desc())
        .limit(5)
        .all()
    )
    return records
