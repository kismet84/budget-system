#!/usr/bin/env python3
"""
定额PDF页码提取脚本
提取每个页面页脚的页码，并与该页所有定额编号关联
输出: quota_code -> pdf_page_number 映射
"""
import fitz
import re
import json
import os
from pathlib import Path

# ============== 配置 ==============
PDF_PATH = "/Users/kis/.hermes/memory/projects/budget-system/data/定额/raw/装饰/《湖北省房屋建筑与装饰工程消耗量定额及全费用基价表》（装饰·措施）（2024）.pdf"
OUTPUT_FILE = Path("/Users/kis/.hermes/memory/projects/budget-system/data/定额/page_numbers.json")

# ============== 辅助函数 ==============
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

def clean_quota_code(v):
    """清理定额编号"""
    if v is None:
        return None
    v = to_half_width(str(v).strip())
    for dash in ['⁃', '‑', '–', '—', '―', '‐', '－']:
        v = v.replace(dash, '-')
    m = re.match(r'^([A-Z]\d+)-(\d+)$', v)
    if m:
        return f"{m.group(1)}-{m.group(2)}"
    return None

def extract_page_number_from_footer(bottom_text):
    """从页脚文本中提取页码
    
    PDF页脚为垂直排版，数字从上往下书写，但应从下往上读。
    例如 '\n１\n４\n' -> 提取 '１４' -> 反转得 '４１' -> 页码 41。
    """
    blocks = re.findall(r'·([\d\n]+)·', bottom_text)
    if not blocks:
        return None
    # 取最后一个块（页码在最底部）
    digits = blocks[-1].replace('\n', '')
    if digits:
        digits_half = to_half_width(digits)
        # 垂直排版：数字从下往上读
        return int(digits_half[::-1])
    return None

def extract_quota_codes_from_page(page):
    """从页面提取所有定额编号"""
    tabs = page.find_tables()
    if not tabs.tables:
        return []
    
    table = tabs.tables[0]
    data = table.extract()
    
    if len(data) < 5:
        return []
    
    codes = set()
    for row in data[:10]:  # 只在前10行查找（定额编号区）
        for cell in row:
            if cell:
                code = clean_quota_code(cell)
                if code:
                    codes.add(code)
    return list(codes)

def main():
    print("=" * 60)
    print("定额PDF页码提取")
    print("=" * 60)
    
    doc = fitz.open(PDF_PATH)
    total_pages = len(doc)
    print(f"PDF总页数: {total_pages}")
    print()
    
    # 结果: pdf_page_idx (0-based) -> {page_number, quota_codes}
    page_map = {}  # quota_code -> page_number
    
    for page_idx in range(total_pages):
        page = doc[page_idx]
        h = page.rect.height
        w = page.rect.width
        
        # 提取页脚 (底部60pt)
        clip = fitz.Rect(0, h - 80, w, h)
        bottom_text = page.get_text("text", clip=clip)
        
        page_num = extract_page_number_from_footer(bottom_text)
        
        # 提取定额编号
        quota_codes = extract_quota_codes_from_page(page)
        
        if quota_codes:
            for code in quota_codes:
                page_map[code] = page_num
            
            print(f"  PDF页 {page_idx} -> 目录页 {page_num}: {len(quota_codes)} 个定额 {quota_codes[:3]}{'...' if len(quota_codes)>3 else ''}")
    
    doc.close()
    
    # 按定额编号排序输出
    sorted_codes = sorted(page_map.keys(), key=lambda x: (x.split('-')[0], int(x.split('-')[1]) if '-' in x else 0))
    
    # 保存
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(page_map, f, ensure_ascii=False, indent=2)
    
    print(f"\n共提取 {len(page_map)} 个定额编号的页码")
    print(f"输出文件: {OUTPUT_FILE}")
    
    # 打印前20条
    print("\n前20条:")
    for code in sorted_codes[:20]:
        print(f"  {code}: 页码 {page_map[code]}")

if __name__ == "__main__":
    main()
