#!/usr/local/bin/python3
"""
重新扫描全 PDF，提取所有定额的计量单位。
步骤1：建立页码→计量单位的映射
步骤2：为所有缺失的定额分配计量单位
"""

import fitz, re, json

pdf_path = '/Users/kis/.hermes/memory/projects/budget-system/data/定额/raw/装饰/《湖北省房屋建筑与装饰工程消耗量定额及全费用基价表》（装饰·措施）（2024）.pdf'
project_names_path = '/Users/kis/.hermes/memory/projects/budget-system/data/定额/parsed/装饰/project_names.json'
output_path = '/Users/kis/.hermes/memory/projects/budget-system/data/定额/parsed/装饰/计量单位_全部.json'

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
    """解析 '100m2' 或 '100' → {quantity, unit}"""
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

# 建立 page_index → 计量单位字符串 的映射
# 扫描每页，提取"计量单位：ＸＸ"
page_unit_map = {}  # pg_idx -> unit_str
for pg_idx in range(len(doc)):
    text = doc[pg_idx].get_text()
    # 找"计量单位：ＸＸ"
    m = re.search(r'计量单位[：:]\s*([^\s\n　]+)', text)
    if m:
        raw_unit = m.group(1)
        # 跳过"见..."
        if '见' in raw_unit or '袁' in raw_unit:
            page_unit_map[pg_idx] = '见袁'  # 标记为见表
        else:
            page_unit_map[pg_idx] = raw_unit

# 建立 quota_id → page_index 的映射
# 通过扫描每页的定额编号
qid_to_page = {}
for pg_idx in range(len(doc)):
    words = doc[pg_idx].get_text('words')
    for w in words:
        if 10 < w[1] < 80:
            m = re.search(r'[ＡA]([１-９\d]+)[⁃‐‑–—―-]?([１-９\d]+)', w[4])
            if m:
                qid = 'A' + fw(m.group(1)) + '-' + fw(m.group(2))
                qid_to_page[qid] = pg_idx

# 读取 project_names.json
with open(project_names_path) as f:
    project_names = json.load(f)

# 提取所有定额的计量单位
results = {}
missing = []

for qid in project_names.keys():
    pg_idx = qid_to_page.get(qid)
    if pg_idx is None:
        missing.append((qid, '未找到页码'))
        continue

    unit_str = page_unit_map.get(pg_idx)
    if unit_str is None:
        missing.append((qid, f'pg_idx={pg_idx}, 无计量单位'))
        continue

    if unit_str == '见袁':
        missing.append((qid, f'pg_idx={pg_idx}, 计量单位为见袁'))
        continue

    parsed = parse_unit(unit_str)
    if parsed:
        results[qid] = parsed
    else:
        missing.append((qid, f'pg_idx={pg_idx}, unit_str={unit_str!r}, parse失败'))

print(f"提取成功: {len(results)} 条")
print(f"缺失: {len(missing)} 条")

# 保存
with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)
print(f"已保存到 {output_path}")

# 打印缺失前20条
if missing:
    print(f"\n缺失示例 (前20):")
    for qid, reason in missing[:20]:
        print(f"  {qid}: {reason}")
