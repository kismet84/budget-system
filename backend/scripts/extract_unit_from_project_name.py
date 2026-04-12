#!/usr/bin/env python3
"""
从项目名称提取计量单位 — 交互式脚本
处理 unit='见表' 的 108 条定额，逐条分析项目名称，提取计量单位。

用法：python3 scripts/extract_unit_from_project_name.py
"""
import re
import json
import psycopg2
from pathlib import Path

# ===== 配置 =====
SCRIPT_DIR = Path(__file__).parent.resolve()
PROJECT_DIR = SCRIPT_DIR.parent.parent
JSON_FILE = PROJECT_DIR / "data" / "定额" / "imported" / "装饰_合并定额.json"
DB_CONFIG = dict(host="localhost", port=5432, database="budget_system", user="kis")

# ===== 辅助函数 =====
def fwc(s: str) -> str:
    """全角→半角转换，同时处理上标字符"""
    result = []
    for ch in str(s):
        code = ord(ch)
        if code == 0x00B2:
            result.append('2')
        elif code == 0x00B3:
            result.append('3')
        elif 0xFF10 <= code <= 0xFF19:
            result.append(chr(code - 0xFF10 + 0x30))
        elif 0xFF01 <= code <= 0xFF5E:
            result.append(chr(code - 0xFEE0))
        elif code == 0xFF0A:
            result.append('*')
        elif code == 0x3000:
            result.append(' ')
        else:
            result.append(ch)
    return ''.join(result)

def has_wh(n: str) -> bool:
    return bool(re.search(r'\d+\s*[×xX*]\s*\d+', n))

def _to_unit(u: str) -> str:
    return {'m2': 'm²', 'm3': 'm³'}.get(u, u)

COUNT_UNITS = {'个', '套', '樘', '扇', '孔', '根', 't'}

def extract_unit(name: str):
    """
    推断规则：
      1. 有板厚NNmm → 去除，提取纯单位
      2. 有 W×H 尺寸 → 去除，提取纯单位
      3. 无尺寸，末尾有数量+单位：
         - 计量单位（m²/m³/m）→ 保留数量（100m²、100m）
         - 计数单位（个/套等）→ 返回纯单位
      4. 无数量，末尾只有纯单位 → 返回纯单位
      5. 其他 → "见表"
    """
    n = fwc(name)

    # 有板厚NNmm → 去除后提取纯单位
    has_thickness = bool(re.search(r'板厚\s*\d+\s*mm', n))
    if has_thickness:
        for _ in range(6):
            prev = n
            n = re.sub(r'\d+\s*[×xX*]\s*\d+', '', n)
            n = re.sub(r'板厚\s*\d+\s*mm', '', n)
            if n == prev:
                break
        n = re.sub(r'^\S+\s*-\s*', '', n).strip()
        m = re.search(r'(m2|m3|m|个|套|樘|扇|孔|根|t)\s*$', n)
        if m:
            return _to_unit(m.group(1))
        return "见表"

    # 去除括号
    n2 = re.sub(r'[（(][^)）]*[)）]', '', n)
    n2 = re.sub(r'^\S+\s*-\s*', '', n2).strip()

    has_dims = has_wh(n2)
    if has_dims:
        for _ in range(6):
            prev = n2
            n2 = re.sub(r'\d+\s*[×xX*]\s*\d+', '', n2)
            if n2 == prev:
                break
        n2 = re.sub(r'^\S+\s*-\s*', '', n2).strip()
        m = re.search(r'(m2|m3|m|个|套|樘|扇|孔|根|t)\s*$', n2)
        if m:
            return _to_unit(m.group(1))
        return "见表"
    else:
        # 无尺寸：找数量+单位
        m = re.search(r'(\d+)\s*(m2|m3|m|个|套|樘|扇|孔|根|t)\s*$', n2)
        if m:
            qty, unit = m.group(1), m.group(2)
            u = _to_unit(unit)
            # 计量单位保留数量（100m²），计数单位返回纯单位
            if unit in COUNT_UNITS:
                return u
            return qty + u
        # 末尾纯单位（无数量前缀）
        m2 = re.search(r'(m2|m3|m|个|套|樘|扇|孔|根|t)\s*$', n2)
        if m2:
            return _to_unit(m2.group(1))
        return "见表"


# ===== 主流程 =====
def main():
    print("=" * 60)
    print("计量单位提取 — 交互式脚本")
    print("=" * 60)

    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    cur.execute("SELECT quota_id FROM quotas WHERE unit = '见表'")
    见表明细 = [r[0] for r in cur.fetchall()]
    cur.close()
    conn.close()

    print(f"\n共 {len(见表明细)} 条 '见表'\n")

    with open(JSON_FILE, encoding="utf-8") as f:
        all_data = json.load(f)
    id_to_name = {r["定额编号"]: r["项目名称"] for r in all_data}

    # 预览统计
    summary = {}
    for qid in 见表明细:
        name = id_to_name.get(qid, "")
        auto = extract_unit(name)
        key = auto if auto else "保持见表"
        summary[key] = summary.get(key, 0) + 1
    print("━━━ 自动推断统计 ━━━")
    for k, v in sorted(summary.items(), key=lambda x: -x[1]):
        print(f"  {k}: {v}条")
    print()

    results = {}
    auto_all = input("是否全部跳过确认直接应用推断？[y/n]: ").strip().lower()
    if auto_all == 'y':
        for qid in 见表明细:
            name = id_to_name.get(qid, "")
            auto = extract_unit(name)
            results[qid] = auto if auto else "见表"
        print(f"已应用 {len(results)} 条")
    else:
        for qid in 见表明细:
            name = id_to_name.get(qid, "")
            auto = extract_unit(name)
            print(f"━━━ {qid} ━━")
            print(f"  项目名称: {name}")
            print(f"  推断: {auto or '（无）'}")
            line = input("  [回车=推断 | q=退出 | 输入=手动]: ").strip()
            if line.lower() == 'q':
                break
            if line:
                results[qid] = line
            elif auto:
                results[qid] = auto
            else:
                results[qid] = "见表"

    if results:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        updated = 0
        for qid, unit in results.items():
            cur.execute("UPDATE quotas SET unit=%s WHERE quota_id=%s", (unit, qid))
            if cur.rowcount > 0:
                updated += 1
        conn.commit()
        cur.close()
        conn.close()
        print(f"\n✅ 写入: {updated} 条")

    final_dist = {}
    for unit in results.values():
        final_dist[unit] = final_dist.get(unit, 0) + 1
    print("\n📊 最终分布:")
    for u, c in sorted(final_dist.items(), key=lambda x: -x[1]):
        print(f"   {u}: {c}条")


if __name__ == "__main__":
    main()
