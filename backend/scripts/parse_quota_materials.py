#!/usr/bin/env python3
"""
提取定额材料明细和机械明细
输出:
  data/定额/materials.json   - 材料消耗明细
  data/定额/machinery.json   - 机械台班明细
"""

import json, re, os, sys
from pathlib import Path

PDF_PATH = Path(__file__).parent.parent.parent / "data/定额/raw/装饰/《湖北省房屋建筑与装饰工程消耗量定额及全费用基价表》（装饰·措施）（2024）.pdf"
MAT_OUTPUT = Path(__file__).parent.parent.parent / "data/定额/materials.json"
MECH_OUTPUT = Path(__file__).parent.parent.parent / "data/定额/machinery.json"

try:
    import fitz
except ImportError:
    print("请先安装 PyMuPDF: pip install pymupdf")
    sys.exit(1)


def clean(v):
    if v is None:
        return ""
    v = str(v)
    for sep in ["⁃", "‐", "‑", "–", "—", "『", "－"]:
        v = v.replace(sep, "-")
    fw_map = {}
    for i in range(0xFF01, 0xFF5F + 1):
        fw_map[i] = chr(i - 0xFEE0)
    fw_map[0x3000] = " "
    fw_map[0xFF08] = "("
    fw_map[0xFF09] = ")"
    v = v.translate(fw_map)
    return re.sub(r"[\s\u3000\n]+", "", v).strip()


def clean_quota_code(v):
    if v is None:
        return None
    for dash in ["⁃", "‑", "–", "—", "―", "‐", "－"]:
        v = str(v).replace(dash, "-")
    m = re.match(r"^([A-Z]\d+)-(\d+)$", clean(v))
    if m:
        return f"{m.group(1)}-{m.group(2)}"
    return None


def to_float(val_str):
    """将全角数字/符号转为浮点数，空值或'-'返回None"""
    if not val_str or val_str.strip() in ["-", "—", "－", ""]:
        return None
    val = val_str.translate(
        {i: chr(i - 0xFEE0) for i in range(0xFF00, 0xFF5F + 1)}
    )
    val = val.replace(",", "").replace("，", "").replace("．", ".")
    try:
        return float(re.sub(r"[^\d.\-]", "", val))
    except ValueError:
        return None


def find_header_row(data, sorted_cols):
    """查找"名称/单位/单价/消耗量"表头所在行索引"""
    for ri in range(4, min(20, len(data))):
        if ri >= len(data):
            continue
        row = data[ri]
        # 检查是否所有 quota 列的 ci=3 位置都是"消耗量"
        if sorted_cols and sorted_cols[0] < len(row):
            cell3 = clean(row[sorted_cols[0]])
            if cell3 == "消耗量":
                return ri
        # 也检查 ci=0 是否有"名称"
        if sorted_cols and sorted_cols[0] < len(row):
            cell0 = clean(row[0])
            if cell0 == "名称":
                return ri
    return None


def main():
    print("=" * 60)
    print("定额材料明细 & 机械台班提取")
    print("=" * 60)

    doc = fitz.open(PDF_PATH)
    print(f"PDF 总页数: {len(doc)}")

    materials_results = {}  # quota_code -> [material_items]
    machinery_results = {}  # quota_code -> [mech_items]

    for fitz_idx in range(len(doc)):
        page = doc[fitz_idx]
        tabs = page.find_tables()
        if not tabs.tables:
            continue
        data = tabs.tables[0].extract()
        if not data or len(data) < 12:
            continue

        # 提取 quota 列
        quota_cols = {}
        for ci, cell in enumerate(data[0]):
            code = clean_quota_code(cell)
            if code:
                quota_cols[ci] = code
        if not quota_cols:
            continue

        sorted_cols = sorted(quota_cols.keys())
        quota_start = sorted_cols[0]  # 第一个 quota 列的索引

        # 查找表头行（名称/单位/单价/消耗量）
        header_row = find_header_row(data, sorted_cols)
        if header_row is None:
            continue

        # 逐行解析，区分材料行和机械行
        current_section = None  # "材料" or "机械"
        for ri in range(header_row + 1, len(data)):
            if ri >= len(data):
                break
            row = data[ri]

            # 确定本行有哪些列有值
            if len(row) <= quota_start:
                continue

            # ci=0: 类型标识（材料/机械/空）
            first_cell = clean(row[0]) if len(row) > 0 else ""
            if first_cell == "材料":
                current_section = "材料"
            elif first_cell == "机械":
                current_section = "机械"
            elif first_cell == "" and current_section is None:
                # 没有类型标识，跳过
                continue
            elif first_cell not in ["", "其中", "人工费(元)", "材料费(元)",
                                     "机械费(元)", "费用(元)", "增值税(元)",
                                     "全费用(元)", "名称", "单位", "单价(元)", "消耗量"]:
                # 非空非标签，可能是不认识的行，跳过
                if current_section is None:
                    continue

            if current_section not in ["材料", "机械"]:
                continue

            # ci=1: 名称, ci=2: 单位, ci=3: 单价
            name = clean(row[1]) if len(row) > 1 else ""
            unit = clean(row[2]) if len(row) > 2 else ""
            unit_price_raw = row[3] if len(row) > 3 else None
            unit_price = to_float(unit_price_raw) if unit_price_raw else None

            # 检查是否为有效行（有名称）
            if not name or name in ["", "其中", "人工费(元)", "材料费(元)",
                                     "机械费(元)", "费用(元)", "增值税(元)",
                                     "全费用(元)", "名称", "单位", "单价(元)", "消耗量"]:
                # 可能是机械行（名称在 ci=1）
                if first_cell == "机械":
                    name = clean(row[1]) if len(row) > 1 else ""
                    unit = clean(row[2]) if len(row) > 2 else ""
                    up = row[3] if len(row) > 3 else None
                    unit_price = to_float(up) if up else None
                else:
                    continue

            if not name:
                continue

            # 跳过金额行（名称列含费用标签）
            if any(kw in name for kw in ["人工费", "材料费", "机械费", "费用", "增值税", "全费用"]):
                continue

            # 提取各 quota 列的消耗量
            target_dict = materials_results if current_section == "材料" else machinery_results
            for ci in sorted_cols:
                code = quota_cols[ci]
                if ci >= len(row):
                    continue
                consumption = to_float(row[ci])
                if consumption is None:
                    continue

                if code not in target_dict:
                    target_dict[code] = []

                target_dict[code].append({
                    "名称": name,
                    "单位": unit,
                    "单价(元)": unit_price,
                    "消耗量": consumption
                })

    doc.close()

    # 排序输出
    materials_sorted = dict(sorted(materials_results.items()))
    machinery_sorted = dict(sorted(machinery_results.items()))

    # 保存
    MAT_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with open(MAT_OUTPUT, "w", encoding="utf-8") as f:
        json.dump(materials_sorted, f, ensure_ascii=False, indent=2)

    MECH_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with open(MECH_OUTPUT, "w", encoding="utf-8") as f:
        json.dump(machinery_sorted, f, ensure_ascii=False, indent=2)

    print(f"\n材料明细: {len(materials_sorted)} 条定额")
    print(f"机械明细: {len(machinery_sorted)} 条定额")
    print(f"输出文件:")
    print(f"  材料: {MAT_OUTPUT}")
    print(f"  机械: {MECH_OUTPUT}")

    # 验证
    print("\n验证（A9-1 前3条材料）:")
    items = materials_sorted.get("A9-1", [])
    for item in items[:3]:
        print(f"  {item['名称']} {item['单位']} 单价={item['单价(元)']} 消耗量={item['消耗量']}")

    print("\n验证（A16-1 前3条机械）:")
    items = machinery_sorted.get("A16-1", [])
    for item in items[:3]:
        print(f"  {item['名称']} {item['单位']} 单价={item['单价(元)']} 消耗量={item['消耗量']}")


if __name__ == "__main__":
    main()
