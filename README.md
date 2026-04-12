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
| 前端 | React + TypeScript + Vite + Zustand | 已完成基础页面 |
| 后端 | Python FastAPI | 异步 API |
| AI 层 | DeepSeek API + SiliconFlow 向量 + pgvector | 语义匹配核心 |
| 数据库 | PostgreSQL + pgvector | 向量存储，定额+材料+项目 |
| 部署 | PM2（Node 进程管理）+ Vite proxy | - |

---

## 核心功能

| 优先级 | 功能 | 状态 |
|--------|------|------|
| **Must** | AI 定额语义匹配 | ✅ 后端就绪 |
| **Must** | 定额数据手动维护 | ✅ 已入库 PostgreSQL |
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

### 后端

```bash
cd backend
pip install -r requirements.txt

# 数据库（确保 PostgreSQL 运行中）
# 配置 .env 中的 DATABASE_URL
python -c "from database import engine; print('✅ DB OK')"

uvicorn main:app --reload --port 8001
```

### 前端

```bash
cd frontend
npm install
npm run dev
# 访问 http://localhost:8501
```

### PM2 生产环境

```bash
pm2 start ecosystem.config.js
```

---

## 项目结构

```
budget-system/
├── backend/
│   ├── main.py              # FastAPI 入口
│   ├── config.py            # 环境配置
│   ├── database.py          # PostgreSQL 连接（Unix socket）
│   ├── core/                # 核心工具（security 等）
│   ├── middleware/          # 中间件
│   ├── routers/             # API 路由
│   │   ├── quota.py         # 定额查询
│   │   ├── search.py        # 搜索
│   │   ├── ai_search.py     # AI 语义搜索
│   │   ├── price.py         # 材料价格
│   │   └── auth.py          # 登录鉴权
│   ├── services/            # 业务服务
│   │   ├── vector_search.py # pgvector 向量检索
│   │   ├── embedding.py     # SiliconFlow embedding
│   │   ├── rerank.py        # 重排序
│   │   ├── llm_parse.py     # DeepSeek LLM 解析
│   │   └── price_agg.py     # 价格汇总
│   ├── models/              # SQLAlchemy 模型
│   ├── schemas/             # Pydantic schemas
│   └── scripts/             # 数据处理脚本
│       ├── parse_quota_cost.py
│       ├── parse_quota_materials.py
│       ├── parse_quota_section.py
│       ├── merge_quota_data.py
│       └── import_quota_db.py
├── frontend/
│   ├── src/
│   │   ├── App.tsx
│   │   ├── main.tsx
│   │   ├── pages/
│   │   │   ├── SearchPage.tsx   # 定额搜索
│   │   │   ├── DetailPage.tsx   # 定额详情
│   │   │   ├── CartPage.tsx     # 购物车/清单
│   │   │   └── MinePage.tsx     # 我的
│   │   ├── components/
│   │   │   ├── QuotaCard.tsx    # 定额卡片
│   │   │   ├── QuotaDetail.tsx  # 定额详情组件
│   │   │   ├── CartItem.tsx     # 清单项
│   │   │   └── BottomNav.tsx    # 底部导航
│   │   ├── store/              # Zustand 状态
│   │   └── api/                # API 客户端
│   └── vite.config.ts           # Vite + proxy 配置
├── data/                       # 数据文件（不提交到 Git）
│   ├── 定额/parsed/            # 解析后 JSON（已入库，可忽略）
│   └── 信息价/indexed/          # 信息价数据
└── docs/                      # 文档（按需创建）
```

---

## API 路由

| 路由 | 方法 | 说明 |
|------|------|------|
| `/api/v1/quotas` | GET | 定额列表/搜索 |
| `/api/v1/quotas/{id}` | GET | 定额详情 |
| `/api/v1/search` | POST | 关键词搜索 |
| `/api/v1/ai-search` | POST | AI 语义搜索 |
| `/api/v1/prices` | GET | 材料价格 |
| `/auth/login` | POST | 用户登录 |

---

## 数据规模

| 数据 | 来源 | 数量 | 状态 |
|------|------|------|------|
| 定额（装饰） | 湖北数字造价平台 | 1,859 条 | ✅ 已入库 PostgreSQL |
| 信息价 | 湖北数字造价平台 | 54,057 条（13个月） | ✅ 已入库 |
| 向量索引 | SiliconFlow | 1,859 条 | ✅ 已生成 |

---

## 环境变量

```bash
# backend/.env
DATABASE_URL=postgresql+asyncpg://user:pass@/budget_db
DEEPSEEK_API_KEY=sk-...
SILICONFLOW_API_KEY=sk-...
SECRET_KEY=your-secret-key
```

---

## 开发说明

- **API 前缀**：`/api/v1`（通过 `settings.API_V1_PREFIX` 配置）
- **数据库连接**：Unix socket（`/tmp/.s.PGSQL.5432`），不通过 TCP
- **向量检索**：pgvector `cosine_distance` 排序，配合 SiliconFlow embedding
- **前端 proxy**：Vite dev server 代理 `/api` → `http://localhost:8001`
