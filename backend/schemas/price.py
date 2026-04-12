"""
Pydantic schemas for material price management
"""
from datetime import date
from typing import Optional
from pydantic import BaseModel


class MaterialPriceBase(BaseModel):
    name: str
    specification: Optional[str] = ""
    unit: str
    unit_price: float
    price_type: str = "信息价"   # 信息价 / 企业价
    region: str = "武汉市"
    publication_date: Optional[date] = None
    source: str = ""
    is_active: bool = True
    remarks: str = ""


class MaterialPriceCreate(MaterialPriceBase):
    pass


class MaterialPriceUpdate(BaseModel):
    name: Optional[str] = None
    specification: Optional[str] = None
    unit: Optional[str] = None
    unit_price: Optional[float] = None
    price_type: Optional[str] = None
    region: Optional[str] = None
    publication_date: Optional[date] = None
    source: Optional[str] = None
    is_active: Optional[bool] = None
    remarks: Optional[str] = None


class MaterialPriceResponse(MaterialPriceBase):
    id: int

    class Config:
        from_attributes = True
