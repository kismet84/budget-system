#!/usr/bin/env python3
"""
提取 PDF 页面中的"工作内容"字段
从原始 PDF 扫描"工作内容：xxx。计量单位"段落，关联到对应定额编号
"""
import fitz
import re
import json
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent.resolve()
PDF_PATH = SCRIPT_DIR.parent.parent / "data" / "定额" / "raw" / "装饰" / "《湖北省房屋建筑与装饰工程消耗量定额及全费用基价表》（装饰·措施）（2024）.pdf"
OUTPUT_FILE = SCRIPT_DIR.parent.parent / "data" / "定额" / "parsed" / "装饰" / "work_contents.json"


def normalize_text(text: str) -> str:
    """将 PDF 中的全角字符转为半角"""
    text = text.replace('⁃', '-')  # 上标减号
    # 全角拉丁字母 → 半角
    text = text.translate(str.maketrans(
        'ＡＢＣＤＥＦＧＨＩＪＫＬＭＮＯＰＱＲＳＴＵＶＷＸＹＺａｂｃｄｅｆｇｈｉｊｋｌｍｎｏｐｑｒｓｔｕｖｗｘｙｚ',
        'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
    ))
    # 全角数字 → 半角
    text = text.translate(str.maketrans('０１２３４５６７８９', '0123456789'))
    return text


def extract_work_contents() -> dict:
    """扫描 PDF，提取所有定额的工作内容"""
    doc = fitz.open(PDF_PATH)
    work_contents = {}
    current_work = None

    for page_num in range(doc.page_count):
        page = doc[page_num]
        text = page.get_text()
        norm = normalize_text(text)

        # 提取"工作内容"段落（到"计量单位"为止）
        work_match = re.search(r'工作内容[：:]\s*(.+?)(?=计量单位)', norm, re.DOTALL)
        if work_match:
            work = re.sub(r'\s+', ' ', work_match.group(1).strip())
            current_work = work

        # 查找定额编号（如 A10-1, A9-12）
        quota_matches = re.findall(r'[A-Z]\d+-\d+', norm)
        if quota_matches and current_work:
            for qid in quota_matches:
                if qid not in work_contents:
                    work_contents[qid] = current_work
            # 工作内容只对当前页的定额生效
            current_work = None

    doc.close()
    return work_contents


if __name__ == "__main__":
    print(f"读取 PDF: {PDF_PATH}")
    work_contents = extract_work_contents()
    print(f"提取到 {len(work_contents)} 条工作内容")

    # 保存 JSON
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(work_contents, f, ensure_ascii=False, indent=2)
    print(f"已保存到: {OUTPUT_FILE}")

    # 示例
    for qid in ['A10-1', 'A9-12', 'A10-51']:
        print(f"  {qid}: {work_contents.get(qid, 'NOT FOUND')[:60]}...")
