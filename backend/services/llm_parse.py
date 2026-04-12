"""
LLM 语义解析服务
使用 DeepSeek API 将用户输入的施工描述解析为结构化参数
"""
import httpx
import json
import re
from typing import Optional
from config import settings


async def parse_construction_text(user_input: str) -> dict:
    """
    将用户的施工描述文本解析为结构化参数。

    例如：
    输入："浇筑C30混凝土矩形柱，截面400x400"
    输出：{
        "action": "浇筑",
        "material": "C30混凝土",
        "shape": "矩形柱",
        "section": "400x400",
        "unit": "m³",
        "raw": "浇筑C30混凝土矩形柱，截面400x400"
    }

    Returns:
        dict: 解析结果（含原始输入）
    """
    system_prompt = """你是一个建筑工程定额语义解析助手。
用户会输入一段施工描述，你需要提取以下结构化信息：

- action: 施工作业动作（如：浇筑、挖掘、铺设、拆除、绑扎等）
- material: 主要材料（如：C30混凝土、钢筋、防水卷材、砌块等）
- specification: 材料规格或施工规格（如：400x400、3mm厚、C25等）
- shape: 构件形状（如：矩形柱、圆形基础、带肋板等）
- unit: 计量单位（根据常识推断，如：m³、m²、m、kg等）
- auxiliary_materials: 辅助材料列表（如有，逗号分隔）
- notes: 其他备注（如有）

请直接输出 JSON，不要有多余文字。字段可以留空字符串。
"""

    user_prompt = f"施工描述：{user_input}"

    if not settings.DEEPSEEK_API_KEY:
        # 降级：返回原始输入作为搜索关键词
        return {
            "action": "",
            "material": "",
            "specification": "",
            "shape": "",
            "unit": "",
            "auxiliary_materials": [],
            "notes": "",
            "search_keyword": user_input,
            "raw": user_input,
            "fallback": True
        }

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                f"{settings.DEEPSEEK_API_BASE}/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.DEEPSEEK_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": settings.DEEPSEEK_MODEL,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    "temperature": 0.1,
                }
            )
            resp.raise_for_status()
            data = resp.json()

            # 提取响应内容
            content = data["choices"][0]["message"]["content"]

            # 尝试解析 JSON
            # 去掉可能的 markdown 代码块
            content = re.sub(r"^```json\s*", "", content.strip())
            content = re.sub(r"\s*```$", "", content.strip())

            parsed = json.loads(content)

            # 生成搜索关键词
            search_parts = [
                parsed.get("action", ""),
                parsed.get("material", ""),
                parsed.get("specification", ""),
                parsed.get("shape", ""),
            ]
            search_keyword = " ".join(p for p in search_parts if p)
            if not search_keyword:
                search_keyword = user_input

            parsed["search_keyword"] = search_keyword
            parsed["raw"] = user_input
            parsed["fallback"] = False
            return parsed

    except Exception as e:
        # 降级：使用原始输入作为搜索关键词
        return {
            "action": "",
            "material": "",
            "specification": "",
            "shape": "",
            "unit": "",
            "auxiliary_materials": [],
            "notes": "",
            "search_keyword": user_input,
            "raw": user_input,
            "fallback": True,
            "error": str(e)
        }
