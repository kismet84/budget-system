#!/usr/local/bin/python3
"""
提取"计量单位：见表"页的定额编号和页码。
"""

import fitz, re, json

pdf_path = '/Users/kis/.hermes/memory/projects/budget-system/data/定额/raw/装饰/《湖北省房屋建筑与装饰工程消耗量定额及全费用基价表》（装饰·措施）（2024）.pdf'
output_path = '/Users/kis/.hermes/memory/projects/budget-system/data/定额/parsed/装饰/计量单位_见表_页码.json'

doc = fitz.open(pdf_path)

def fw(s):
    r = []
    for ch in s:
        if '１' <= ch <= '９': r.append(chr(ord(ch)-0xFF10+0x30))
        elif ch == '０': r.append('0')
        else: r.append(ch)
    return ''.join(r)

results = []

for pg_idx in range(len(doc)):
    text = doc[pg_idx].get_text()
    if not re.search(r'计量单位[：:]\s*见', text):
        continue

    words = doc[pg_idx].get_text('words')

    # 提取定额编号（y≈10-50）
    quota_ids = []
    for w in words:
        if 10 < w[1] < 50:
            m = re.search(r'[ＡA]([１-９\d]+)[⁃‐‑–—―-]?([１-９\d]+)', w[4])
            if m:
                qid = 'A' + fw(m.group(1)) + '-' + fw(m.group(2))
                quota_ids.append(qid)

    results.append({
        'page_index': pg_idx,
        'page_number': pg_idx + 1,
        'quota_ids': quota_ids,
    })

    print(f"pg_idx={pg_idx} (page={pg_idx+1}): {len(quota_ids)} 个定额")

print(f"\n共 {len(results)} 页，{sum(len(r['quota_ids']) for r in results)} 个定额编号")

with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)
print(f"已保存到 {output_path}")
