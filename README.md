# 建设工程预算分析系统

> 施工单位自用轻量级工程预算工具

**仓库**：https://github.com/kismet84/budget-system

---

## 项目概述

- **定位**：专注投标报价估算 + 成本分析，不替代广联达
- **目标用户**：施工单位预算负责人
- **工程类型**：房建 / 市政 / 园林
- **开发周期**：6 个月（业余时间自投）

---

## 技术栈

| 层级 | 技术 | 说明 |
|------|------|------|
| 前端 | React + TypeScript + Vite + Zustand + TailwindCSS | 已完成 4 个页面 |
| 后端 | Python FastAPI + SQLAlchemy + psycopg2 | 异步 API + 同步 DB |
| AI 层 | DeepSeek API + SiliconFlow 向量 + pgvector | 语义匹配核心 |
| 数据库 | PostgreSQL 15+ + pgvector | 向量存储，定额+材料+价格 |
| 部署 | PM2（Node 进程管理）+ Vite proxy | - |

---

## 核心功能

| 优先级 | 功能 | 状态 |
|--------|------|------|
| **Must** | AI 定额语义匹配 | ✅ 已完成，前后端联调 |
| **Must** | 定额数据手动维护 | ✅ 1,859 条已入库 PostgreSQL |
| **Must** | 材料价格双轨管理（信息价+企业价）| ✅ 54,057 条已入库 |
| **Must** | 预算书生成（导出） | 🔜 下一步 |
| **Should** | 历史项目复用 | 🔜 Sprint 2 |
| **Should** | 成本分析 | 🔜 Sprint 3 |

---

## 快速开始

### 前提

- Python 3.10+
- Node.js 18+
- PostgreSQL 15+ with pgvector extension
- DeepSeek API Key（`DEEPSEEK_API_KEY` 环境变量）

### 数据库

```bash
# 确保 PostgreSQL 运行中
# DATABASE_URL 必须用 127.0.0.1（macOS localhost 走 IPv6）
# backend/.env 中配置：
DATABASE_URL=postgresql://kis@127.0.0.1:5432/budget_system
```

### 后端

```bash
cd ~/.hermes/memory/projects/budget-system/backend
source venv/bin/activate

# 数据库连接验证
python -c "from database import engine; print('✅ DB OK')"

# 启动服务
uvicorn main:app --host 0.0.0.0 --port 8001 --reload
```

### 前端

```bash
cd ~/.hermes/memory/projects/budget-system/frontend
npm install
npm run dev
# 访问 http://localhost:8501
```

### PM2 生产环境

```bash
pm2 start ecosystem.config.js
# 重启前端（修复 HMR 等问题）
pm2 restart budget-frontend
```

---

## 项目结构

```
budget-system/
├── backend/
│   ├── main.py                  # FastAPI 入口
│   ├── config.py                # 环境配置（pydantic-settings）
│   ├── database.py              # PostgreSQL 连接（Unix socket / 127.0.0.1）
│   ├── core/
│   │   └── security.py          # JWT / 密码工具
│   ├── routers/
│   │   ├── quota.py             # 定额查询
│   │   ├── search.py            # 关键词搜索
│   │   ├── ai_search.py         # AI 语义搜索（DeepSeek + pgvector）
│   │   ├── price.py             # 材料价格
│   │   ├── auth.py              # 登录鉴权
│   │   └── import_excel.py      # Excel 导入（冗余，待清理）
│   ├── services/
│   │   ├── vector_search.py     # pgvector 语义检索
│   │   ├── embedding.py         # SiliconFlow embedding
│   │   ├── rerank.py            # 二阶段重排序
│   │   ├── llm_parse.py         # DeepSeek LLM 解析
│   │   └── price_agg.py          # 价格汇总 + get_connection()
│   ├── models/
│   │   ├── quota.py             # 定额 SQLAlchemy 模型（含 quantity 字段）
│   │   ├── material.py          # 材料明细模型
│   │   └── price.py             # 材料价格模型
│   ├── schemas/
│   │   ├── quota.py             # 定额 Pydantic schemas
│   │   └── price.py             # 价格 Pydantic schemas
│   └── scripts/                  # 数据处理管道
│       ├── parse_quota_cost.py         # 提取费用数据
│       ├── parse_quota_materials.py     # 提取材料明细
│       ├── parse_quota_section.py       # 提取分部工程
│       ├── parse_quota_project_name.py  # 提取项目名称
│       ├── extract_units.py             # 提取计量单位（全量）
│       ├── extract_units_post.py        # 计量单位 fallback 推断
│       ├── merge_quota_data.py          # 合并 6 个 JSON
│       └── import_quota_db.py           # 入库 PostgreSQL
├── frontend/
│   ├── src/
│   │   ├── App.tsx              # React 根组件（BrowserRouter）
│   │   ├── main.tsx             # createRoot 入口
│   │   ├── pages/
│   │   │   ├── SearchPage.tsx   # 定额搜索（核心）
│   │   │   ├── DetailPage.tsx   # 定额详情 + 材料明细
│   │   │   ├── CartPage.tsx     # 清单/购物车
│   │   │   └── MinePage.tsx     # 我的
│   │   ├── components/
│   │   │   ├── QuotaCard.tsx    # 定额卡片
│   │   │   ├── QuotaDetail.tsx  # 定额详情组件
│   │   │   ├── CartItem.tsx     # 清单项
│   │   │   └── BottomNav.tsx    # 底部导航
│   │   ├── store/
│   │   │   └── cartStore.ts     # Zustand 状态
│   │   └── api/
│   │       └── quota.ts         # API 客户端
│   ├── vite.config.ts           # Vite + proxy（HMR 已禁用）
│   └── index.html
├── data/                        # 数据文件（不提交到 Git）
│   └── 定额/parsed/             # 解析后 JSON
├── docs/                        # 测试报告等文档
└── ecosystem.config.js          # PM2 配置
```

---

## API 路由

| 路由 | 方法 | 说明 |
|------|------|------|
| `/api/v1/quotas` | GET | 定额列表/搜索 |
| `/api/v1/quotas/{id}` | GET | 定额详情 |
| `/api/v1/quotas/{id}/materials` | GET | 定额材料明细 |
| `/api/v1/search` | POST | 关键词搜索 |
| `/api/v1/ai/search` | POST | AI 语义搜索 |
| `/api/v1/prices` | GET | 材料价格 |
| `/auth/login` | POST | 用户登录 |

---

## 数据规模

| 数据 | 来源 | 数量 | 状态 |
|------|------|------|------|
| 定额（装饰） | 湖北数字造价平台 | 1,859 条 | ✅ 已入库，含 quantity + unit 拆分 |
| 信息价 | 湖北数字造价平台 | 54,057 条（13 个月） | ✅ 已入库 |
| 向量索引 | SiliconFlow | 1,859 条 | ✅ 已生成 |

---

## 环境变量

```bash
# backend/.env
DATABASE_URL=postgresql://kis@127.0.0.1:5432/budget_system
DEEPSEEK_API_KEY=***
SILICONFLOW_API_KEY=***
SECRET_KEY=***
```

```javascript
// frontend/.env
VITE_API_BASE_URL=http://localhost:8001
```

---

## 开发说明

- **API 前缀**：`/api/v1`（通过 `settings.API_V1_PREFIX` 配置）
- **数据库连接**：macOS 必须用 `127.0.0.1`（`localhost` 走 IPv6 导致 trust 认证失败）
- **向量检索**：pgvector `cosine_distance` 排序，配合 SiliconFlow embedding
- **前端 proxy**：Vite dev server 代理 `/api` → `http://localhost:8001`
- **HMR**：生产环境已禁用（`hmr: false`），解决 React 18 + StrictMode 双重渲染竞争条件

---

## 已知 Bug 与修复记录

| Bug | 影响 | 状态 |
|-----|------|------|
| 前端 SearchPage finally 导致搜索卡死 | 搜索无响应 | ✅ 已修复（SearchPage.tsx） |
| 精确 quota_id 搜索 500 错误 | `SessionLocal` 无 `.cursor()` | ✅ 已修复（ai_search.py 用 `get_connection()`） |
| 精确匹配 Rerank 顺序错误 | A9-1 被 A9-15 压排 | ✅ 已修复（ai_search.py 跳过 Rerank） |
| Vite HMR + React 18 竞争条件 | onClick → noop | ✅ 已修复（`hmr: false`） |
| CartPage 按钮被 BottomNav 遮挡 | 无法点击生成预算书 | ✅ 已修复（z-index 调整） |
| `import_excel.py` 冗余 | 重复实现已有逻辑 | ⚠️ 待清理 |
