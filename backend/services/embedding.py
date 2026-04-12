"""
DeepSeek Embedding 服务
用于将文本转为向量，支持语义搜索
"""
import httpx
from config import settings


async def get_embedding(text: str) -> list[float]:
    """
    调用 DeepSeek API 获取文本 embedding 向量
    模型：deepseek-embed
    """
    if not settings.DEEPSEEK_API_KEY:
        # 占位返回零向量
        return [0.0] * 1024

    url = f"{settings.DEEPSEEK_API_BASE}/embeddings"
    headers = {
        "Authorization": f"Bearer {settings.DEEPSEEK_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "deepseek-embed",
        "input": text,
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(url, json=payload, headers=headers)
        resp.raise_for_status()
        data = resp.json()
        return data["data"][0]["embedding"]


def search_similar(query_vector: list[float], top_k: int = 10):
    """
    在 pgvector 中搜索相似向量
    TODO: 接入 PostgreSQL + pgvector 实现
    """
    # 占位
    return []
