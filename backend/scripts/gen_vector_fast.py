#!/usr/bin/env python3
"""
使用 SiliconFlow API 生成定额向量 - 优化版
- 批量 API 调用（每批最多 50 条）
- 并发请求（控制并发数）
- 断点续传（重启不重复）
- 自动重试
"""
import urllib.request
import urllib.error
import json
import psycopg2
import time
import sys
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

# ========== 配置（从 config.py 统一读取）==========
_backend_root = Path(__file__).parent.parent
sys.path.insert(0, str(_backend_root))
from config import settings
from urllib.parse import urlparse

API_KEY=settings.SILICONFLOW_API_KEY  # 从 .env 读取，禁止硬编码

# 解析 DATABASE_URL 构建 psycopg2 连接参数
_db_url = settings.DATABASE_URL
parsed = urlparse(_db_url)
DB = {
    "host": parsed.hostname or "localhost",
    "port": parsed.port or 5432,
    "database": parsed.path.lstrip("/") or "budget_system",
    "user": parsed.username or "kis",
    "password": parsed.password or "",
}

BATCH_SIZE = 20       # 每批文本数（SiliconFlow 限制在 30 以内）
MAX_WORKERS = 3       # 并发线程数
MAX_RETRIES = 3       # 最大重试次数
REQUEST_TIMEOUT = 60  # API 超时（秒）
SAVE_INTERVAL = 200   # 每处理 N 条提交一次数据库

def embed_batch(texts):
    """批量调用 SiliconFlow 文本嵌入 API"""
    url = 'https://api.siliconflow.cn/v1/embeddings'
    payload = {'model': 'BAAI/bge-large-zh-v1.5', 'input': texts}
    
    for attempt in range(MAX_RETRIES):
        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode('utf-8'),
                headers={
                    'Authorization': f'Bearer {API_KEY}',
                    'Content-Type': 'application/json'
                },
                method='POST'
            )
            with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as r:
                result = json.loads(r.read())
                embeddings = result['data']
                # 按 index 排序（API 不保证顺序）
                embeddings.sort(key=lambda x: x['index'])
                return [e['embedding'] for e in embeddings]
        except Exception as e:
            if attempt < MAX_RETRIES - 1:
                wait = 2 ** attempt
                print(f'  [重试 {attempt+1}/{MAX_RETRIES}] {e}, {wait}s后重试', flush=True)
                time.sleep(wait)
            else:
                raise

def main():
    print('=' * 50, flush=True)
    print('向量生成优化版启动', flush=True)
    print(f'批量大小: {BATCH_SIZE}, 并发: {MAX_WORKERS}', flush=True)
    print('=' * 50, flush=True)
    
    conn = psycopg2.connect(**DB)
    conn.set_session(autocommit=False)  # 手动控制事务
    cur = conn.cursor()

    # 确保 pgvector 扩展已启用
    cur.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # 确保 embedding 列存在（首次运行迁移）
    cur.execute("""
        ALTER TABLE quotas ADD COLUMN IF NOT EXISTS embedding vector(1024)
    """)

    # 统计
    cur.execute('SELECT COUNT(*) FROM quotas WHERE embedding IS NULL')
    remaining = cur.fetchone()[0]
    cur.execute('SELECT COUNT(*) FROM quotas WHERE embedding IS NOT NULL')
    done = cur.fetchone()[0]
    total = done + remaining
    
    print(f'总计: {total}, 已完成: {done}, 剩余: {remaining}', flush=True)
    
    if remaining == 0:
        print('全部完成！', flush=True)
        return
    
    # 每次取一批
    batch_num = 0
    success_count = done
    start_time = time.time()
    
    while True:
        # 获取一批未处理的记录，构建丰富的文本用于向量化
        # 文本来源：定额编号 + 分类 + 分部/项目名称 + 计量单位 + 材料明细
        cur.execute('''
            SELECT q.id, q.quota_id,
                   CONCAT_WS('，',
                     q.quota_id,
                     q.category,
                     q.section,
                     '计量单位：' || q.unit,
                     COALESCE((
                         SELECT string_agg(name, '、' ORDER BY name)
                         FROM materials WHERE quota_id = q.quota_id
                     ), '')
                   ) AS embed_text
            FROM quotas q
            WHERE q.embedding IS NULL
            ORDER BY q.id
            LIMIT %s
        ''', (BATCH_SIZE,))
        rows = cur.fetchall()
        if not rows:
            break
        
        batch_num += 1
        ids = [r[0] for r in rows]
        qids = [r[1] for r in rows]
        texts = [r[2][:2000] for r in rows]  # 截断到 2000 字符
        
        # 分割为子批次（每子批次最多 BATCH_SIZE）
        sub_batches = []
        for i in range(0, len(texts), BATCH_SIZE):
            sub_batches.append((
                ids[i:i+BATCH_SIZE],
                qids[i:i+BATCH_SIZE],
                texts[i:i+BATCH_SIZE]
            ))
        
        try:
            for sub_ids, sub_qids, sub_texts in sub_batches:
                if not sub_texts:
                    continue
                embeddings = embed_batch(sub_texts)
                
                # 更新数据库
                for qid, emb in zip(sub_qids, embeddings):
                    cur.execute(
                        'UPDATE quotas SET embedding=%s::vector WHERE quota_id=%s',
                        (str(emb), qid)
                    )
                
                conn.commit()
                success_count += len(sub_texts)
                elapsed = time.time() - start_time
                rate = success_count / elapsed if elapsed > 0 else 0
                remaining_now = total - success_count
                eta = remaining_now / rate / 60 if rate > 0 else 0
                
                print(f'[{batch_num}] +{len(sub_texts)} 累计:{success_count}/{total} '
                      f'速度:{rate:.1f}/s 剩余:{eta:.1f}min', flush=True)
                
        except Exception as e:
            print(f'批次 {batch_num} 失败: {e}', flush=True)
            conn.rollback()
            time.sleep(5)
    
    conn.close()
    elapsed = time.time() - start_time
    print(f'完成！共 {success_count} 条，耗时 {elapsed/60:.1f} 分钟', flush=True)

if __name__ == '__main__':
    main()
