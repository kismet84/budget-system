# Scripts 审查报告

> 审查日期：2026-04-13
> 审查范围：`backend/scripts/` 全部脚本（共 18 个）

---

## 一、整体架构

这些脚本构成一套完整的 **PDF → JSON → PostgreSQL → 向量索引** 数据管道，分为四个阶段：

```
Stage 1: PDF 解析
  ├── parse_quota_cost.py          费用数据（全费用/人工/材料/机械/管理/增值税）
  ├── parse_quota_materials.py     材料明细 + 机械台班
  ├── parse_quota_section.py       分部/子部/分项三级路径
  ├── parse_quota_subitems.py      项目名称（含子项规格）
  ├── parse_quota_page_numbers.py  定额编号 → PDF 页码映射
  ├── extract_work_content.py      工作内容
  ├── extract_quota_unit.py        计量单位（废弃版）
  ├── extract_all_units.py         计量单位（废弃版）
  ├── extract_units.py             计量单位（标准版）
  ├── extract_units_post.py        计量单位后处理（项目名称推断）
  ├── extract_quota_see_table.py  计量单位（废弃）
  └── extract_see_table_pages.py   计量单位（废弃）

Stage 2: 数据合并
  └── merge_quota_data.py         6 个 JSON → 装饰_合并定额.json

Stage 3: 数据库导入
  ├── import_quota_db.py          主导入脚本（quotas + materials）
  └── backfill_cost_fields.py     补充费用字段（增量）

Stage 4: 向量生成
  ├── gen_vector_fast.py          SiliconFlow 批量向量化（生产级）
  └── regen_vectors.py            向量生成（废弃版）

独立流程：
  └── parse_info_price.py         信息价 Excel 解析（xlsx → JSON）
```

---

## 二、文件分级

> ⚠️ **2026-04-14 更新**：已删除 6 个废弃脚本；4 个 `.openclaw` 路径已迁移至 `.hermes/memory/projects/budget-system/`。

|| 状态 | 脚本 | 说明 |
||------|------|------|
|| ✅ 生产可用 | `import_quota_db.py` | 主导入，使用相对路径，逻辑完整 |
|| ✅ 生产可用 | `merge_quota_data.py` | 数据合并，使用相对路径 |
|| ✅ 生产可用 | `gen_vector_fast.py` | 批量并发断点续传，生产级质量 |
|| ✅ 生产可用 | `extract_units.py` | 计量单位最终版，注释完整 |
|| ✅ 生产可用 | `extract_units_post.py` | 从项目名称推断"见袁"定额单位 |
|| ✅ 可用 | `parse_quota_cost.py` | 费用解析，路径使用 `Path(...).parent` 相对定位 |
|| ✅ 可用 | `parse_quota_materials.py` | 材料解析，路径使用 `Path(...).parent` 相对定位 |
|| ✅ 可用 | `parse_quota_page_numbers.py` | 页码提取，已修复路径 |
|| ✅ 可用 | `parse_quota_section.py` | 分部路径，已修复路径 |
|| ✅ 可用 | `parse_quota_subitems.py` | 子项规格，已修复路径 |
|| ✅ 可用 | `parse_info_price.py` | 信息价解析，已修复路径（`date/` → `data/信息价/`） |
|| ✅ 可用 | `extract_work_content.py` | 工作内容提取，路径使用 `Path(...).parent` 相对定位 |
|| ⚠️ 可用但低效 | `backfill_cost_fields.py` | 功能正确，但 1859 条 × 3718 次 DB 往返 |

---

## 三、路径问题详情

### 3.1 ✅ 已修复

2026-04-14 完成迁移：`.openclaw` → `.hermes/memory/projects/budget-system/`

| 脚本 | 原路径段 | 新路径段 |
|------|---------|---------|
| `parse_quota_section.py` | `.openclaw/.../data/定额/` | `.hermes/memory/projects/budget-system/data/定额/` |
| `parse_quota_subitems.py` | `.openclaw/.../data/定额/` | `.hermes/memory/projects/budget-system/data/定额/` |
| `parse_info_price.py` | `.openclaw/.../date/` | `.hermes/memory/projects/budget-system/data/信息价/raw/` |
| `parse_info_price.py` | `.openclaw/.../date_parsed/` | `.hermes/memory/projects/budget-system/data/信息价/indexed/` |
| `parse_quota_page_numbers.py` | `.openclaw/.../data/定额/` | `.hermes/memory/projects/budget-system/data/定额/` |

### 3.2 计量单位脚本版本说明

现有 2 个计量单位脚本：
- `extract_units.py` — 主力，从 PDF 提取所有计量单位
- `extract_units_post.py` — 后处理，从项目名称推断"见袁"条目单位

废弃已删除：`extract_quota_unit.py`、`extract_all_units.py`、`extract_quota_see_table.py`、`extract_see_table_pages.py`、`extract_unit_from_project_name.py`

---

## 四、效率问题

### 4.1 `backfill_cost_fields.py` — 3718 次 DB 往返

```python
for quota_id, cost_data in costs.items():
    # 每次循环 2 次 DB 调用
    cur.execute(f"SELECT {field} FROM quotas WHERE quota_id = %s", ...)
    cur.execute(f"UPDATE quotas SET ...")
```

1859 条 × 2 次 = **3718 次数据库往返**。

**优化方案**：一次批量查询 + 一次批量更新

```python
# 批量查询所有 quota_id 的当前值
all_ids = list(costs.keys())
cur.execute("SELECT quota_id, labor_fee, material_fee, ... FROM quotas WHERE quota_id = ANY(%s)", (all_ids,))
existing = {row[0]: row[1:] for row in cur.fetchall()}

# 内存中计算差异，批量更新
for quota_id, cost_data in costs.items():
    updates = {}
    for field, json_key in field_map.items():
        if existing.get(quota_id, [None]*n)[field_idx] is None:  # 已是 NULL
            val = cost_data.get(json_key)
            if val is not None:
                updates[field] = float(val)
    if updates:
        # 批量 UPDATE（多条）
```

### 4.2 `regen_vectors.py` — 逐条调用，无并发

`gen_vector_fast.py` 使用批量 API + 3 并发 + 断点续传，性能约 `regen_vectors.py` 的 10 倍以上。

---

## 五、依赖分析

### 5.1 PDF 解析脚本共同依赖

| 依赖 | 提供者 | 使用脚本 |
|------|--------|---------|
| `fitz` (PyMuPDF) | `pip install pymupdf` | `parse_quota_cost.py`, `parse_quota_materials.py`, `parse_quota_section.py`, `parse_quota_subitems.py`, `parse_quota_page_numbers.py`, `extract_work_content.py`, `extract_quota_unit.py`, `extract_all_units.py`, `extract_units.py`, `extract_units_post.py`, `extract_quota_see_table.py`, `extract_see_table_pages.py` |

未在 `requirements.txt` 中声明。

### 5.2 数据库连接方式不统一

| 脚本 | 连接方式 |
|------|---------|
| `import_quota_db.py` | `psycopg2` + 自定义 Unix socket 检测 |
| `backfill_cost_fields.py` | `psycopg2` 硬编码 `localhost:5432` |
| `extract_units_post.py` | `psycopg2` 硬编码 `127.0.0.1:5432` |
| `regen_vectors.py` | `psycopg2` 硬编码 `host='/tmp'` |
| `gen_vector_fast.py` | `psycopg2` + `urlparse` 解析 `DATABASE_URL` |

建议统一通过 `from config import settings; psycopg2.connect(settings.DATABASE_URL)` 获取连接。

### 5.3 硬编码数据库配置

```python
# backfill_cost_fields.py
def get_connection():
    return psycopg2.connect(host="localhost", port=5432, dbname="budget_system", user="kis")

# extract_units_post.py
DB_CONFIG = dict(host='127.0.0.1', port=5432, database='budget_system', user='kis')

# regen_vectors.py
DB = dict(host='/tmp', port=5432, database='budget_system', user='kis')
```

三个脚本三个不同的连接方式，但数据库地址完全相同。`import_quota_db.py` 和 `gen_vector_fast.py` 正确使用了 `from config import settings`。

---

## 六、废弃脚本与删除清单

### 6.1 ✅ 已处理（2026-04-14）

**已删除（6 个废弃脚本）**：
- `regen_vectors.py` — 被 `gen_vector_fast.py` 替代
- `extract_quota_unit.py` — 被 `extract_units.py` 替代
- `extract_all_units.py` — 被 `extract_units.py` 替代
- `extract_quota_see_table.py` — 被 `extract_units.py` 替代
- `extract_see_table_pages.py` — 被 `extract_units.py` 替代
- `extract_unit_from_project_name.py` — 被 `extract_units_post.py` 替代

**路径已修复（4 个脚本）**：`.openclaw` → `.hermes/memory/projects/budget-system/`
- `parse_quota_section.py`
- `parse_quota_subitems.py`
- `parse_info_price.py`（`date/` → `data/信息价/`，`date_parsed/` → `data/信息价/indexed/`）
- `parse_quota_page_numbers.py`

---

## 七、保留脚本说明

### `import_quota_db.py` ✅

- 使用 `from config import settings` 统一配置
- `ON CONFLICT (quota_id) DO NOTHING` 支持增量导入
- 同时写入 `quotas` 和 `materials` 两张表
- 事务控制正确（`rowcount == 0` 时跳过，避免空事务）

**注意**：`get_connection()` 中的 Unix socket 检测在某些 Postgres 实现上可能失效（参见 REVIEW.md 主报告）。

### `merge_quota_data.py` ✅

- 合并 6 个 JSON 文件为统一记录
- `计量单位.json` 优先级最高（已提取 quantity + unit）
- 正确处理缺失字段（`missing_project` / `missing_section` 统计）
- 分部统计摘要输出

**问题**：`计量单位.json` 的路径是 `DATA_DIR / "计量单位.json"`，`DATA_DIR = SCRIPT_DIR.parent.parent / "data" / "定额" / "parsed" / "装饰"`，与 `extract_units.py` 的输出路径一致，**衔接正确**。

### `gen_vector_fast.py` ✅

- 批量 API（每批 20 条，SiliconFlow 限制 30 以内）
- 3 并发线程
- 断点续传（重启不重复，已完成的不重跑）
- 自动重试（指数退避）
- 每 200 条提交一次 DB，减少事务数

**推荐作为生产向量生成工具**。`regen_vectors.py` 删除后无歧义。

### `extract_units.py` + `extract_units_post.py` ✅

`extract_units.py`：
- 两种页面类型（明确计量单位 / 见袁）统一处理
- `见袁` 页通过 x 位置最近邻匹配提取
- 注释完整，工具函数（`to_half_width` / `fw` / `normalize_unit` / `extract_quantity`）可复用

`extract_units_post.py`：
- 处理数据库中 `quantity IS NULL` 的条目
- 从 `project_names.json` 项目名称推断计量单位
- 交互模式（`input()`）用于人工确认，但支持 `y` 全自动模式

### `backfill_cost_fields.py` ⚠️

功能正确，但效率问题（见 4.1）。若数据量不大（1859 条），当前实现可接受；若未来扩展到万级，需要优化。

---

## 八、管理脚本（已完成 ✅）

| 脚本 | 用途 | 状态 | 提交 |
|------|------|------|------|
| `backend/routers/quota_import.py` | 管理员上传 Excel 定额文件，写入 quotas 表 | ✅ 已完成 | `8a016d7` |
| `backend/routers/price_import.py` | 信息价 Excel → material_prices 表 | ✅ 已完成 | `80625fa` |
| `backend/routers/data_report.py` | 数据质量报告（覆盖率/缺失率/分部统计）| ✅ 已完成 | `e6a5eb0` |

### 前端页面

| 页面 | 路由 |
|------|------|
| `AdminQuotaPage.tsx` | `/admin/quota` |
| `AdminPricePage.tsx` | `/admin/price` |
| `DataReportPage.tsx` | `/admin/report` |

### API 端点

| 端点 | 说明 |
|------|------|
| `POST /api/v1/admin/quota/import` | 上传 Excel 定额，幂等更新 |
| `GET /api/v1/admin/quota/report` | 定额导入报告 + 统计 |
| `POST /api/v1/admin/price/import` | 上传 Excel 信息价 |
| `GET /api/v1/admin/price/report` | 信息价导入历史 |
| `GET /api/v1/admin/report` | 数据质量总报告 |

---

## 九、Script 执行顺序建议

**首次数据导入（从 PDF）**：
```
1. parse_quota_cost.py              费用数据
2. parse_quota_materials.py         材料 + 机械
3. parse_quota_page_numbers.py      页码（其他脚本依赖此文件路径）
4. parse_quota_section.py           分部路径
5. extract_work_content.py          工作内容
6. extract_units.py                 计量单位（第一阶段）
7. extract_units_post.py             计量单位（后处理，补充"见袁"条目）
8. merge_quota_data.py             合并为装饰_合并定额.json
9. import_quota_db.py              导入 PostgreSQL
10. backfill_cost_fields.py         补充费用字段（如有遗漏）
11. gen_vector_fast.py              生成向量索引
```

**增量更新（新版定额发布后）**：
```
1. 新版 PDF 解析（重复 1-6 步）→ 输出新版 JSON
2. import_quota_db.py --conflict=update  （需改造，支持 ON CONFLICT UPDATE）
```

---

## 十、清理命令

```bash
# ✅ 已完成（2026-04-14）
# 废弃脚本已删除：
rm backend/scripts/regen_vectors.py
rm backend/scripts/extract_quota_unit.py
rm backend/scripts/extract_all_units.py
rm backend/scripts/extract_quota_see_table.py
rm backend/scripts/extract_see_table_pages.py
rm backend/scripts/extract_unit_from_project_name.py

# 路径已修复为 .hermes/memory/projects/budget-system/
# 验证无残留 .openclaw：
grep -r '\.openclaw' backend/scripts/*.py && echo "还有残留" || echo "已全部清除"
```

---

## 十一、PM2 启动配置（2026-04-14 更新）

`ecosystem.config.js`（当前生效配置）：

```javascript
module.exports = {
  apps: [
    {
      name: 'budget-api',
      script: '/usr/local/bin/python3.11',
      args: '-m uvicorn main:app --host 0.0.0.0 --port 8001 --reload',
      cwd: '/Users/kis/.hermes/memory/projects/budget-system/backend',
      watch: ['.'],
      ignore_watch: ['venv/', '__pycache__/', '*.pyc', '.git/'],
      env: { PYTHONPATH: '...' },
    },
    {
      name: 'budget-frontend',
      script: 'node_modules/.bin/vite',
      args: '--port 5173 --mode production',
      cwd: '/Users/kis/.hermes/memory/projects/budget-system/frontend',
    },
  ]
};
```

| 进程 | 端口 | 热重载 |
|------|------|--------|
| `budget-api` | 8001 | ✅ `watching: enabled` |
| `budget-frontend` | 5173 | ❌ |

**重启命令**：`pm2 restart budget-api`（几秒内自动重载新代码）

**⚠️ 注意**：Vite dev server（5173）在 PM2 下为 production 构建，`npm run build` 后需手动 `pm2 restart budget-frontend` 刷新。
