"""
AI 语义搜索路由
完整链路：LLM解析 → 向量检索 → 价格聚合 → 返回结果

AI 提供商（统一）：
  · LLM 语义解析：DeepSeek（services/llm_parse.py）
  · 向量嵌入：SiliconFlow BAAI/bge-large-zh-v1.5（services/vector_search.py）
  · Embedding（备选）：DeepSeek deepseek-embed（services/embedding.py）
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import asyncio
import re

from database import get_db
from config import settings
from core.security import get_current_user
from services.llm_parse import parse_construction_text
from services.vector_search import hybrid_search, text_to_vector, search_by_keyword, tokenize_chinese
from services.price_agg import aggregate_top_quotas, format_quota_response, get_connection
from services.rerank import rerank

router = APIRouter(prefix="/ai", tags=["AI 语义搜索"])


class AISearchRequest(BaseModel):
    """AI 语义搜索请求"""
    query: str                        # 用户输入，如"浇筑C30混凝土矩形柱"
    top_k: int = 3                   # 返回数量
    category: Optional[str] = None     # 可选，专业分类过滤
    min_similarity: float = 0.0      # 相似度阈值过滤
    section_prefix: Optional[str] = None  # 可选，分部路径前缀过滤


class ParsedParams(BaseModel):
    """LLM 解析后的结构化参数"""
    action: str
    material: str
    specification: str
    shape: str
    unit: str
    search_keyword: str
    fallback: bool = False


class QuotaResult(BaseModel):
    """单条定额结果"""
    quota_id: str
    category: str
    work_content: str
    section: str
    unit: str
    quantity: Optional[str] = None
    total_cost: float
    labor_fee: Optional[float]
    material_fee: Optional[float]
    machinery_fee: Optional[float]
    management_fee: Optional[float]
    tax: Optional[float]
    project_name: Optional[str]
    similarity: Optional[float]
    rerank_score: Optional[float] = None
    materials_count: int
    total_material_cost: Optional[float]
    reference_price: Optional[float]


class AISearchResponse(BaseModel):
    """AI 搜索响应"""
    query: str                    # 原始输入
    parsed: ParsedParams          # LLM 解析结果
    results: List[QuotaResult]     # Top-K 定额结果
    total: int                    # 结果数量
    filtered_count: int = 0       # 因相似度阈值被过滤的数量
    warning: Optional[str] = None  # 警告信息
    info_price_missing: bool = False  # 信息价是否缺失


@router.post("/search", response_model=AISearchResponse)
async def ai_semantic_search(
    body: AISearchRequest,
    db=Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    AI 语义搜索主入口

    完整链路：
    1. LLM 解析用户输入 → 结构化参数
    2. 生成查询向量（SiliconFlow BAAI/bge-large-zh-v1.5）
    3. 向量检索（pgvector，余弦相似度 Top-K）
    4. 价格聚合（材料单价汇总）
    5. 返回格式化结果
    """
    warnings = []

    # ========== Step 1: LLM 语义解析 ==========
    parsed = await parse_construction_text(body.query)

    if parsed.get("fallback"):
        warnings.append(
            f"LLM 解析降级（API Key 未配置或调用失败），"
            f"使用原始文本搜索: {body.query}"
        )

    # ========== Step 2: 生成查询向量 ==========
    search_keyword = parsed.get("search_keyword") or body.query
    raw_query = body.query.strip()

    # 检测是否为精确 quota_id 查询（直接用 quota_id 搜索）
    # 此时直接走 DB 精确查询，不走向量搜索，避免向量距离过大导致排序错误
    exact_quota_id = None
    if re.match(r'^[A-Z]\d+-\d+$', raw_query, re.IGNORECASE):
        # 精确匹配 quota_id，跳过向量搜索
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            "SELECT id, quota_id, category, unit, quantity, work_content, section, "
            "total_cost, labor_fee, material_fee, machinery_fee, management_fee, tax, "
            "project_name, source_file FROM quotas WHERE UPPER(quota_id) = UPPER(%s) LIMIT 1",
            (raw_query,)
        )
        row = cur.fetchone()
        cur.close()
        conn.close()
        if row:
            exact_quota_id = row[1]
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM materials WHERE quota_id = %s", (row[1],))
            mats_count = cur.fetchone()[0]
            cur.close()
            conn.close()
            exact_result = {
                "id": row[0], "quota_id": row[1], "category": row[2], "unit": row[3],
                "quantity": row[4], "work_content": row[5], "section": row[6],
                "total_cost": row[7], "labor_fee": row[8], "material_fee": row[9],
                "machinery_fee": row[10], "management_fee": row[11], "tax": row[12],
                "project_name": row[13], "source_file": row[14],
                "raw_similarity": 1.0, "similarity": 1.0, "rerank_score": None,
                "materials_count": mats_count,
            }
            try:
                enriched = aggregate_top_quotas([exact_result])
                exact_result_fmt = format_quota_response(enriched[0])
            except Exception:
                exact_result_fmt = format_quota_response(exact_result)
            return AISearchResponse(
                query=body.query, parsed=ParsedParams(**parsed),
                results=[exact_result_fmt], total=1,
                warning="精确 quota_id 查询（直接匹配）"
            )
        # 没查到也继续向量搜索

    try:
        query_vector = await asyncio.to_thread(text_to_vector, search_keyword, settings.SILICONFLOW_API_KEY)
    except Exception as e:
        # 向量生成失败，降级为纯关键词搜索
        warnings.append(f"向量生成失败，降级为关键词搜索: {e}")
        keyword_results = search_by_keyword(search_keyword, body.top_k)
        enriched = aggregate_top_quotas(keyword_results)
        results = [format_quota_response(q) for q in enriched]
        info_price_missing = any(r.get('material_price_missing', False) for r in results)
        if info_price_missing:
            warnings.append("⚠️ 信息价缺失，定额价格基于定额综合单价，非市场价")
        return AISearchResponse(
            query=body.query,
            parsed=ParsedParams(**parsed),
            results=results,
            total=len(results),
            warning=" | ".join(warnings) if warnings else None,
            info_price_missing=info_price_missing
        )

    # ========== Step 3: 向量 + 混合检索 ==========
    try:
        vector_results = hybrid_search(
            query_vector=query_vector,
            keyword=search_keyword,
            top_k=body.top_k * 2,  # 多取一些，后面筛选
            vector_weight=0.7,
            section_prefix=body.section_prefix
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"向量检索失败: {e}")

    # ========== Step 4: 关键词精确匹配 Boost ==========
    # Boost 规则（按优先级）：
    # 1. Exact quota_id match → +0.5 (highest priority)
    # 2. Project name match (exact word in project_name field) → +0.25
    # 3. Section leaf match (query word matches LAST segment of section path) → +0.2
    # 4. Exact phrase in section → +0.15
    # 5. Category match (query word in category) → +0.1
    # 6. Synonym match (expanded synonym list) → +0.1
    # 7. Character overlap ≥80% → +0.05
    # Maximum total boost: +0.5 (cap at 0.5)
    raw_query = body.query.strip()
    query_words = tokenize_chinese(raw_query)

    # 建筑专业同义词表（expanded）
    CONSTRUCTION_SYNONYMS = {
        "墙体": ["墙面", "墙体", "墙身"],
        "柱体": ["柱面", "柱", "柱身"],
        "梁体": ["梁面", "梁", "梁侧"],
        "楼地面": ["楼地面", "地面", "地板"],
        "天棚": ["天棚", "顶棚", "吊顶", "棚面"],
        "抹灰": ["抹灰", "粉刷", "饰面"],
        "防水": ["防水", "防潮", "防腐"],
        "门窗": ["门窗", "门", "窗", "门扇", "窗扇"],
        "涂料": ["涂料", "油漆", "面漆", "饰料"],
        "保温": ["保温", "隔热"],
        "砌筑": ["砌筑", "砌体", "砖墙"],
        "混凝土": ["混凝土", "砼", "钢筋混凝土"],
        "模板": ["模板", "模型板", "支模"],
        "脚手架": ["脚手架", "架子", "外脚手"],
        "拆除": ["拆除", "拆除工程", "破坏"],
    }
    # 同义词反向索引：section 中的词 → 查询词
    SYNONYM_REVERSE = {}
    for kw, syns in CONSTRUCTION_SYNONYMS.items():
        for s in syns:
            SYNONYM_REVERSE.setdefault(s, []).append(kw)

    def get_section_leaf(section: str) -> str:
        """获取 section 路径的最后一段（叶节点）"""
        parts = re.split(r'[/／、]', section)
        return parts[-1] if parts else ""

    def exact_word_in_field(word: str, field_value: str) -> bool:
        """检查词是否作为完整词出现在字段中（支持中英文分词）"""
        if not field_value:
            return False
        # 用空格和标点分词后检查是否完全匹配
        field_words = re.split(r'[,，、\s　]+', field_value)
        return word in field_words

    for r in vector_results:
        sec = r.get("section", "") or ""
        cat = r.get("category", "") or ""
        proj = r.get("project_name", "") or ""
        qid = r.get("quota_id", "") or ""
        boost_amt = 0.0

        sec_leaf = get_section_leaf(sec)

        # 1. Exact quota_id match → +0.5 (highest priority)
        if qid and (qid == raw_query or raw_query == qid):
            boost_amt = 0.5
        else:
            # 2. Project name match (exact word in project_name field) → +0.25
            for word in query_words:
                if exact_word_in_field(word, proj):
                    boost_amt = max(boost_amt, 0.25)
                    break

            # 3. Section leaf match (query word matches LAST segment of section path) → +0.2
            for word in query_words:
                if exact_word_in_field(word, sec_leaf):
                    boost_amt = max(boost_amt, 0.2)
                    break

            # 4. Exact phrase in section → +0.15
            if boost_amt < 0.15 and raw_query in sec:
                boost_amt = max(boost_amt, 0.15)

            # 5. Category match (query word in category) → +0.1
            for word in query_words:
                if exact_word_in_field(word, cat):
                    boost_amt = max(boost_amt, 0.1)
                    break

            # 6. Synonym match → +0.1
            for word in query_words:
                if word in CONSTRUCTION_SYNONYMS:
                    for syn in CONSTRUCTION_SYNONYMS[word]:
                        if syn in sec or syn in cat:
                            boost_amt = max(boost_amt, 0.1)
                            break
                    if boost_amt >= 0.1:
                        break

            # 7. Character overlap ≥80% → +0.05
            if boost_amt < 0.05:
                for word in query_words:
                    overlap_sec = sum(1 for c in word if c in sec) / len(word) if word else 0
                    overlap_cat = sum(1 for c in word if c in cat) / len(word) if word else 0
                    if max(overlap_sec, overlap_cat) >= 0.8:
                        boost_amt = max(boost_amt, 0.05)
                        break

        # Cap total boost at 0.5
        boost_amt = min(boost_amt, 0.5)
        raw_sim = r.get("similarity") or 0
        r["raw_similarity"] = raw_sim
        # 避免负相似度导致排序错误
        r["similarity"] = min(raw_sim + boost_amt, 1.0) if raw_sim >= 0 else boost_amt

    # 重新排序
    vector_results.sort(key=lambda x: x.get("similarity") or 0, reverse=True)

    # ========== Step 5: 价格聚合 ==========
    try:
        enriched = aggregate_top_quotas(vector_results)
        results = [format_quota_response(q) for q in enriched]
    except Exception as e:
        warnings.append(f"价格聚合失败，仅返回检索结果: {e}")
        results = [format_quota_response(q) for q in vector_results]

    # ========== Step 5.5: 二阶段检索（Rerank）==========
    # 精确 quota_id 匹配的结果不受 Rerank 干扰，直接排在最前
    exact_quota_ids = set()
    for r in results:
        qid = (r.get("quota_id") or "").strip()
        if qid and qid == raw_query:
            exact_quota_ids.add(qid)

    if results and not exact_quota_ids:
        # 无精确匹配时正常 Rerank
        oversample = body.top_k * 4
        candidates = results[:oversample]
        doc_texts = [
            " | ".join(filter(None, [
                str(r.get("project_name", "") or "")[:200],
                str(r.get("work_content", "") or "")[:200],
                str(r.get("unit", "") or "")[:200],
                str(r.get("section", "") or "")[:200],
                str(r.get("category", "") or "")[:200],
            ]))
            for r in candidates
        ]
        try:
            reranked = await asyncio.to_thread(rerank, body.query, doc_texts, top_n=body.top_k)
            rerank_map = {rr["index"]: rr["relevance_score"] for rr in reranked}
            for i, r in enumerate(candidates):
                r["rerank_score"] = rerank_map.get(i, 0.0)
            reranked_ids = [rr["index"] for rr in reranked]
            results = [candidates[i] for i in reranked_ids if i < len(candidates)]
        except Exception as ex:
            warnings.append(f"Rerank 失败: {ex}")

    # 有精确匹配时，将精确命中的结果按 Boost 后的位置排在最前
    if exact_quota_ids:
        exact_results = [r for r in results if (r.get("quota_id") or "").strip() in exact_quota_ids]
        other_results = [r for r in results if (r.get("quota_id") or "").strip() not in exact_quota_ids]
        results = exact_results + other_results

    # 判断是否有信息价缺失
    info_price_missing = any(r.get('material_price_missing', False) for r in results)
    if info_price_missing:
        warnings.append("⚠️ 信息价缺失，定额价格基于定额综合单价，非市场价")

    # 截断到指定数量
    results = results[:body.top_k]

    # ========== Step 6: 相似度阈值过滤（使用原始相似度，不受 Boost 影响）==========
    if body.min_similarity > 0:
        before_filter = len(results)
        results = [r for r in results if (r.get("raw_similarity") or 0) >= body.min_similarity]
        filtered_count = before_filter - len(results)
    else:
        filtered_count = 0

    # ========== Step 7: 返回结果 ==========
    return AISearchResponse(
        query=body.query,
        parsed=ParsedParams(**parsed),
        results=results,
        total=len(results),
        filtered_count=filtered_count,
        warning=" | ".join(warnings) if warnings else None,
        info_price_missing=info_price_missing
    )
