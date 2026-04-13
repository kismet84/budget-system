#!/usr/local/bin/python3
"""
统一提取定额计量单位。

两种页面类型：
1. 明确计量单位：表头写"计量单位：100m²"，直接提取分配给该页所有定额
2. 计量单位：见袁：单位在各定额列下方，需要从 words 按 y 分组 + x 位置匹配提取

输出：计量单位_统一.json
"""

import fitz, re, json
from itertools import groupby

PDF_PATH = '/Users/kis/.hermes/memory/projects/budget-system/data/定额/raw/装饰/《湖北省房屋建筑与装饰工程消耗量定额及全费用基价表》（装饰·措施）（2024）.pdf'
PROJECT_NAMES_PATH = '/Users/kis/.hermes/memory/projects/budget-system/data/定额/parsed/装饰/project_names.json'
OUTPUT_PATH = '/Users/kis/.hermes/memory/projects/budget-system/data/定额/parsed/装饰/计量单位_统一.json'

# ============================================================
# 工具函数（统一实现，各脚本共用）
# ============================================================

def to_half_width(t: str) -> str:
    """全角→半角：0xFF01-0xFF5E（数字/字母/符号），0x3000→空格"""
    result = []
    for ch in str(t):
        code = ord(ch)
        if 0xFF01 <= code <= 0xFF5E:
            code -= 0xFEE0
        elif code == 0x3000:
            code = 0x0020
        result.append(chr(code))
    return ''.join(result)


def fw(s: str) -> str:
    """全角数字→半角（保留其他字符不动）"""
    result = []
    for ch in s:
        if '１' <= ch <= '９':
            result.append(chr(ord(ch) - 0xFF10 + 0x30))
        elif ch == '０':
            result.append('0')
        else:
            result.append(ch)
    return ''.join(result)


def normalize_unit(raw: str) -> str | None:
    """归一化单位文本，返回 canonical 单位或 None（浮点数/价格列）"""
    raw = to_half_width(raw)
    raw = fw(raw)
    raw = raw.replace('m2', 'm²').replace('m3', 'm³')
    # 拒绝纯数字/浮点数（来自价格/消耗量列）
    if re.match(r'^\d+(?:\.\d+)?$', raw):
        return None
    # 去掉数量前缀
    raw = re.sub(r'^\d+(?:\.\d+)?', '', raw)
    mapping = [
        ('100m²', 'm²'), ('100m³', 'm³'), ('100m', 'm'),
        ('10m²', 'm²'), ('10m³', 'm³'), ('10m', 'm'),
        ('m³', 'm³'), ('m²', 'm²'), ('t', 't'), ('kg', 'kg'),
        ('个', '个'), ('套', '套'), ('樘', '樘'), ('项', '项'), ('节', '节'), ('m', 'm'),
        ('根', '根'), ('榀', '榀'), ('扇', '扇'), ('座', '座'), ('组', '组'),
        ('件', '件'), ('盏', '盏'), ('副', '副'), ('只', '只'),
        ('块', '块'), ('片', '片'), ('把', '把'),
    ]
    for k, v in mapping:
        if k in raw:
            return v
    return None  # 非标准单位


def extract_quantity(raw: str) -> str | None:
    """从 raw 字符串提取数量前缀，拒绝浮点数和 >500 的异常值"""
    raw = to_half_width(raw)
    raw = fw(raw)
    raw = raw.replace('m2', 'm²').replace('m3', 'm³')
    m = re.match(r'^(\d+(?:\.\d+)?)', raw)
    if not m:
        return None
    q = m.group(1)
    if '.' in q:  # 拒绝浮点数
        return None
    if int(q) > 500:  # 正常前缀最大 350
        return None
    return q


def find_unit_candidates(raw: str) -> list[dict]:
    """从合并行中提取所有可能的单位子模式"""
    raw = to_half_width(raw)
    raw = fw(raw)
    raw = raw.replace('m2', 'm²').replace('m3', 'm³')
    candidates = []
    # 匹配 100m² / 10m³ / 10m / 100m 等
    for m in re.finditer(r'(\d+)(m²|m³|m)(?!\w)', raw):
        unit_map = {'m²': 'm²', 'm³': 'm³', 'm': 'm'}
        candidates.append({'quantity': m.group(1), 'unit': unit_map[m.group(2)], 'pos': m.start()})
    # 匹配 100个 / 10套 等
    for m in re.finditer(r'(\d+)(个|套|樘|项|节|盏|副|只|根|扇|块|片|榀|把|组|t|kg|件|座)(?!\w)', raw):
        candidates.append({'quantity': m.group(1), 'unit': m.group(2), 'pos': m.start()})
    # 匹配纯单位（无数量前缀）
    for m in re.finditer(r'^(m²|m³|m|t|kg|个|套|樘|项|节|盏|副|只|根|扇|块|片|榀|把|组|件|座)', raw):
        candidates.append({'quantity': '1', 'unit': m.group(1), 'pos': m.start()})
    return candidates


def parse_unit(raw: str) -> dict | None:
    """解析单个单位字符串，返回 {quantity, unit} 或 None"""
    candidates = find_unit_candidates(raw)
    return candidates[0] if candidates else None


# ============================================================
# 核心提取逻辑
# ============================================================

def extract_page_unit_from_header(page_text: str) -> tuple[str | None, str | None]:
    """从页面顶部'计量单位：XXX'行提取数量和单位"""
    m = re.search(r'计量单位[：:]\s*(.+)', page_text)
    if not m:
        return None, None
    raw = to_half_width(m.group(1)).strip()
    # 跳过"见袁/见上表"等
    if '见' in raw:
        return None, None
    q = extract_quantity(raw)
    u = normalize_unit(raw)
    return q, u


def group_words_by_line(words, y_tolerance: int = 5) -> list[dict]:
    """按 y 分组 words，y 差< tolerance 视为同一行"""
    groups = {}
    for w in words:
        y_key = round(w[1] / y_tolerance) * y_tolerance
        if y_key not in groups:
            groups[y_key] = []
        groups[y_key].append(w)
    lines = []
    for y_key, ws in sorted(groups.items()):
        ws_sorted = sorted(ws, key=lambda w: w[0])
        merged_text = ''.join(w[4] for w in ws_sorted)
        lines.append({
            'y': y_key,
            'text': merged_text,
            'x_min': min(w[0] for w in ws_sorted),
            'x_max': max(w[0] + w[2] - w[0] for w in ws_sorted),
            'words': ws_sorted,
        })
    return lines


def extract_see_table_units(pdf, pg_idx: int) -> dict:
    """
    从'计量单位：见袁'页提取各列实际单位。

    策略：
    1. 定额编号行 y=10-80 → 建立 x→quota_id 映射
    2. 单位行 y=75-135 → 收集所有 words，按 y 分组合并
    3. 收集每行中每个 unit candidate 的 x 位置
    4. 每个 quota 的 x 位置，找最近的 unit candidate
    """
    page = pdf[pg_idx]
    words = page.get_text('words')

    # 步骤1：提取定额编号（y=10-80）
    quota_x_map = {}  # x -> quota_id
    for w in words:
        if 10 < w[1] < 80:
            m = re.search(r'[ＡA]([１-９\d]+)[⁃‐‑–—―-]?([１-９\d]+)', w[4])
            if m:
                qid = 'A' + fw(m.group(1)) + '-' + fw(m.group(2))
                quota_x_map[int(w[0])] = qid

    if not quota_x_map:
        return {}

    # 步骤2：收集单位行的 words（y=75-135），过滤表头词
    skip_words = {'综合', '单价', '人工', '材料', '机械', '管理', '利润', '规费',
                  '名称', '规格', '型号', '定额', '编号', '含量', '费', '用', '其',
                  '中', '名', '称', '单位', '增值税', '除税', '税率', '增', '值',
                  '税', '项', '目', '带', '不带', '垫', '板', '棍', '压', '铜',
                  '质', '件', '１', '２', '３', '４', '５', '６', '７', '８', '９', '０',
                  '.', '－', '-', '、', '，', '。', ' ', '　', '(', ')', '（', '）',
                  '名', '称', '单', '价', '元', '消', '耗', '量',
                  '全', '费', '人', '工', '料', '机', '械', '其', '中',
                  '增', '值', '税', '管理', '利润', '规费', '项目', '序号', '编号'}

    # 步骤3：收集每行中每个 unit candidate 的 x 位置
    # 结构：[(x_position, {quantity, unit}), ...]
    unit_candidates = []  # (x, result_dict)

    for w in words:
        if 75 < w[1] < 135:
            txt = to_half_width(w[4]).strip()
            if not txt or re.match(r'^[0-9\.\-]+$', txt):
                continue
            if txt in skip_words:
                continue
            parsed = parse_unit(w[4])  # 用原始文本（含全角）
            if parsed:
                unit_candidates.append((int(w[0]), parsed))

    # 步骤4：每个 quota 找最近的 unit candidate
    result = {}
    sorted_quota_x = sorted(quota_x_map.items(), key=lambda x: x[0])
    for qx, qid in sorted_quota_x:
        best = None
        best_dist = 100
        for (ux, uc) in unit_candidates:
            dist = abs(ux - qx)
            if dist < best_dist:
                best_dist = dist
                best = uc

        if best and best_dist < 80:
            result[qid] = best
        else:
            result[qid] = {'quantity': None, 'unit': None}

    return result


# ============================================================
# 主流程
# ============================================================

def extract_all_units() -> dict:
    pdf = fitz.open(PDF_PATH)
    print(f"PDF 总页数: {pdf.page_count}")

    # 步骤1：扫描全 PDF，建立 page→unit 映射
    page_unit_map = {}  # pg_idx -> raw_unit_str or '见袁'
    for pg_idx in range(pdf.page_count):
        text = pdf[pg_idx].get_text()
        if '计量单位' not in text:
            continue
        m = re.search(r'计量单位[：:]\s*([^\s\n　]+)', text)
        if not m:
            continue
        raw = m.group(1)
        if '见' in raw or '袁' in raw:
            page_unit_map[pg_idx] = '见袁'
        else:
            page_unit_map[pg_idx] = raw

    # 步骤2：扫描全 PDF，建立 quota_id→page 映射
    qid_to_page = {}
    for pg_idx in range(pdf.page_count):
        words = pdf[pg_idx].get_text('words')
        for w in words:
            if 10 < w[1] < 80:
                m = re.search(r'[ＡA]([１-９\d]+)[⁃‐‑–—―-]?([１-９\d]+)', w[4])
                if m:
                    qid = 'A' + fw(m.group(1)) + '-' + fw(m.group(2))
                    qid_to_page[qid] = pg_idx

    # 步骤3：读取 project_names.json 确保覆盖所有定额
    with open(PROJECT_NAMES_PATH, encoding='utf-8') as f:
        project_names = json.load(f)

    results = {}  # quota_id -> {quantity, unit}
    see_table_qids = []

    for qid in project_names.keys():
        pg_idx = qid_to_page.get(qid)
        if pg_idx is None:
            continue

        unit_str = page_unit_map.get(pg_idx)
        if unit_str is None:
            continue

        if unit_str == '见袁':
            see_table_qids.append(qid)
            continue

        q, u = extract_page_unit_from_header(f"计量单位：{unit_str}")
        if q is None and u is None:
            continue
        results[qid] = {'quantity': q, 'unit': u}

    # 步骤4：处理"见袁"页
    see_table_pages = sorted(set(qid_to_page[q] for q in see_table_qids))
    print(f"\n发现 {len(see_table_pages)} 页'见袁'，{len(see_table_qids)} 个定额")
    for pg_idx in see_table_pages:
        units = extract_see_table_units(pdf, pg_idx)
        matched = sum(1 for q, d in units.items() if d['quantity'] is not None)
        print(f"  pg_idx={pg_idx}: {len(units)} 个定额，匹配 {matched} 条")
        for qid, data in units.items():
            if qid in see_table_qids:
                results[qid] = data

    pdf.close()

    with_q = sum(1 for d in results.values() if d['quantity'] is not None)
    without_q = sum(1 for d in results.values() if d['quantity'] is None)
    print(f"\n提取成功（含数量）: {with_q} 条")
    print(f"无数量前缀: {without_q} 条")

    return results


if __name__ == '__main__':
    print('=' * 50)
    print('统一提取定额计量单位')
    print('=' * 50)

    results = extract_all_units()

    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n已保存到 {OUTPUT_PATH}")

    # 统计
    unit_dist = {}
    q_dist = {}
    for v in results.values():
        u = v['unit'] or '无'
        q = v['quantity'] or '无'
        unit_dist[u] = unit_dist.get(u, 0) + 1
        q_dist[q] = q_dist.get(q, 0) + 1

    print("\n单位分布（前10）:")
    for u, cnt in sorted(unit_dist.items(), key=lambda x: -x[1])[:10]:
        print(f"   {u}: {cnt}条")
    print("\n数量前缀分布:")
    for q, cnt in sorted(q_dist.items(), key=lambda x: -x[1]):
        print(f"   {q}: {cnt}条")
