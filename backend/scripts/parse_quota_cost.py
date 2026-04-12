#!/usr/bin/env python3
"""
提取定额费用数据（全费用、人工费、材料费、机械费、费用、增值税）
输出: data/定额/parsed/装饰/quota_costs.json

表格结构（每页）：
  定额编号行 → 各列 col4+ 为定额编号（每个占一列）
  全费用行   → 各列 col4+ 为全费用数值
  人工费行   → 各列 col4+ 为人工费数值
  ...（以下各行同理）

关键差异：
  · 页67（A10-1~A10-6）：中间有规格/单位行 → 全费用在 R03
  · 页69（A10-11~A10-13）：无规格行         → 全费用在 R02
  · 页70（A10-14~A10-17）：可能有规格行       → 全费用在 R04
  · 页126（A10-171~A10-174）：无规格行        → 全费用在 R02

解决方案：
  1. 在列0中动态查找 "全费用（元）" 所在行（label_row = 全费用行）
  2. 各费用字段 = label_row + 固定偏移
  3. 读取对应列的值
"""

import json
import re
import os
import sys
from pathlib import Path

PDF_PATH = Path(__file__).parent.parent.parent / "data/定额/raw/装饰/《湖北省房屋建筑与装饰工程消耗量定额及全费用基价表》（装饰·措施）（2024）.pdf"
OUTPUT_PATH = Path(__file__).parent.parent.parent / "data/定额/parsed/装饰/quota_costs.json"

try:
    import fitz
except ImportError:
    print("请先安装 PyMuPDF: pip install pymupdf")
    sys.exit(1)


def no_space(text):
    """移除所有空白字符"""
    if not text:
        return ""
    return re.sub(r"\s+", "", str(text))


def normalize(text):
    """全角→半角，统一破折号"""
    if not text:
        return ""
    result = []
    for ch in str(text):
        code = ord(ch)
        if 0xFF01 <= code <= 0xFF5E:
            code -= 0xFEE0
        elif code == 0x3000:
            code = 0x0020
        result.append(chr(code))
    text = "".join(result)
    text = re.sub(r"[\s⁃‐‑–—―\-]+", "-", text)
    return text.strip("-")


def clean_quota_code(v):
    """从单元格提取定额编号"""
    if not v:
        return None
    v = normalize(v)
    m = re.match(r"^([A-Z]\d+)-(\d+)$", v)
    if m:
        return m.group(1) + "-" + m.group(2)
    return None


def to_float(val_str):
    """字符串 → 浮点数，'－'/空/'-' → None"""
    if not val_str:
        return None
    val = str(val_str)
    result = []
    for ch in val:
        code = ord(ch)
        if 0xFF01 <= code <= 0xFF5E:
            code -= 0xFEE0
        elif code == 0x3000:
            code = 0x0020
        result.append(chr(code))
    val = "".join(result)
    val = val.replace(",", "").replace("，", "").replace("．", ".")
    try:
        return float(re.sub(r"[^\d.\-]", "", val))
    except ValueError:
        return None


# 各费用字段相对"全费用"行的偏移
COST_ROW_OFFSETS = {
    "全费用": 0,
    "人工费": 1,
    "材料费": 2,
    "机械费": 3,
    "费用": 4,
    "增值税": 5,
}


def find_label_row(data, label):
    """
    在列0中查找标签所在行索引。
    返回该行在 data 中的索引。
    """
    target = no_space(label)
    for ri in range(min(20, len(data))):
        if ri >= len(data) or not data[ri]:
            continue
        cell0 = data[ri][0] if len(data[ri]) > 0 else None
        if cell0 and no_space(cell0) == target:
            return ri
    return None


def main():
    print("=" * 60)
    print("定额费用数据提取（v3 — 动态行定位）")
    print("=" * 60)

    doc = fitz.open(PDF_PATH)
    print(f"PDF 总页数: {len(doc)}")

    results = {}
    skipped_pages = 0
    empty_pages = 0

    for fitz_idx in range(len(doc)):
        page = doc[fitz_idx]
        tabs = page.find_tables()
        if not tabs.tables:
            empty_pages += 1
            continue

        data = tabs.tables[0].extract()
        if not data or len(data) < 8:
            skipped_pages += 1
            continue

        # ---- Step 1: 找"全费用（元）"标签行（动态）----
        full_row = find_label_row(data, "全费用（元）")
        if full_row is None:
            skipped_pages += 1
            continue

        # ---- Step 2: 建立列索引 → quota_id 映射----
        r00 = data[0]
        quota_cols = {}
        for ci in range(len(r00)):
            code = clean_quota_code(r00[ci])
            if code:
                quota_cols[ci] = code

        if not quota_cols:
            continue

        # ---- Step 3: 对每个 quota，读取各费用字段----
        for ci, quota_id in quota_cols.items():
            cost_values = {}

            for cost_type, offset in COST_ROW_OFFSETS.items():
                ri = full_row + offset
                if ri >= len(data):
                    continue
                if ci >= len(data[ri]):
                    continue

                raw_val = data[ri][ci]
                if not raw_val:
                    continue

                # 跳过标签类内容
                ns = no_space(raw_val)
                if ns in [
                    "其中",
                    "人-工-费(元)", "人-工-费（元）",
                    "材-料-费(元)", "材-料-费（元）",
                    "机-械-费(元)", "机-械-费（元）",
                    "费-用(元)", "费-用（元）",
                    "增-值-税(元)", "增-值-税（元）",
                    "全-费-用(元)", "全-费-用（元）",
                    "名称", "单位", "单价",
                    "名称消耗量", "名称单价",
                ]:
                    continue

                f = to_float(raw_val)
                cost_values[cost_type] = f

            results[quota_id] = cost_values

    doc.close()

    # ---- Step 4: 排序输出----
    sorted_results = dict(sorted(results.items()))

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(sorted_results, f, ensure_ascii=False, indent=2)

    print(f"\n提取到 {len(sorted_results)} 条费用数据")
    print(f"输出文件: {OUTPUT_PATH}")
    print(f"跳过页数: {skipped_pages}，无表格页: {empty_pages}")

    # ---- Step 5: 验证----
    print("\n验证（重点定额）:")
    targets = ["A10-1", "A10-11", "A10-12", "A10-174", "A14-23", "A14-18"]
    for code in targets:
        if code in sorted_results:
            c = sorted_results[code]
            parts = []
            for k in COST_ROW_OFFSETS:
                v = c.get(k)
                if v is not None:
                    parts.append("{}={:.2f}".format(k, v))
                else:
                    parts.append("{}=-".format(k))
            print("  {}: {}".format(code, " ".join(parts)))
        else:
            print("  {}: ❌ 未提取".format(code))

    # ---- Step 6: 校验和（全费用 ≈ 人工费+材料费+机械费+费用+增值税）----
    print("\n校验和检查:")
    errors = 0
    for code, c in sorted_results.items():
        vals = [c.get(k) for k in COST_ROW_OFFSETS]
        if any(v is None for v in vals):
            continue
        total_fee, labor, mat, mach, fee, tax = vals
        mach = mach or 0.0
        expected = labor + mat + mach + fee + tax
        diff = abs(total_fee - expected)
        if diff > 1.0:
            errors += 1
            if errors <= 5:
                print("  ❌ {}: 全费用={:.2f}, 合计={:.2f}, 差={:.2f}".format(
                    code, total_fee, expected, diff))
    if errors == 0:
        print("  ✅ 全部通过（误差<1元）")
    else:
        print("  ⚠️  {} 条有误差（可能因原始PDF格式不标准）".format(errors))


if __name__ == "__main__":
    main()
