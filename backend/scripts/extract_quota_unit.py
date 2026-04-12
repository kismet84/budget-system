#!/usr/bin/env python3
"""
从原始 PDF 提取定额计量单位
PDF 中每个章节页都有明确的"计量单位："行，
关联到该页所有定额编号。
"""
import fitz
import re
import json
from pathlib import Path

# ===== 配置 =====
PDF_PATH = Path(__file__).parent.parent.parent / "data" / "定额" / "raw" / "装饰" / "《湖北省房屋建筑与装饰工程消耗量定额及全费用基价表》（装饰·措施）（2024）.pdf"
OUTPUT_FILE = Path(__file__).parent.parent.parent / "data" / "定额" / "parsed" / "装饰" / "计量单位.json"

# ===== 归一化函数 =====
def to_half_width(text):
    """全角转半角"""
    if not text:
        return text
    result = []
    for ch in str(text):
        code = ord(ch)
        if 0xFF01 <= code <= 0xFF5E:
            code -= 0xFEE0
        elif code == 0x3000:
            code = 0x0020
        result.append(chr(code))
    return ''.join(result)

def clean_text(text):
    """清理文本：去多余空白"""
    if not text:
        return ""
    return re.sub(r'[\s\u3000\n]+', '', str(text)).strip()

# ===== 提取逻辑 =====
def extract_unit_from_pdf(pdf_path):
    """逐页扫描，提取每页的计量单位及对应定额编号"""
    pdf = fitz.open(pdf_path)
    print(f"PDF 总页数: {pdf.page_count}")

    UNIT_PATTERNS = [
        r'计量单位[：:]\s*(.+)',
    ]

    # 定额编号正则（全角/半角兼容）
    # 匹配 A9-160 或 Ａ９-１６０ 格式
    CODE_PATTERNS = [
        re.compile(r'[ＡA][\d１-９\d]+[-－‐‑–—―⁃‐-](\d+)', re.IGNORECASE),
    ]

    unit_map = {}   # quota_id -> unit
    page_units = {} # page_idx -> unit（用于页内多个定额共享同一计量单位）

    pages_with_unit = 0
    codes_found = 0

    for pg_idx in range(pdf.page_count):
        page = pdf[pg_idx]
        text = page.get_text()

        # ---- 提取计量单位 ----
        unit = None
        for pat in UNIT_PATTERNS:
            m = re.search(pat, text)
            if m:
                raw_unit = clean_text(m.group(1))
                unit = normalize_unit(raw_unit)
                break

        if not unit:
            continue

        pages_with_unit += 1
        page_units[pg_idx] = unit

        # ---- 提取定额编号 ----
        # 匹配所有可能的定额编号格式（统一转大写）
        # 格式: A + 数字 + "-" + 数字
        all_codes_in_page = re.findall(
            r'[ＡA]([１-９\d]+)[-－‐‑–—―⁃‐-](\d+)',
            text,
            re.IGNORECASE
        )

        for d1, d2 in all_codes_in_page:
            # 全角数字转半角
            def fwc(s):
                result = []
                for ch in s:
                    if '１' <= ch <= '９':
                        result.append(chr(ord(ch) - 0xFF10 + 0x30))
                    elif ch == '０':
                        result.append('0')
                    else:
                        result.append(ch)
                return ''.join(result)

            prefix = 'A' + fwc(d1)
            num = fwc(d2)
            quota_id = f"{prefix}-{num}"

            if unit_map.get(quota_id) != unit:
                unit_map[quota_id] = unit
                codes_found += 1

    pdf.close()

    print(f"有计量单位的页: {pages_with_unit}")
    print(f"提取到计量单位的定额: {len(unit_map)} 条")

    return unit_map

def normalize_unit(raw: str) -> str:
    """归一化计量单位文本"""
    # 去多余空白
    raw = clean_text(raw)
    # 全角→半角
    raw = to_half_width(raw)
    # 先处理基础单位符号（全角m2/m3 → m²/m³）
    raw = raw.replace('m2', 'm²').replace('m3', 'm³')
    # 统一常见写法（按长度降序排列，避免 'm²' 先匹配 '100m²'）
    mapping = [
        ('100m²', '100m²'),
        ('100m³', '100m³'),
        ('100m',  '100m'),
        ('10m²',  '10m²'),
        ('10m³',  '10m³'),
        ('10m',   '10m'),
        ('m³',    'm³'),
        ('m²',    'm²'),
        ('t',     't'),
        ('kg',    'kg'),
        ('个',    '个'),
        ('套',    '套'),
        ('樘',    '樘'),
        ('项',    '项'),
        ('节',    '节'),
        ('m',     'm'),
    ]
    for k, v in mapping:
        if k in raw:
            return v
    return raw
    return raw

# ===== 主流程 =====
if __name__ == "__main__":
    print("=" * 50)
    print("从 PDF 提取定额计量单位")
    print("=" * 50)

    if not PDF_PATH.exists():
        print(f"❌ PDF 文件不存在: {PDF_PATH}")
        exit(1)

    unit_map = extract_unit_from_pdf(PDF_PATH)

    # 写入 JSON
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(unit_map, f, ensure_ascii=False, indent=2)

    print(f"\n✅ 输出文件: {OUTPUT_FILE}")

    # 统计计量单位分布
    unit_dist = {}
    for u in unit_map.values():
        unit_dist[u] = unit_dist.get(u, 0) + 1
    print("\n📊 计量单位分布（前10）:")
    for u, cnt in sorted(unit_dist.items(), key=lambda x: -x[1])[:10]:
        print(f"   {u}: {cnt}条")

    # 示例
    sample_ids = list(unit_map.keys())[:5]
    print("\n示例（前5条）:")
    for qid in sample_ids:
        print(f"   {qid}: {unit_map[qid]}")
