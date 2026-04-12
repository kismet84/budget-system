#!/usr/bin/env python3
"""
重新生成定额库的 embedding 向量
使用增强文本: {project_name} | {work_content} | {计量单位} | {section} | {category}

Usage:
    cd backend
    python3 scripts/regen_vectors.py
"""
import sys
import os
import time
import signal

# 确保 backend 目录在 sys.path 中，以便 import config
_script_dir = os.path.dirname(os.path.abspath(__file__))
_backend_dir = os.path.dirname(_script_dir)
sys.path.insert(0, _backend_dir)

import psycopg2
import requests
from config import settings

API_URL = "https://api.siliconflow.cn/v1/embeddings"
MODEL = settings.SILICONFLOW_EMBEDDING_MODEL
API_KEY = settings.SILICONFLOW_API_KEY

DB = dict(host='/tmp', port=5432, database='budget_system', user='kis')

# 优雅退出标志
_shutdown = False

def _signal_handler(sig, frame):
    global _shutdown
    print("\n收到中断信号，正在保存进度...")
    _shutdown = True

signal.signal(signal.SIGINT, _signal_handler)
signal.signal(signal.SIGTERM, _signal_handler)


def get_embedding(text, retry=3):
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    payload = {"model": MODEL, "input": text}
    for attempt in range(retry):
        try:
            r = requests.post(API_URL, headers=headers, json=payload, timeout=30)
            if r.status_code == 200:
                return r.json()["data"][0]["embedding"]
            elif r.status_code == 429:
                time.sleep(5)
            else:
                print(f"API error {r.status_code}: {r.text[:200]}")
                return None
        except Exception as e:
            print(f"Request error: {e}")
            time.sleep(2)
    return None


def build_text(row):
    parts = []
    for val in [row.get('project_name'), row.get('work_content'),
                row.get('unit'), row.get('section'), row.get('category')]:
        if val and str(val).strip():
            parts.append(str(val).strip())
    return ' | '.join(parts)


def main():
    if not API_KEY:
        print("ERROR: SILICONFLOW_API_KEY not configured")
        return

    conn = psycopg2.connect(**DB)
    cur = conn.cursor()

    cur.execute("""
        SELECT quota_id, project_name, work_content, unit, section, category
        FROM quotas
        WHERE project_name IS NOT NULL AND project_name != ''
    """)
    rows = cur.fetchall()
    total = len(rows)
    print(f"待处理: {total} 条定额")

    updated = 0
    failed = 0

    for i, row in enumerate(rows):
        if _shutdown:
            print(f"\n中断退出，已处理到第 {i}/{total} 条")
            break
        quota_id, project_name, work_content, unit, section, category = row
        text = build_text({
            'project_name': project_name,
            'work_content': work_content,
            'unit': unit,
            'section': section,
            'category': category
        })

        emb = get_embedding(text)
        if emb:
            cur.execute(
                "UPDATE quotas SET embedding = %s WHERE quota_id = %s",
                (emb, quota_id)
            )
            conn.commit()
            updated += 1
        else:
            failed += 1

        if (i + 1) % 20 == 0:
            print(f"进度: {i+1}/{total} (成功:{updated} 失败:{failed})")

        time.sleep(0.15)

    print(f"完成! 成功:{updated} 失败:{failed}")
    conn.close()


if __name__ == "__main__":
    main()
