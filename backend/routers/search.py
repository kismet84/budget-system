from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from database import get_db
from models.quota import Quota
from schemas.quota import AISearchRequest, QuotaResponse
from services.embedding import get_embedding, search_similar

router = APIRouter(prefix="/search", tags=["AI 搜索"])


@router.post("/semantic", response_model=List[QuotaResponse])
def semantic_search(body: AISearchRequest, db: Session = Depends(get_db)):
    """AI 语义搜索（占位，由 /ai/search 提供完整实现）"""
    # 当前由 ai_search.py 的 /ai/search 提供完整链路，此路由预留扩展用
    return []
