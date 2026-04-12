#!/usr/bin/env python3
"""
合并定额数据（装饰工程）
将 quota_costs / section_names / project_names / materials / machinery / page_numbers
6个文件按 quota_id 合并为完整记录，写入 imported/ 目录
"""
import json
import os
import re
from pathlib import Path

# ===== 配置 =====
SCRIPT_DIR = Path(__file__).parent.resolve()
DATA_DIR = SCRIPT_DIR.parent.parent / "data" / "定额" / "parsed" / "装饰"
OUTPUT_FILE = SCRIPT_DIR.parent.parent / "data" / "定额" / "imported" / "装饰_合并定额.json"

# ===== 辅助函数（定义在前，避免调用时未定义）=====
# 预加载计量单位（已有独立文件，直接用）
_UNIT_FILE = DATA_DIR / "计量单位.json"
_unit_map: dict = {}
if _UNIT_FILE.exists():
    with open(_UNIT_FILE, "r", encoding="utf-8") as f:
        _unit_map = json.load(f)


def extract_unit(quota_id: str, project_str: str) -> str:
    # 优先使用现成的计量单位.json（直接匹配 quota_id）
    if quota_id in _unit_map:
        return _unit_map[quota_id]
    # fallback：从项目名称正则提取
    """从项目名称字符串末尾提取计量单位"""
    if not project_str:
        return ""
    patterns = [
        r"单位[：:]\s*(\S+)",
        r"(\d+(?:\.\d+)?m³)",
        r"(\d+(?:\.\d+)?m²)",
        r"(\d+(?:\.\d+)?m)(?!\w)",
        r"(\d+(?:\.\d+)?\s*(?:m³|m²|m|t|kg|个|套|樘|项|节|盏|米|平方|立方|延长米))\s*$",
    ]
    for pat in patterns:
        m = re.search(pat, project_str)
        if m:
            return m.group(1).strip()
    return ""

def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, dict):
        return data
    raise ValueError(f"期望 dict，得到 {type(data)}：{path}")

# ===== 加载6个文件 =====
print("📂 加载数据文件...")
quota_costs    = load_json(DATA_DIR / "quota_costs.json")
section_names  = load_json(DATA_DIR / "section_names.json")
project_names  = load_json(DATA_DIR / "project_names.json")
materials      = load_json(DATA_DIR / "materials.json")
machinery      = load_json(DATA_DIR / "machinery.json")
page_numbers   = load_json(DATA_DIR / "page_numbers.json")

# 统一 quota_id 集合
all_ids = set(quota_costs.keys())
print(f"   quota_costs:   {len(quota_costs)} 条")
print(f"   section_names: {len(section_names)} 条")
print(f"   project_names: {len(project_names)} 条")
print(f"   materials:     {len(materials)} 条")
print(f"   machinery:     {len(machinery)} 条")
print(f"   page_numbers:  {len(page_numbers)} 条")
print(f"   合并后应得:   {len(all_ids)} 条")

# ===== 合并 =====
print("\n🔄 开始合并...")
records = []
missing_project = []
missing_section = []

for quota_id in sorted(all_ids):
    costs = quota_costs.get(quota_id, {})
    section = section_names.get(quota_id, {})
    project = project_names.get(quota_id, "")
    mats = materials.get(quota_id, [])
    mags = machinery.get(quota_id, [])
    page = page_numbers.get(quota_id, None)

    if not project:
        missing_project.append(quota_id)
    if not section:
        missing_section.append(quota_id)

    # 构造完整记录（字段名与 import_quota_db.py 的 SQL 对应）
    record = {
        "定额编号": quota_id,
        "category": section.get("一级", ""),        # 专业类别（一级分部）
        "section": " / ".join(filter(None, [        # 完整三级路径
            section.get("一级", ""),
            section.get("二级", ""),
            section.get("三级", ""),
        ])),
        "项目名称": project,
        "计量单位": extract_unit(quota_id, project),
        "工作内容": "",
        "全费用":     costs.get("全费用"),
        "其中人工费": costs.get("人工费"),
        "材料费":     costs.get("材料费"),
        "机械费":     costs.get("机械费"),
        "费用":       costs.get("费用"),       # 管理费（含利润、规费）
        "增值税":     costs.get("增值税"),
        "材料明细": mats,
        "机械明细": mags,
        "source_file": f"湖北定额2024-装饰/{quota_id}",
        "page_number": page,
    }
    records.append(record)

# ===== 写入 =====
OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(records, f, ensure_ascii=False, indent=2)

print(f"\n✅ 合并完成！共 {len(records)} 条记录")
print(f"   输出文件: {OUTPUT_FILE}")

if missing_project:
    print(f"\n⚠️  project_names 缺失: {len(missing_project)} 条（显示前5条）: {missing_project[:5]}")
if missing_section:
    print(f"\n⚠️  section_names 缺失: {len(missing_section)} 条（显示前5条）: {missing_section[:5]}")
if not missing_project and not missing_section:
    print("   无缺失警告 ✓")

# ===== 摘要统计 =====
sections = {}
for r in records:
    cat = r["category"] or "未知"
    sections[cat] = sections.get(cat, 0) + 1

print("\n📊 分部统计：")
for sec, cnt in sorted(sections.items(), key=lambda x: -x[1]):
    print(f"   {sec}: {cnt}条")
