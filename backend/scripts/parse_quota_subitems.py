#!/usr/bin/env python3
"""
定额项目名称（含子项规格）提取脚本
从PDF原始表格中提取每列定额的子项规格信息（Row2 规格行 + Row3 子项），
与 parsed JSON 中的项目名称合并，输出 enriched 项目名称。
处理合并单元格：Row3 中某列有值但同行后续列为空 → 该值向右扩展到所有空列。
"""
import fitz
import re
import json
from pathlib import Path

# ============== 配置 ==============
PDF_PATH = "/Users/kis/.openclaw/memory/projects/budget-system/data/定额/raw/装饰/《湖北省房屋建筑与装饰工程消耗量定额及全费用基价表》（装饰·措施）（2024）.pdf"
PARSED_FILE = Path("/Users/kis/.openclaw/memory/projects/budget-system/data/定额/parsed/装饰_措施_全部.json")
OUTPUT_FILE = Path("/Users/kis/.openclaw/memory/projects/budget-system/data/定额/project_names.json")

# ============== 辅助函数 ==============
def clean(v):
    if v is None:
        return ''
    v = str(v)
    for sep in ['⁃', '‐', '‑', '–', '—', '―', '－']:
        v = v.replace(sep, '-')
    return re.sub(r'[\s\u3000\n]+', '', v).strip()

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

def clean_quota_code(v):
    if v is None:
        return None
    v = to_half_width(clean(v))
    for dash in ['⁃', '‑', '–', '—', '―', '‐', '－']:
        v = v.replace(dash, '-')
    m = re.match(r'^([A-Z]\d+)-(\d+)$', v)
    if m:
        return f"{m.group(1)}-{m.group(2)}"
    return None

def is_valid_text(val):
    """判断是否为有效的子项文本（不是空白/横线/纯金额/表头词）"""
    if not val or val in ['-', '－']:
        return False
    if val in ['消耗量', '消', '耗量', '单位', '单价', '名称']:
        return False
    if any(s in val for s in ['消耗量', '消', '耗量', '单位', '单价', '名称']):
        return False
    val_ascii = val.translate({i: chr(i - 0xFEE0) for i in range(0xFF00, 0xFFFF) if 0xFF00 <= i <= 0xFF5E})
    # 纯数字/金额（数字+符号，无字母）→ 过滤
    if re.match(r'^[\d．.，,+\-+/]+\$', val_ascii):
        return False
    # 包含字母（mm 等规格标记）→ 保留
    if re.search(r'[a-zA-Z]', val_ascii):
        return True
    # 包含规格符号（×、＞、＜等）→ 保留（如 450×450、＞600×600）
    if re.search(r'[×><＞＜]', val):
        return True
    # 其他情况：数字开头且无中文 → 过滤
    has_chinese = bool(re.search(r'[\u4e00-\u9fff]', val))
    if not has_chinese and re.match(r'^[\d０-９．.，,+\-+/]', val):
        return False
    return True

def strip_mm_from_end(val):
    """从项目名称末尾去除残留的 mm 厚度数值（如 20mm）"""
    if not val:
        return val
    val_ascii = to_half_width(val)
    # Strip trailing mm pattern from ascii version (e.g. 20mm)
    cleaned_ascii = re.sub(r'[\d]+m{2,}$', '', val_ascii, flags=re.IGNORECASE)
    if cleaned_ascii != val_ascii:
        # Also strip trailing fullwidth digits from the cleaned result
        return re.sub(r'[\d０-９]+$', '', cleaned_ascii).rstrip()
    return val

def extract_page_subitems(page):
    """提取页面中每列定额的子项规格
    返回: (quota_cols, project_names, specs)
      quota_cols: {col_idx: quota_code}
      project_names: {col_idx: project_name_from_row1}
      specs: {col_idx: enriched_spec_string}
    """
    tabs = page.find_tables()
    if not tabs.tables:
        return {}, {}, {}

    data = tabs.tables[0].extract()
    if len(data) < 3:
        return {}, {}, {}

    # 找定额编号行 (Row 0)
    quota_cols = {}
    for ci, cell in enumerate(data[0]):
        code = clean_quota_code(cell)
        if code:
            quota_cols[ci] = code

    if not quota_cols:
        return {}, {}, {}

    sorted_cols = sorted(quota_cols.keys())

    # Row 1: 项目名称
    project_names = {}
    if len(data) > 1:
        for ci in quota_cols:
            if ci < len(data[1]):
                pn = clean(data[1][ci])
                if pn:
                    project_names[ci] = pn

    # Row 2: 规格
    # Row 3+: 子项名称（可能有合并单元格向右扩展）
    specs = {}
    if len(data) > 2:
        for ci in quota_cols:
            parts = []

            # Row2：逐列独立提取，空值向后继承
            if ci < len(data[2]):
                raw = clean(data[2][ci])
                if is_valid_text(raw):
                    parts.append(raw)
                else:
                    # 向后搜索最近一列的非空 Row2（合并单元格）
                    ci_idx = sorted_cols.index(ci)
                    for prev_ci in reversed(sorted_cols[:ci_idx]):
                        if prev_ci < len(data[2]):
                            pv = clean(data[2][prev_ci])
                            if is_valid_text(pv):
                                parts.append(pv)
                                break

            # Row3+: 子项名称，合并单元格向右扩展
            for ri in range(3, len(data)):
                row_vals = {}
                for cj in sorted_cols:
                    if cj < len(data[ri]):
                        row_vals[cj] = clean(data[ri][cj])
                    else:
                        row_vals[cj] = ''

                own_val = row_vals.get(ci, '')
                ci_idx = sorted_cols.index(ci)

                if is_valid_text(own_val):
                    # 自身有值：直接添加（不再检查后续列）
                    parts.append(own_val)
                else:
                    # 向前找最近的非空文本（合并单元格向左继承）
                    merged_val = None
                    for prev_ci in reversed(sorted_cols[:ci_idx]):
                        pv = row_vals.get(prev_ci, '')
                        if is_valid_text(pv):
                            merged_val = pv
                            break
                    if merged_val:
                        parts.append(merged_val)

            if parts:
                specs[ci] = ' '.join(parts)

    return quota_cols, project_names, specs

def main():
    print("=" * 60)
    print("定额项目名称（含子项规格）提取")
    print("=" * 60)

    doc = fitz.open(PDF_PATH)
    project_names_map = {}

    for page_idx in range(len(doc)):
        page = doc[page_idx]
        quota_cols, project_names, specs = extract_page_subitems(page)

        last_project_name = ''
        for ci, code in sorted(quota_cols.items()):
            proj_name = project_names.get(ci, '')

            # 同行多列：继承前一个非空项目名称
            if not proj_name:
                proj_name = last_project_name
            else:
                last_project_name = proj_name

            # 从项目名末尾去除残留的 mm 厚度数值
            proj_name = strip_mm_from_end(proj_name)

            spec = specs.get(ci, '')

            # 格式：项目名称 - 规格
            if spec and proj_name:
                enriched_name = f"{proj_name} - {spec}"
            elif spec:
                enriched_name = spec
            else:
                enriched_name = proj_name

            if enriched_name:
                project_names_map[code] = enriched_name

    doc.close()
    print(f"提取到 {len(project_names_map)} 条项目名称")

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(project_names_map, f, ensure_ascii=False, indent=2)

    print(f"输出文件: {OUTPUT_FILE}")

    # 验证
    print("\n验证 A9-37/38/39:")
    for code in ['A9-37', 'A9-38', 'A9-39']:
        print(f"  {code}: {project_names_map.get(code, 'N/A')}")

    print("\n验证 A9-16/17:")
    for code in ['A9-16', 'A9-17']:
        print(f"  {code}: {project_names_map.get(code, 'N/A')}")

    print("\n前20条:")
    for code in list(project_names_map.keys())[:20]:
        print(f"  {code}: {project_names_map[code]}")

if __name__ == "__main__":
    main()
