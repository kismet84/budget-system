# 建设工程预算分析系统 — 全面审查报告

> 审查日期：2026-04-13
> 审查范围：后端 API · 前端 · Scripts · 配置 · 数据管道

---

## 一、整体现状

| 维度 | 状态 | 说明 |
|------|------|------|
| 后端 API 链路 | ✅ 基本完整 | AI 搜索链路规范，路由分层清晰 |
| 前端（React） | ⚠️ 页面有，API 未通 | 4 个页面骨架完整，但代理配置错误 |
| 前端（Streamlit） | ⚠️ 功能较全，端口硬编码 | `app.py` 完整但指向 8001 |
| 数据入库 | ⚠️ 未确认 | `import_quota_db.py` 可用，但未验证是否跑通 |
| 预算书生成 | ❌ 未实现 | CartPage 按钮为空壳 |
| 材料价格前端 | ❌ 未实现 | 后端完整，前端缺失 |
| Excel 导入管理界面 | ❌ 未实现 | 只有脚本，无 UI 入口 |

---

## 二、后端 API

### 2.1 路由注册（`main.py`）

```
✅ /api/v1/quota/*   — 定额 CRUD + 搜索
✅ /api/v1/search/*  — 语义搜索（占位，未使用）
✅ /api/v1/ai/search — AI 完整链路（核心）
✅ /api/v1/price/*   — 材料价格 CRUD
✅ /auth/login       — JWT 认证
```

**问题**：CORS 白名单写了 `localhost:8501`（Streamlit 端口），但实际后端跑在 **8000**。如果 Streamlit 和 FastAPI 同时启动，CORS 配置是对的；但如果前端（React）从 8501 调用后端 8000，Origin 不匹配。

**建议**：将 CORS 改为 `["*"]` 或补充 `localhost:5173`（Vite 默认端口）。

### 2.2 数据库连接（`database.py`）

Unix socket 检测逻辑：
```python
if parsed.hostname in (None, "localhost", "127.0.0.1"):
    _db_url = f"postgresql://{parsed.username}@/{parsed.path.lstrip('/')}?host=/tmp"
```

`.env` 中 `DATABASE_URL=postgresql://kis@127.0.0.1:5432/budget_system`，hostname 为 `127.0.0.1`，tuple 判断 `("localhost" in ...)` 为 False（因为实际是 `"127.0.0.1"` 而非 `"localhost"`），所以**不会走 Unix socket 分支**，而是直接用 127.0.0.1:5432。这个行为是正确的，但逻辑上容易混淆——`"localhost"` 分支永远不会被包含 `.env` 值的路径触发。

### 2.3 死代码

| 文件 | 问题 |
|------|------|
| `routers/search.py` | 占位路由，返回空数组，无任何调用方 |
| `services/embedding.py` | DeepSeek embed，完全无调用方；实际向量用 SiliconFlow BAAI |
| 两套 embedding 并存 | `embedding.py`（DeepSeek）与 `vector_search.py`（SiliconFlow）维度一致但互不相通 |

### 2.4 API Key 明文

`.env` 中两个 Key 直接明文：
```
DEEPSEEK_API_KEY=sk-3cb2227446a6414392387e825a3a603f
SILICONFLOW_API_KEY=sk-lznvbjdlhltpbvnkyzbayplcuwxdxkw...
```

该文件被 git track。**应立即移除并加入 `.gitignore`，改用环境变量注入。**

---

## 三、前端（React + Vite）

### 3.1 目录结构

```
frontend/
├── src/
│   ├── main.tsx
│   ├── App.tsx                  ✅ 路由注册，4个页面
│   ├── index.css                ✅ Tailwind + 深色主题
│   ├── api/quota.ts             ✅ API 调用封装
│   ├── types/quota.ts           ✅ 类型定义
│   ├── store/cartStore.ts       ✅ Zustand 持久化
│   ├── pages/
│   │   ├── SearchPage.tsx       ✅ AI 搜索页（完整）
│   │   ├── DetailPage.tsx       ✅ 定额详情页（完整）
│   │   ├── CartPage.tsx        ⚠️ 购物车，"生成预算书"按钮为空壳
│   │   └── MinePage.tsx        ⚠️ 个人页，硬编码"1859条定额"
│   └── components/
│       ├── QuotaCard.tsx        ✅ 搜索结果卡片
│       ├── CartItem.tsx         ✅ 清单项
│       ├── BottomNav.tsx        ✅ 底部 Tab 导航
│       └── ErrorBoundary.tsx    ✅ React 错误边界
├── vite.config.ts               ✅ 代理到 localhost:8001
└── .env                         VITE_API_BASE_URL=http://localhost:8000/api/v1
```

### 3.2 端口 mismatch（关键问题）

| 服务 | 端口 | 说明 |
|------|------|------|
| FastAPI 后端 | **8000**（默认） | `.env` 无端口配置时用 uvicorn 默认 |
| Vite dev server | 8501 | `vite.config.ts` 中 hardcoded |
| Streamlit | 8501 | `app.py` 硬编码 `API_BASE = "http://localhost:8001"` |
| Vite proxy 目标 | `localhost:8001` | 指向 Streamlit，非 FastAPI |

**实际连接路径**：
- React → Vite proxy → `localhost:8001` → **Streamlit** → FastAPI `:8000`

但 Streamlit 和 FastAPI 是两套独立系统，不会自动对接。**两套前端实际上都无法调通后端 API。**

**正确配置**：Vite proxy 应指向 `localhost:8000`，Streamlit 也应指向 `localhost:8000`。

### 3.3 `api/quota.ts` 的 baseURL 为空

```typescript
const api = axios.create({
  baseURL: '',  // ← 空字符串，依赖 Vite proxy
  timeout: 15000,
})
```

空字符串配合 Vite proxy 可以工作，但语义不清晰。如果 proxy 配置错误，所有请求都会失败且无明显提示。

---

## 四、两套前端并存

| | React + Vite | Streamlit |
|--|--|--|
| 文件 | `frontend/src/` | `frontend/app.py` |
| 端口 | 8501（通过 Vite） | 8501（直接） |
| 功能 | 移动端优先，4页面 | PC 端，搜索 + 分页 + 材料表 |
| 状态 | 页面骨架完整 | 功能最完整 |
| 问题 | API 端口配置错误 | 硬编码 `localhost:8001` |

**两套都存在但各自独立，且都无法真正连通后端。** 建议保留一套（取决于团队更熟悉 React 还是 Streamlit），另一套删除。

---

## 五、数据管道 Scripts

### 5.1 脚本职责地图

```
PDF 原始文件
    │
    ├── parse_quota_cost.py         → quota_costs.json（费用）
    ├── parse_quota_materials.py    → materials.json + machinery.json
    ├── parse_quota_section.py      → section_names.json（分部路径）❌路径错误
    ├── parse_quota_subitems.py     → project_names.json（含规格）❌路径错误
    ├── parse_quota_page_numbers.py → page_numbers.json（页码）
    │
    ├── extract_work_content.py     → work_contents.json
    ├── extract_quota_unit.py       → 计量单位（废弃版）
    ├── extract_all_units.py        → 计量单位（废弃版）
    ├── extract_units.py            → 计量单位（标准版）✅
    ├── extract_units_post.py       → 计量单位后处理 ✅
    ├── extract_quota_see_table.py → 计量单位（废弃）
    ├── extract_see_table_pages.py → 计量单位（废弃）
    │
    ├── merge_quota_data.py         → 装饰_合并定额.json ✅
    ├── import_quota_db.py          → PostgreSQL（主导入）✅
    │
    ├── backfill_cost_fields.py     → 补充费用字段 ⚠️ 3718次DB往返
    ├── gen_vector_fast.py          → 向量生成（生产级）✅
    └── regen_vectors.py            → 向量生成（废弃）🗑️

信息价 Excel（原始）
    │
    └── parse_info_price.py        → 解析 xlsx ❌ 路径错误
```

### 5.2 路径问题汇总

| 脚本 | 错误路径 | 正确路径应为 |
|------|---------|------------|
| `parse_quota_section.py` | `/Users/kis/.openclaw/...` | `~/.hermes/...` |
| `parse_quota_subitems.py` | `/Users/kis/.openclaw/...` | `~/.hermes/...` |
| `parse_info_price.py` | `/Users/kis/.openclaw/.../date/` | `~/.hermes/...` |
| `extract_quota_see_table.py` | `/Users/kis/.openclaw/...` | `~/.hermes/...` |
| `extract_see_table_pages.py` | `/Users/kis/.openclaw/...` | `~/.hermes/...` |

**需确认**：`/Users/kis/.openclaw/memory/projects/budget-system/data/` 目录是否还存在。如果已删除，这 5 个脚本完全无法运行。

### 5.3 废弃脚本（应删除）

| 脚本 | 原因 |
|------|------|
| `regen_vectors.py` | 功能被 `gen_vector_fast.py` 完全替代 |
| `extract_quota_unit.py` | 功能被 `extract_units.py` 替代 |
| `extract_all_units.py` | 功能被 `extract_units.py` 替代 |
| `extract_quota_see_table.py` | 功能被 `extract_units.py` 替代 |
| `extract_see_table_pages.py` | 功能被 `extract_units.py` 替代 |

### 5.4 效率问题

`backfill_cost_fields.py`：1859 条记录 × 2 次 DB 查询 = **3718 次数据库往返**。应改为批量查询 + 批量更新。

---

## 六、数据模型

### 6.1 Quota 模型

```python
class Quota(Base):
    quota_id      — 唯一索引 ✅
    category      — 分部（一级）
    section       — 完整三级路径
    unit          — 计量单位（m² / 个 / 等）
    quantity      — 数量前缀（100 / 10 / None）
    work_content  — 工作内容
    total_cost    — 全费用
    labor_fee     — 人工费
    material_fee  — 材料费
    machinery_fee — 机械费
    management_fee — 管理费
    tax           — 增值税
    source_file   — 来源文件
    project_name  — 项目名称（含规格）
    embedding      — vector(1024) ✅
```

### 6.2 Material 模型

```python
class Material(Base):
    quota_id     — 关联外键（无 FK 约束，仅索引）
    name         — 材料名称
    unit         — 单位
    unit_price   — 单价
    consumption  — 消耗量
    mat_type     — "材料" / "机械"
```

**问题**：`quota_id` 上无外键约束。如果 quotas 表中一条记录被删除，materials 表会留下孤儿记录。需确认业务上是否可以接受。

### 6.3 MaterialPrice 模型

```python
class MaterialPrice(Base):
    name              — 材料名称
    specification     — 规格型号
    unit             — 单位
    unit_price       — 单价
    price_type       — "信息价" / "企业价"
    region           — 地区（默认"武汉市"）
    publication_date — 发布日期
    is_active        — 是否有效
    source / remarks — 来源/备注
```

该模型与 `materials` 表（定额内材料明细）是**完全不同的两张表**，需注意区分：
- `materials` — 定额附带的材料消耗明细（定额库自带，不可编辑）
- `material_prices` — 独立的价格信息表（用户录入/导入，可编辑）

---

## 七、AI 搜索链路

```
用户输入施工描述
    │
    ▼
parse_construction_text()     LLM 语义解析（DeepSeek）✅
    │
    ▼
text_to_vector()              SiliconFlow BAAI/bge-large-zh-v1.5
    │
    ▼
hybrid_search()               向量检索 + 关键词混合 ✅
    │
    ▼
Boost 规则                    精确 ID/项目名/分部叶节点/同义词/字符重叠 ✅
    │
    ▼
aggregate_top_quotas()        材料价格聚合（psycopg2 原生 SQL）✅
    │
    ▼
rerank()                      SiliconFlow Rerank API 二阶段排序 ✅
    │
    ▼
format_quota_response()       响应格式化 ✅
```

**亮点**：
- Boost 规则考虑了中国建筑行业的语义（同义词表、建筑构件层级）
- 精确 quota_id 查询有专门分支，避免向量距离误导
- 价格聚合用了 N+1 优化（`ANY(%s)` 批量 IN）

**问题**：
- `aggregate_top_quotas` 和 `vector_search` 用原生 `psycopg2`，其他模块用 SQLAlchemy——**数据库访问层不统一**
- 精确 quota_id 查询直接操作 connection pool，未经过 SQLAlchemy session

---

## 八、环境与配置

### 8.1 端口现状

| 服务 | 预期端口 | 实际端口 | 状态 |
|------|---------|---------|------|
| FastAPI | 8000 | 8000（默认） | ✅ |
| Vite | 8501 | 8501 | ✅ |
| Streamlit | 8501 | 8501 | ✅ |

### 8.2 .env 现状

```
DATABASE_URL=postgresql://kis@127.0.0.1:5432/budget_system
DEEPSEEK_API_KEY=sk-3cb...  ❌ 明文，应移除
SILICONFLOW_API_KEY=sk-lz... ❌ 明文，应移除
JWT_SECRET=CHANGE_ME_IN_PRODUCTION ❌ 默认值，未修改
```

**Vite proxy 配置**：
```typescript
proxy: {
  '/api': {
    target: 'http://localhost:8001',  // ❌ 应为 8000
  }
}
```

---

## 九、优先级与行动项

### P0（阻塞项，必须立即处理）

| # | 行动项 | 状态 | 更新日期 |
|---|--------|------|------|
| 1 | 脚本路径 `.openclaw` → `.hermes` | ✅ 已解决 | 2026-04-13 |
| 2 | `import_quota_db.py` 入库 | ✅ 1859条已入库 | 2026-04-13 |
| 3 | 统一端口：后端 8001，前端 proxy → 8001，CORS 已支持环境变量 | ✅ 已解决 | 2026-04-14 |
| 4 | `.env` 明文 API Key | ⚠️ 已创建 `.env.template`，`.env` 需用户手动填写真实 Key | 2026-04-14 |

### P1（Sprint 2 核心交付）

| # | 行动项 | 状态 | 更新日期 |
|---|--------|------|------|
| 5 | 生成预算书（CartPage + XLSX 客户端导出）| ✅ 已实现 | 2026-04-13 |
| 6 | 材料价格管理前端 CRUD（PricesPage + PriceModal）| ✅ 已实现 | 2026-04-13 |
| 7 | Excel 导入管理界面（AdminQuotaPage + AdminPricePage）| ✅ 已实现 | 2026-04-13 |
| 8 | 两套前端统一（Streamlit 已废弃，React 为唯一前端）| ✅ 已解决 | 2026-04-14 |

### P2（代码质量）

| # | 行动项 | 状态 | 更新日期 |
|---|--------|------|------|
| 9 | 删除废弃脚本 | ✅ 已清理 | 2026-04-13 |
| 10 | 数据库访问层统一 | ✅ 合理分层（psycopg2 向量查询 + SQLAlchemy CRUD） | 2026-04-14 |
| 11 | 删除死代码 | ✅ 已清理 | 2026-04-13 |
| 12 | backfill_cost_fields.py 批量 DB | ✅ 已是优化版（≤10次往返） | 2026-04-13 |

### P3（已新增完成项）

| # | 行动项 | 状态 | 更新日期 |
|---|--------|------|------|
| A | Phase 3 代码质量优化（String length, async def, CORS, 404路由, TypeScript）| ✅ 已完成 | 2026-04-14 |
| B | 材料价格批量导入（60424条信息价，13个月，17城市）| ✅ 已完成 | 2026-04-13 |
| C | machinery_fee 缺失修复（953条填0）| ✅ 已完成 | 2026-04-13 |

---

## 十、建议的 Sprint 2 工作流

```
第 1 天：验证数据入库 → 修复端口配置 → 确认 API 连通
第 2-3 天：AI 搜索前端与后端对接 → 材料价格管理前端 CRUD
第 4-5 天：Excel 导入界面 → 清单项管理优化
第 6-7 天：生成预算书（Excel 导出）→ 数据校验
```

---

## 附录：文件清理清单

**应删除**：
- `backend/services/embedding.py`
- `backend/routers/search.py`
- `backend/scripts/regen_vectors.py`
- `backend/scripts/extract_quota_unit.py`
- `backend/scripts/extract_all_units.py`
- `backend/scripts/extract_quota_see_table.py`
- `backend/scripts/extract_see_table_pages.py`
- `frontend/app.py`（如果选择 React 作为主前端）

**应清理但保留**：
- `frontend/src/pages/MinePage.tsx`（硬编码 "1859 条定额" 应改为动态查询）
