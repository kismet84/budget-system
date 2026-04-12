"""
SiliconFlow Rerank API 封装
"""
import requests
from config import settings

RERANK_URL = "https://api.siliconflow.cn/v1/rerank"


def rerank(query: str, documents: list[str], model: str = "BAAI/bge-reranker-v2-m3", top_n: int = None) -> list[dict]:
    """
    调用 SiliconFlow Rerank API 对文档进行相关性重排序

    Args:
        query: 查询文本
        documents: 候选文档列表
        model: Rerank 模型名
        top_n: 返回前 N 条，不传则返回全部

    Returns:
        [{index, document, relevance_score}, ...] 按相关性降序
    """
    payload = {
        "model": model,
        "query": query,
        "documents": documents,
        "top_n": top_n or len(documents),
        "return_documents": False,
    }
    headers = {
        "Authorization": f"Bearer {settings.SILICONFLOW_API_KEY}",
        "Content-Type": "application/json",
    }

    resp = requests.post(RERANK_URL, json=payload, headers=headers, timeout=30)
    if resp.status_code != 200:
        raise RuntimeError(f"Rerank API error {resp.status_code}: {resp.text}")

    data = resp.json()
    return data.get("results", [])
