#!/usr/bin/env python3
"""
从原始 PDF 提取定额计量单位（数量 + 单位）

输出格式：{quota_id: {"quantity": "100", "unit": "m²"}, ...}
- quantity: 数量前缀字符串（如 "100", "10", "1"），无数量时为 null
- unit:     单位字符串（如 "m²", "个", "t"），无单位时为 null

PDF 中有两种页面：
1. 明确计量单位：表头写"计量单位：100m²"，所有列共用同一个单位
2. 计量单位：见表 — 单位在各定额列下方，需要从列中提取
"""
import fitz
import re
import json
from pathlib import Path
from collections import defaultdict

# ===== 配置 =====
PDF_PATH = Path(__file__).parent.parent.parent / "data" / "定额" / "raw" / "装饰" / "《湖北省房屋建筑与装饰工程消耗量定额及全费用基价表》（装饰·措施）（2024）.pdf"
OUTPUT_FILE = Path(__file__).parent.parent.parent / "data" / "定额" / "parsed" / "装饰" / "计量单位.json"

# ===== 工具函数 =====

def to_half_width(text):
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


def clean_text(text):
    if not text:
        return ""
    return re.sub(r'[\s\u3000\n]+', '', str(text)).strip()


def extract_quantity(raw: str):
    """从 raw 计量单位字符串提取数量前缀

    定额计量单位只有固定的几种数量前缀：100, 10, 1, 350, 120, 240。
    如果提取到浮点数或大于 1000 的数，说明取到了价格/消耗量列，判定为无效。
    """
    raw = clean_text(raw)
    raw = to_half_width(raw)
    raw = raw.replace('m2', 'm²').replace('m3', 'm³')
    m = re.match(r'^(\d+(?:\.\d+)?)', raw)
    if not m:
        return None
    q = m.group(1)
    # 拒绝浮点数（来自价格/消耗量列）
    if '.' in q:
        return None
    # 拒绝大于 500 的数（正常数量前缀最大是 350）
    if int(q) > 500:
        return None
    return q


def normalize_unit(raw: str):
    """归一化单位文本"""
    raw = clean_text(raw)
    raw = to_half_width(raw)
    raw = raw.replace('m2', 'm²').replace('m3', 'm³')
    # 拒绝纯数字/浮点数（来自价格/消耗量列）
    if re.match(r'^\d+(?:\.\d+)?$', raw):
        return None
    # 去掉数量前缀（如 "100根" → "根", "10榀" → "榀"）
    raw = re.sub(r'^\d+(?:\.\d+)?', '', raw)
    mapping = [
        ('100m²', 'm²'), ('100m³', 'm³'), ('100m', 'm'),
        ('10m²', 'm²'), ('10m³', 'm³'), ('10m', 'm'),
        ('m³', 'm³'), ('m²', 'm²'), ('t', 't'), ('kg', 'kg'),
        ('个', '个'), ('套', '套'), ('樘', '樘'), ('项', '项'), ('节', '节'), ('m', 'm'),
        ('根', '根'), ('榀', '榀'), ('扇', '扇'), ('座', '座'), ('组', '组'), ('件', '件'),
    ]
    for k, v in mapping:
        if k in raw:
            return v
    return to_half_width(raw)  # 未匹配到已知单位时返回原始文本


# ===== 核心提取逻辑 =====

def extract_page_unit_from_header(page_text):
    """从页面顶部的'计量单位：XXX'行提取数量和单位"""
    m = re.search(r'计量单位[：:]\s*(.+)', page_text)
    if not m:
        return None, None
    raw = clean_text(m.group(1))
    q = extract_quantity(raw)
    u = normalize_unit(raw)
    if u == raw:
        return None, u
    return q, u


def _extract_from_unit_row(words, sorted_quota_x):
    """
    核心提取函数：从单位行（y≈90-130）提取每个 quota 列对应的单位。

    PDF 材料明细表结构：
      - "名称"列 x≈25-60    → 材料名
      - "单位"列 x≈130-165  → 材料单位（本列是公共列，所有 quota 共用同一个"单位"表头）
      - 定额1消耗量 x≈220-260
      - 定额2消耗量 x≈275-315
      - ...

    但实际上：单位行（y≈90-130）的文本是在材料表头（含"名称 单位 单价 消耗量"），
    而每个定额列下方的消耗量（y=140+）才对应各自的单位。

    正确策略：对于"计量单位：见表"页，单位行（y≈90-130）有 x 个文本块，
    每个文本块对应一个 quota 列，文本内容是该列的材料单位。

    我们只需要找到单位行（y≈90-130）中最接近每个 quota x 位置的文本。
    """
    # 收集单位行的所有文本（y=75-135）
    unit_row_words = []
    for w in words:
        if 75 < w[1] < 135:
            txt = to_half_width(w[4]).strip()
            if not txt:
                continue
            # 过滤表头标签词
            if txt in ('名', '称', '单', '价', '(', '元)', '消', '耗', '量',
                       '名称', '单位', '单价', '(元)', '消耗量',
                       '全', '费', '用', '人', '工', '料', '材', '机', '械',
                       '其', '中', '增', '值', '税', '管理', '利润', '规费',
                       '项目', '序号', '编号'):
                continue
            unit_row_words.append((w[0], w[1], txt))

    if not unit_row_words:
        return {}

    # 对每个 quota，找最近邻的单位行文本
    result = {}
    for qx, qid in sorted_quota_x:
        best = None
        best_dist = 999
        for ux, uy, utxt in unit_row_words:
            dist = abs(ux - qx)
            if dist < best_dist:
                best = (ux, uy, utxt)
                best_dist = dist

        if best and best_dist < 80:
            # 先提取数量（包含数量的才可能是有效单位行）
            q = extract_quantity(best[2])
            if q is None:
                # 提取不到有效数量前缀 → 跳过（取到了价格/消耗量/项目名列）
                result[qid] = {"quantity": None, "unit": None}
                continue
            # 再归一化单位
            norm = normalize_unit(best[2])
            if norm:
                result[qid] = {"quantity": q, "unit": norm}
            else:
                # 归一化失败（非标准单位文本）→ 标记 quantity=100 作为占位
                result[qid] = {"quantity": "100", "unit": None}
        else:
            result[qid] = {"quantity": None, "unit": None}

    return result


def extract_see_table_units(pdf, pg_idx):
    """从'计量单位：见表'页提取各列实际单位"""
    page = pdf[pg_idx]
    words = page.get_text('words')

    # 1. 找所有定额编号的 x 位置（y=10-50）
    quota_x_map = {}
    for w in words:
        if 10 < w[1] < 50:
            m = re.search(r'[ＡA]([１-９\d]+)[⁃‐‑–—―-]?([１-９\d]+)', w[4])
            if m:
                qid = 'A' + fwc(m.group(1)) + '-' + fwc(m.group(2))
                quota_x_map[w[0]] = qid

    if not quota_x_map:
        return {}

    sorted_quota_x = sorted(quota_x_map.items(), key=lambda x: x[0])

    # 2. 从单位行提取
    return _extract_from_unit_row(words, sorted_quota_x)


# ===== 主流程 =====

def extract_unit_from_pdf(pdf_path):
    pdf = fitz.open(pdf_path)
    print(f"PDF 总页数: {pdf.page_count}")

    result = {}

    see_table_pages = []
    for pg_idx in range(pdf.page_count):
        page = pdf[pg_idx]
        text = page.get_text()

        if '计量单位' not in text:
            continue

        if '见表' in text:
            see_table_pages.append(pg_idx)
        else:
            q, u = extract_page_unit_from_header(text)
            if q is None and u is None:
                continue
            codes = re.findall(r'[ＡA]([１-９\d]+)[⁃‐‑–—―-](\d+)', text, re.IGNORECASE)
            for d1, d2 in codes:
                qid = 'A' + fwc(d1) + '-' + fwc(d2)
                result[qid] = {"quantity": q, "unit": u}

    # 处理"计量单位：见表"页（pdf 保持打开）
    print(f"发现 {len(see_table_pages)} 页'计量单位：见表'，开始提取...")
    for pg_idx in see_table_pages:
        units = extract_see_table_units(pdf, pg_idx)
        for qid, data in units.items():
            result[qid] = data

    pdf.close()

    with_q = {k: v for k, v in result.items() if v["quantity"] is not None}
    without_q = {k: v for k, v in result.items() if v["quantity"] is None}

    print(f"提取到计量单位（含数量）: {len(with_q)} 条")
    print(f"无数量前缀: {len(without_q)} 条")

    return result


if __name__ == "__main__":
    print("=" * 50)
    print("从 PDF 提取定额计量单位（数量+单位）")
    print("=" * 50)

    if not PDF_PATH.exists():
        print(f"❌ PDF 文件不存在: {PDF_PATH}")
        exit(1)

    unit_map = extract_unit_from_pdf(PDF_PATH)

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(unit_map, f, ensure_ascii=False, indent=2)

    print(f"\n✅ 输出文件: {OUTPUT_FILE}")

    unit_dist = {}
    q_dist = {}
    for v in unit_map.values():
        u = v["unit"] or "无"
        q = v["quantity"] or "无"
        unit_dist[u] = unit_dist.get(u, 0) + 1
        q_dist[q] = q_dist.get(q, 0) + 1

    print("\n📊 单位分布（前10）:")
    for u, cnt in sorted(unit_dist.items(), key=lambda x: -x[1])[:10]:
        print(f"   {u}: {cnt}条")

    print("\n📊 数量前缀分布:")
    for q, cnt in sorted(q_dist.items(), key=lambda x: -x[1]):
        print(f"   {q}: {cnt}条")

    sample = list(unit_map.items())[:5]
    print("\n示例（前5条）:")
    for qid, v in sample:
        print(f"   {qid}: quantity={v['quantity']!r}, unit={v['unit']!r}")
