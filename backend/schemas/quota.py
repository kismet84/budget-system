from pydantic import BaseModel
from typing import Optional


class QuotaBase(BaseModel):
    """定额基础 schema"""
    quota_id: str
    category: Optional[str] = None
    unit: Optional[str] = None
    quantity: Optional[str] = None
    work_content: Optional[str] = None
    section: Optional[str] = None
    project_name: Optional[str] = None
    total_cost: Optional[float] = None
    labor_fee: Optional[float] = None
    material_fee: Optional[float] = None
    machinery_fee: Optional[float] = None
    management_fee: Optional[float] = None
    tax: Optional[float] = None
    source_file: Optional[str] = None


class QuotaCreate(QuotaBase):
    """创建定额"""
    pass


class QuotaResponse(QuotaBase):
    """定额响应"""
    id: int

    class Config:
        from_attributes = True


class QuotaSearchRequest(BaseModel):
    """定额搜索请求"""
    keyword: str
    limit: int = 20


class AISearchRequest(BaseModel):
    """AI 语义搜索请求"""
    query: str
    top_k: int = 10
