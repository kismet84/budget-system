#!/usr/local/bin/python3
"""
提取"计量单位：见表"页的定额编号和计量单位。
关键：m² 等单位可能被拆成多个 word，需要按 y 分组合并后再按 x 位置匹配。
"""

import fitz, re, json
from itertools import groupby

pdf_path = '/Users/kis/.hermes/memory/projects/budget-system/data/定额/raw/装饰/《湖北省房屋建筑与装饰工程消耗量定额及全费用基价表》（装饰·措施）（2024）.pdf'
output_path = '/Users/kis/.hermes/memory/projects/budget-system/data/定额/parsed/装饰/计量单位_见表.json'

doc = fitz.open(pdf_path)

def to_half_width(t):
    r = []
    for ch in str(t):
        code = ord(ch)
        if 0xFF01 <= code <= 0xFF5E: code -= 0xFEE0
        elif code == 0x3000: code = 0x0020
        r.append(chr(code))
    return ''.join(r)

def fw(s):
    r = []
    for ch in s:
        if '１' <= ch <= '９': r.append(chr(ord(ch)-0xFF10+0x30))
        elif ch == '０': r.append('0')
        else: r.append(ch)
    return ''.join(r)

def parse_unit(raw):
    """解析单个单位字符串"""
    raw = to_half_width(raw)
    raw = fw(raw)
    raw = raw.replace('m2', 'm²').replace('m3', 'm³')
    m = re.match(r'^(\d+)m²$', raw)
    if m: return {'quantity': m.group(1), 'unit': 'm²'}
    m = re.match(r'^(\d+)m³$', raw)
    if m: return {'quantity': m.group(1), 'unit': 'm³'}
    m = re.match(r'^(\d+)m$', raw)
    if m: return {'quantity': m.group(1), 'unit': 'm'}
    m = re.match(r'^(\d+)(个|套|樘|项|节|盏|副|只|根|扇|块|片|榀|把|组|t|kg)$', raw)
    if m: return {'quantity': m.group(1), 'unit': m.group(2)}
    if raw in ('m²', 'm³', 'm', 't', 'kg', '个', '套', '樘', '项', '节', '盏', '副', '只', '根', '扇', '块', '片', '榀', '把', '组'):
        return {'quantity': '1', 'unit': raw}
    return None

# 步骤1：找到所有"计量单位：见表"的页
see_table_pages = []
for pg_idx in range(len(doc)):
    text = doc[pg_idx].get_text()
    if re.search(r'计量单位[：:]\s*见', text):
        see_table_pages.append(pg_idx)

print(f"找到 {len(see_table_pages)} 页含'计量单位：见表'\n")

results = {}
total_matched = 0

for pg_idx in see_table_pages:
    page = doc[pg_idx]
    words = page.get_text('words')

    # 步骤2a：提取定额编号（y≈10-50）
    quota_x_map = {}  # x -> quota_id
    for w in words:
        if 10 < w[1] < 50:
            m = re.search(r'[ＡA]([１-９\d]+)[⁃‐‑–—―-]?([１-９\d]+)', w[4])
            if m:
                qid = 'A' + fw(m.group(1)) + '-' + fw(m.group(2))
                quota_x_map[int(w[0])] = qid

    if not quota_x_map:
        print(f"  pg_idx={pg_idx}: 无定额编号")
        continue

    # 步骤2b：收集单位区域的所有 words（y≈75-135）
    unit_words = []
    for w in words:
        if 75 < w[1] < 135:
            txt = to_half_width(w[4]).strip()
            if not txt:
                continue
            if re.match(r'^[0-9\.\-]+$', txt):
                continue
            skip = {'综合', '单价', '人工', '材料', '机械', '管理', '利润', '规费',
                    '名称', '规格', '型号', '定额', '编号', '含量', '费', '用', '其',
                    '中', '名', '称', '单位', '增值税', '除税', '税率', '增', '值',
                    '税', '项', '目', '带', '不带', '垫', '板', '棍', '压', '铜',
                    '质', '件', '１', '２', '３', '４', '５', '６', '７', '８', '９', '０',
                    '.', '－', '-', '、', '，', '。', ' ', '　', '(', ')', '（', '）'}
            if txt in skip:
                continue
            unit_words.append((int(w[0]), int(round(w[1]/5)*5), w[4]))

    # 步骤2c：每个定额找最近的单位 word
    page_matched = 0
    for qx, qid in sorted(quota_x_map.items()):
        best_word = None
        best_dist = 100
        for (ux, uy, uorig) in unit_words:
            dist = abs(ux - qx)
            if dist < best_dist:
                best_dist = dist
                best_word = (ux, uy, uorig)

        if best_word:
            ux, uy, uorig = best_word
            # 收集同 y 行的所有连续 words，合并成一个单位字符串
            row_words = [(ux2, uorig2) for (ux2, uy2, uorig2) in unit_words
                         if abs(uy2 - uy) < 5 and abs(ux2 - ux) < 60]
            row_words_sorted = sorted(row_words, key=lambda x: x[0])
            merged = ''.join(orig for _, orig in row_words_sorted)
            parsed = parse_unit(merged)
            if parsed:
                results[qid] = parsed
                page_matched += 1

    total_matched += page_matched
    status = '✓' if page_matched == len(quota_x_map) else f'({page_matched}/{len(quota_x_map)})'
    print(f"  pg_idx={pg_idx}: {len(quota_x_map)} 个定额 {status}")

print(f"\n共提取 {len(results)} 条（总匹配 {total_matched} 次）")

# 保存
with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)
print(f"已保存到 {output_path}")
