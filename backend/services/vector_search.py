"""
向量检索服务
使用 pgvector 进行语义相似度搜索
"""
import psycopg2
from typing import List, Tuple
from config import settings

# 中文分词
import jieba
import re

STOP_WORDS = {"的", "了", "和", "与", "或", "及", "在", "于", "为", "以", "等", " ", "　", "，", "、", "（", "）", "(", ")"}


def tokenize_chinese(text: str) -> List[str]:
    """
    中文分词 + 过滤停用词 + 过滤单字符
    返回有意义的词列表
    """
    if not text:
        return []
    words = jieba.cut(text)
    return [w for w in words if len(w) >= 2 and w not in STOP_WORDS]


def get_connection():
    """获取数据库连接"""
    return psycopg2.connect(settings.DATABASE_URL)


def text_to_vector(text: str, api_key: str) -> List[float]:
    """
    使用 SiliconFlow API 将文本转为向量（BAAI/bge-large-zh-v1.5）
    与 gen_vector_fast.py 使用相同模型，保持一致
    """
    import urllib.request
    import json

    payload = {
        "model": "BAAI/bge-large-zh-v1.5",
        "input": text[:1000]  # 截断
    }

    req = urllib.request.Request(
        "https://api.siliconflow.cn/v1/embeddings",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        },
        method="POST"
    )

    with urllib.request.urlopen(req, timeout=60) as r:
        result = json.loads(r.read())
        return result["data"][0]["embedding"]


def search_by_vector(
    query_vector: List[float],
    top_k: int = 10,
    category_filter: str = None
) -> List[dict]:
    """
    在 pgvector 中搜索与 query_vector 最相似的定额

    Args:
        query_vector: 查询向量（1024维）
        top_k: 返回数量
        category_filter: 可选，专业分类过滤

    Returns:
        List[dict]: Top-K 定额列表（含相似度分数）
    """
    conn = get_connection()
    cur = conn.cursor()

    # SQL：使用余弦相似度 (cosine distance)
    sql = """
        SELECT
            id, quota_id, category, unit, work_content, section,
            total_cost, labor_fee, material_fee, machinery_fee, management_fee, tax,
            project_name, source_file,
            1 - (embedding <=> %s::vector) AS similarity
        FROM quotas
        WHERE embedding IS NOT NULL
    """
    params = [query_vector]

    if category_filter:
        sql += " AND category = %s"
        params.append(category_filter)

    sql += " ORDER BY embedding <=> %s::vector LIMIT %s"
    params.extend([query_vector, top_k])

    cur.execute(sql, params)
    rows = cur.fetchall()

    results = []
    for row in rows:
        results.append({
            "id": row[0],
            "quota_id": row[1],
            "category": row[2],
            "unit": row[3],
            "work_content": row[4],
            "section": row[5],
            "total_cost": row[6],
            "labor_fee": row[7],
            "material_fee": row[8],
            "machinery_fee": row[9],
            "management_fee": row[10],
            "tax": row[11],
            "project_name": row[12],
            "source_file": row[13],
            "similarity": round(row[14], 4)
        })

    cur.close()
    conn.close()
    return results


def search_by_keyword(
    keyword: str,
    top_k: int = 20
) -> List[dict]:
    """
    关键词全文搜索（作为向量搜索的补充）

    Args:
        keyword: 搜索关键词
        top_k: 返回数量

    Returns:
        List[dict]: 匹配的定额列表
    """
    conn = get_connection()
    cur = conn.cursor()

    # Try exact quota_id match first (avoids substring false positives like "A10-51" matching "A15-51")
    exact_sql = """
        SELECT
            id, quota_id, category, unit, work_content, section,
            total_cost, labor_fee, material_fee, machinery_fee, management_fee, tax,
            project_name, source_file
        FROM quotas
        WHERE embedding IS NOT NULL AND quota_id = %s
    """
    cur.execute(exact_sql, (keyword.strip(),))
    exact_row = cur.fetchone()
    if exact_row:
        cur.close()
        conn.close()
        return [{
            "id": exact_row[0],
            "quota_id": exact_row[1],
            "category": exact_row[2],
            "unit": exact_row[3],
            "work_content": exact_row[4],
            "section": exact_row[5],
            "total_cost": exact_row[6],
            "labor_fee": exact_row[7],
            "material_fee": exact_row[8],
            "machinery_fee": exact_row[9],
            "management_fee": exact_row[10],
            "tax": exact_row[11],
            "project_name": exact_row[12],
            "source_file": exact_row[13],
            "similarity": None
        }]

    # Fall back to substring/ILIKE search
    cur.execute(
        """
        SELECT
            id, quota_id, category, unit, work_content, section,
            total_cost, labor_fee, material_fee, machinery_fee, management_fee, tax,
            project_name, source_file
        FROM quotas
        WHERE
            work_content ILIKE %s
            OR section ILIKE %s
            OR quota_id ILIKE %s
        LIMIT %s
        """,
        (f"%{keyword}%", f"%{keyword}%", f"%{keyword}%", top_k)
    )
    rows = cur.fetchall()

    results = []
    for row in rows:
        results.append({
            "id": row[0],
            "quota_id": row[1],
            "category": row[2],
            "unit": row[3],
            "work_content": row[4],
            "section": row[5],
            "total_cost": row[6],
            "labor_fee": row[7],
            "material_fee": row[8],
            "machinery_fee": row[9],
            "management_fee": row[10],
            "tax": row[11],
            "project_name": row[12],
            "source_file": row[13],
            "similarity": None
        })

    cur.close()
    conn.close()
    return results


def hybrid_search(
    query_vector: List[float],
    keyword: str,
    top_k: int = 10,
    vector_weight: float = 0.7
) -> List[dict]:
    """
    混合搜索：向量相似度（vector_weight）+ 关键词匹配（1 - vector_weight）

    真实加权融合：
    1. 并行执行向量搜索和关键词搜索
    2. 各自归一化分数到 [0, 1]
    3. 加权求和: score = vector_weight * norm_vector_sim + (1-vector_weight) * norm_keyword_sim
    4. 按融合分数排序、去重
    """
    keyword_weight = 1.0 - vector_weight

    # ========== 第一步：并行向量搜索 + 关键词搜索 ==========
    vector_results = search_by_vector(query_vector, top_k * 3)
    keyword_results = search_by_keyword(keyword, top_k * 3)

    # 构建结果字典（按 id 去重）
    all_results: dict[int, dict] = {}
    for r in vector_results:
        all_results[r["id"]] = {**r, "_vec_sim": r.get("similarity") or 0.0}
    for r in keyword_results:
        if r["id"] in all_results:
            all_results[r["id"]]["_kw_sim"] = 1.0  # 命中关键词，赋最高原始分
        else:
            all_results[r["id"]] = {**r, "_vec_sim": 0.0, "_kw_sim": 1.0}

    # ========== 第二步：归一化 + 加权融合 ==========
    vec_sims = [r["_vec_sim"] for r in all_results.values() if r["_vec_sim"] > 0]
    max_vec = max(vec_sims) if vec_sims else 1.0
    min_vec = min(vec_sims) if vec_sims else 0.0
    vec_range = max_vec - min_vec if max_vec != min_vec else 1.0

    for r in all_results.values():
        # 向量相似度归一化（Min-Max）
        norm_vec = (r.get("_vec_sim", 0.0) - min_vec) / vec_range if vec_range > 0 else 0.0
        # 关键词命中归一化：有 _kw_sim 字段 = 1.0，否则 0
        norm_kw = r.get("_kw_sim", 0.0)
        # 加权融合
        r["similarity"] = round(vector_weight * norm_vec + keyword_weight * norm_kw, 4)
        # 清理临时字段（pop with default，避免重复删除 KeyError）
        r.pop("_vec_sim", None)
        r.pop("_kw_sim", None)

    # ========== 第三步：按融合分数排序 ==========
    sorted_results = sorted(all_results.values(), key=lambda x: x["similarity"], reverse=True)

    # ========== 第四步：精确 quota_id 匹配优先（不破坏排序逻辑）==========
    keyword_upper = keyword.strip().upper()
    exact_idx = None
    for i, r in enumerate(sorted_results):
        if r.get("quota_id", "").upper() == keyword_upper:
            exact_idx = i
            break
    if exact_idx is not None and exact_idx != 0:
        exact_item = sorted_results.pop(exact_idx)
        sorted_results.insert(0, exact_item)
        # 重新赋最高融合分
        top_score = sorted_results[0]["similarity"] if sorted_results else 1.0
        sorted_results[0]["similarity"] = min(top_score + 0.01, 1.0)

    return sorted_results[:top_k]
