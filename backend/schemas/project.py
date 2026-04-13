from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ProjectBase(BaseModel):
    name: str
    description: Optional[str] = ""
    region: Optional[str] = "武汉市"
    budget_period: Optional[str] = ""
    notes: Optional[str] = ""
    status: Optional[str] = "进行中"


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    region: Optional[str] = None
    budget_period: Optional[str] = None
    notes: Optional[str] = None
    status: Optional[str] = None


class ProjectResponse(ProjectBase):
    id: int
    created_by: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    quota_count: Optional[int] = 0
    total_cost: Optional[float] = 0.0

    class Config:
        from_attributes = True


class ProjectQuotaItem(BaseModel):
    """项目中的单条定额"""
    quota_id: str
    project_name: Optional[str] = None
    section: Optional[str] = None
    unit: Optional[str] = None
    quantity: float
    total_cost: float
    labor_fee: Optional[float] = None
    material_fee: Optional[float] = None
    machinery_fee: Optional[float] = None
    management_fee: Optional[float] = None
    tax: Optional[float] = None


class ProjectDetailResponse(ProjectResponse):
    """项目详情（含定额列表）"""
    items: list[ProjectQuotaItem] = []


class ProjectQuotaAdd(BaseModel):
    """向项目添加定额"""
    quota_id: str
    quantity: float = 1.0
