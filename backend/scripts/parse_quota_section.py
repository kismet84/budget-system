#!/usr/bin/env python3
"""
定额分部/子部分项工程名称提取脚本
提取每个定额编号对应的：
  - 一级标题（章）
  - 二级标题（大节）
  - 三级标题（小节）
忽略前缀（章节号），只保留名称。
"""
import fitz
import re
import json
from pathlib import Path

# ============== 配置 ==============
PDF_PATH = "/Users/kis/.openclaw/memory/projects/budget-system/data/定额/raw/装饰/《湖北省房屋建筑与装饰工程消耗量定额及全费用基价表》（装饰·措施）（2024）.pdf"
PAGE_NUMBERS_FILE = Path("/Users/kis/.openclaw/memory/projects/budget-system/data/定额/page_numbers.json")
OUTPUT_FILE = Path("/Users/kis/.openclaw/memory/projects/budget-system/data/定额/section_names.json")

# ============== 辅助函数 ==============
def clean_spaces(text):
    if not text:
        return ''
    return re.sub(r'[\s\u3000]+', '', text)

def to_half_width_int(s):
    """全角数字字符串转int"""
    s_half = s.translate({0xFF10 + i: str(i) for i in range(10)})
    return int(s_half)

def extract_toc_entries(toc_text):
    """从TOC页面文本中提取所有条目
    结构：名称行 -> （页码）行 -> 点线行 -> 循环
    返回: [(level, name, page_number), ...]
    level: 1=章, 2=节, 3=小节, 4=子目
    """
    lines = toc_text.split('\n')
    entries = []

    i = 0
    while i < len(lines):
        line = lines[i].strip()
        i += 1

        if not line:
            continue

        # 跳过点线行
        if line.startswith('．') or line == '':
            # consume dots line
            continue

        # 跳过"说明" / "工程量计算规则"（单独成行）
        if line == '说明' or line == '工程量计算规则':
            # 消费后面的（页码）
            if i < len(lines) and re.match(r'（\d+）', lines[i].strip()):
                i += 1  # consume page num
            continue

        # 跳过只有页码的行（已在上一轮处理）
        if re.match(r'（\d+）', line):
            continue

        # 找到名称行，查找下一页码
        name = None
        level = None

        # 一级: 第X章　名称
        m = re.match(r'^第([一二三四五六七八九十百零\d]+)章(.*)$', line)
        if m:
            level = 1
            name = clean_spaces(m.group(2)) or m.group(1) + '章'

        # 二级: 一、二、三、...
        elif re.match(r'^[一二三四五六七八九十]+、', line):
            level = 2
            name = clean_spaces(re.sub(r'^[一二三四五六七八九十]+、', '', line))

        # 三级: １．、２．、３．...（全角阿拉伯数字）
        elif re.match(r'^[\d]+[．..]', line):
            level = 3
            name = clean_spaces(re.sub(r'^[\d]+[．..]', '', line))

        # 四级: （１）、（２）...
        elif re.match(r'^（[０１２３４５６７８９\d]+）', line):
            level = 4
            name = clean_spaces(re.sub(r'^（[０１２３４５６７８９\d]+）', '', line))

        if level is not None and name:
            # 查找后续行的页码
            page_num = None
            for j in range(i, min(i + 3, len(lines))):
                pm = re.search(r'（(\d+)）', lines[j])
                if pm:
                    page_num = int(pm.group(1))
                    i = j + 1  # consume page num line
                    break
            if page_num is not None:
                entries.append((level, name, page_num))

    return entries

def build_section_map(entries):
    """将TOC条目构建为列表，每个节点含(级别, 名称, 页码, 上级节点索引)
    返回: [(level, name, page, parent_l1_idx, parent_l2_idx), ...]
    """
    result = []  # (level, name, page, l1_idx, l2_idx)
    l1_idx = -1
    l2_idx = -1

    for level, name, page in entries:
        if level == 1:
            l1_idx = len(result)
            l2_idx = -1
        elif level == 2:
            l2_idx = len(result)
        elif level == 3:
            pass  # l2_idx stays as is

        result.append((level, name, page, l1_idx, l2_idx))

    return result

def get_quota_sections(section_map, quota_page):
    """根据定额所在目录页码，在section_map中查找对应的一二三级标题"""
    result = ['', '', '']  # [一级, 二级, 三级]

    # 从后往前找，找到第一个页码 <= quota_page 的条目
    for level, name, page, l1_idx, l2_idx in reversed(section_map):
        if page > quota_page:
            continue
        if level == 1:
            result[0] = name
            result[1] = ''
            result[2] = ''
        elif level == 2:
            if l1_idx >= 0:
                result[0] = section_map[l1_idx][1]
            result[1] = name
            result[2] = ''
        elif level == 3:
            if l1_idx >= 0:
                result[0] = section_map[l1_idx][1]
            if l2_idx >= 0:
                result[1] = section_map[l2_idx][1]
            result[2] = name
        break

    return result

def main():
    print("=" * 60)
    print("定额分部/子部分项工程名称提取")
    print("=" * 60)

    # 1. 读取页码映射
    with open(PAGE_NUMBERS_FILE, encoding='utf-8') as f:
        page_numbers = json.load(f)
    print(f"已加载 {len(page_numbers)} 条定额页码")

    # 2. 解析TOC
    doc = fitz.open(PDF_PATH)
    toc_text = ''
    for page_idx in range(8):  # TOC pages 0-7
        toc_text += doc[page_idx].get_text()
    doc.close()

    # 3. 提取TOC条目
    entries = extract_toc_entries(toc_text)
    print(f"TOC条目数: {len(entries)}")

    # 4. 构建扁平映射表
    section_map = build_section_map(entries)

    # 5. 为每个定额编号查找分部名称
    section_names_map = {}
    for quota_code, toc_page in page_numbers.items():
        sections = get_quota_sections(section_map, toc_page)
        section_names_map[quota_code] = {
            "一级": sections[0],
            "二级": sections[1],
            "三级": sections[2],
            "目录页码": toc_page
        }

    # 6. 保存
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(section_names_map, f, ensure_ascii=False, indent=2)

    print(f"输出文件: {OUTPUT_FILE}")

    # 7. 验证几个
    print("\n验证:")
    for code in ['A9-110', 'A9-112', 'A13-210', 'A12-32', 'A17-47']:
        if code in section_names_map:
            s = section_names_map[code]
            print(f"  {code}: {s['一级']} > {s['二级']} > {s['三级']} (页{s['目录页码']})")

    # 打印前20条
    print("\n前20条:")
    for code in list(section_names_map.keys())[:20]:
        s = section_names_map[code]
        print(f"  {code}: {s['一级']} > {s['二级']} > {s['三级']}")

if __name__ == "__main__":
    main()
