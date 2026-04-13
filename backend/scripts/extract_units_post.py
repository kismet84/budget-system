#!/usr/local/bin/python3
"""
计量单位后处理 — 从项目名称推断"见袁"定额的单位。

处理 extract_units.py 剩余的 quantity=NULL 条目，
从 project_names.json 的项目名称中提取计量单位。

用法：python3 scripts/extract_units_post.py
"""

import re, json, sys

PROJECT_NAMES_PATH = '/Users/kis/.hermes/memory/projects/budget-system/data/定额/parsed/装饰/project_names.json'
DB_CONFIG = dict(host='127.0.0.1', port=5432, database='budget_system', user='kis')

# ============================================================
# 工具函数（从 extract_units.py 统一实现）
# ============================================================

def to_half_width(t: str) -> str:
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
    result = []
    for ch in s:
        if '１' <= ch <= '９':
            result.append(chr(ord(ch) - 0xFF10 + 0x30))
        elif ch == '０':
            result.append('0')
        else:
            result.append(ch)
    return ''.join(result)


def _to_unit(u: str) -> str:
    return {'m2': 'm²', 'm3': 'm³'}.get(u, u)


COUNT_UNITS = {'个', '套', '樘', '扇', '孔', '根', 't', '件', '座', '组', '把', '榀', '片', '块', '盏', '副', '只'}


def extract_unit_from_name(name: str) -> str | None:
    """
    从项目名称推断计量单位。
    规则：
      1. 去除板厚/尺寸规格（板厚 NNmm, W×H, NNmm厚 等）
      2. 末尾有"数量+单位"（100m²、10m³、100m）：
         - 计量单位保留数量 → "100m²"
         - 计数单位返回纯单位 → "个"
      3. 末尾只有纯单位 → 返回纯单位
      4. 无法判断 → None
    """
    n = fw(to_half_width(name))

    # 有板厚 NNmm → 去除后提取纯单位
    has_thickness = bool(re.search(r'板厚\s*\d+\s*mm', n))
    if has_thickness:
        for _ in range(6):
            prev = n
            n = re.sub(r'\d+\s*[×xX*]\s*\d+', '', n)
            n = re.sub(r'板厚\s*\d+\s*mm', '', n)
            n = re.sub(r'\d+\s*mm\s*厚', '', n)
            if n == prev:
                break
        n = re.sub(r'^\S+\s*-\s*', '', n).strip()
        m = re.search(r'(m2|m3|m|个|套|樘|扇|孔|根|t|件|座|组|把|榀|片|块|盏|副|只)\s*$', n)
        if m:
            return _to_unit(m.group(1))
        return None

    # 有 W×H 尺寸 → 去除后提取纯单位
    n2 = re.sub(r'[（(][^)）]*[)）]', '', n)
    n2 = re.sub(r'^\S+\s*-\s*', '', n2).strip()

    has_dims = bool(re.search(r'\d+\s*[×xX*]\s*\d+', n2))
    if has_dims:
        for _ in range(6):
            prev = n2
            n2 = re.sub(r'\d+\s*[×xX*]\s*\d+', '', n2)
            if n2 == prev:
                break
        n2 = re.sub(r'^\S+\s*-\s*', '', n2).strip()
        m = re.search(r'(m2|m3|m|个|套|樘|扇|孔|根|t|件|座|组|把|榀|片|块|盏|副|只)\s*$', n2)
        if m:
            return _to_unit(m.group(1))
        return None

    # 无尺寸：找末尾"数量+单位"
    m = re.search(r'(\d+)\s*(m2|m3|m|个|套|樘|扇|孔|根|t|件|座|组|把|榀|片|块|盏|副|只)\s*$', n2)
    if m:
        qty, unit = m.group(1), m.group(2)
        u = _to_unit(unit)
        # 计量单位保留数量（100m²），计数单位返回纯单位
        if unit in COUNT_UNITS:
            return u
        return qty + u

    # 末尾纯单位
    m2 = re.search(r'(m2|m3|m|个|套|樘|扇|孔|根|t|件|座|组|把|榀|片|块|盏|副|只)\s*$', n2)
    if m2:
        return _to_unit(m2.group(1))

    return None


# ============================================================
# 主流程
# ============================================================

def main():
    import psycopg2

    # 读取 project_names.json
    with open(PROJECT_NAMES_PATH, encoding='utf-8') as f:
        project_names = json.load(f)

    # 查数据库中 quantity=NULL 的条目
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    cur.execute("SELECT quota_id, project_name FROM quotas WHERE quantity IS NULL OR unit IS NULL")
    null_rows = cur.fetchall()
    cur.close()
    conn.close()

    if not null_rows:
        print('没有需要处理的 NULL 条目')
        return

    print(f'共 {len(null_rows)} 条 quantity=NULL\n')

    results = {}  # quota_id -> (quantity, unit)
    for qid, db_name in null_rows:
        name = project_names.get(qid, db_name or '')
        inferred = extract_unit_from_name(name)

        if inferred:
            # 判断 inferred 是 "100m²" 形式还是 "m" 形式
            m = re.match(r'^(\d+)(.+)$', inferred)
            if m:
                results[qid] = (m.group(1), m.group(2))
            else:
                results[qid] = ('1', inferred)
        else:
            results[qid] = None

    # 统计
    inferred_cnt = sum(1 for v in results.values() if v is not None)
    failed_cnt = sum(1 for v in results.values() if v is None)
    print(f'自动推断成功: {inferred_cnt} 条')
    print(f'无法推断（需人工）: {failed_cnt} 条')

    if failed_cnt > 0:
        print('\n无法推断的条目:')
        for qid, db_name in null_rows:
            if results.get(qid) is None:
                name = project_names.get(qid, db_name or '')
                print(f'  {qid}: {name}')

    # 写入数据库
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    updated = 0
    for qid, val in results.items():
        if val is not None:
            q, u = val
            cur.execute('UPDATE quotas SET quantity=%s, unit=%s WHERE quota_id=%s', (q, u, qid))
            updated += cur.rowcount
    conn.commit()
    cur.close()
    conn.close()

    print(f'\n写入数据库: {updated} 条')


if __name__ == '__main__':
    main()
