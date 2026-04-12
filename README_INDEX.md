# 项目索引 — 建设工程预算分析系统

> 最后更新：2026-04-12 | 负责人：策士 | 仓库：https://github.com/kismet84/budget-system

---

## 1. 文档总览

| 文档 | 说明 |
|------|------|
| `README.md` | 项目概述、快速上手 |
| `PRD.md` | 产品需求文档（v0.6）|
| `BACKLOG.md` | 产品待办列表（v1.0）|

---

## 2. 代码结构

### 后端 `backend/`

| 文件 | 说明 | 状态 |
|------|------|------|
| `main.py` | FastAPI 入口，注册所有路由 | ✅ |
| `config.py` | 环境配置（pydantic-settings）| ✅ |
| `database.py` | PostgreSQL 连接（Unix socket）| ✅ |
| `core/security.py` | JWT / 密码工具 | ✅ |
| `routers/quota.py` | 定额查询 API | ✅ |
| `routers/search.py` | 关键词搜索 API | ✅ |
| `routers/ai_search.py` | AI 语义搜索（DeepSeek + pgvector）| ✅ |
| `routers/price.py` | 材料价格 API | ✅ |
| `routers/auth.py` | 登录鉴权 | ✅ |
| `services/vector_search.py` | pgvector 语义检索 | ✅ |
| `services/embedding.py` | SiliconFlow embedding | ✅ |
| `services/rerank.py` | 结果重排序 | ✅ |
| `services/llm_parse.py` | DeepSeek LLM 解析 | ✅ |
| `services/price_agg.py` | 价格汇总 | ✅ |
| `models/quota.py` | 定额 SQLAlchemy 模型 | ✅ |
| `models/price.py` | 材料价格模型 | ✅ |
| `models/base.py` | Base 类 | ✅ |
| `schemas/quota.py` | 定额 Pydantic schemas | ✅ |
| `schemas/price.py` | 价格 Pydantic schemas | ✅ |
| `scripts/import_quota_db.py` | 定额数据入库 | ✅ |
| `scripts/merge_quota_data.py` | 定额数据合并 | ✅ |
| `scripts/parse_quota_*.py` | 各字段解析脚本 | ✅ |

### 前端 `frontend/src/`

| 文件 | 说明 | 状态 |
|------|------|------|
| `App.tsx` | React 根组件 | ✅ |
| `main.tsx` | React 18 createRoot | ✅ |
| `pages/SearchPage.tsx` | 定额搜索页（核心）| ✅ |
| `pages/DetailPage.tsx` | 定额详情页 | ✅ |
| `pages/CartPage.tsx` | 清单/购物车页 | ✅ |
| `pages/MinePage.tsx` | 我的页面 | ✅ |
| `components/QuotaCard.tsx` | 定额卡片组件 | ✅ |
| `components/QuotaDetail.tsx` | 定额详情组件 | ✅ |
| `components/CartItem.tsx` | 清单项组件 | ✅ |
| `components/BottomNav.tsx` | 底部导航 | ✅ |
| `components/ErrorBoundary.tsx` | React 错误边界 | ✅ |
| `store/cartStore.ts` | Zustand 状态管理 | ✅ |
| `api/quota.ts` | API 客户端 | ✅ |
| `vite.config.ts` | Vite 配置 + proxy | ✅ |

---

## 3. 数据资产

### 定额数据（装饰工程）

| 文件 | 说明 | 数量 |
|------|------|------|
| `quota_costs.json` | 定额单价（全费用/人工/材料/机械/增值税）| 1,859 条 |
| `materials.json` | 材料明细 | 1,781 条 |
| `section_names.json` | 分部分项名称 | 1,859 条 |
| `project_names.json` | 定额子目名称 | 1,859 条 |
| `page_numbers.json` | 页码索引 | — |
| `machinery.json` | 机械台班单价 | 902 条 |

**存储**：已入库 PostgreSQL `quotas` + `materials` 表，向量已生成。

### 信息价数据

| 索引文件 | 内容 |
|---------|------|
| `月份索引.json` | 13 个月（2025-02 ~ 2026-02）|
| `城市索引.json` | 18 城市 |
| `材料价格总索引.json` | 2,938 种材料 |
| `价格索引/2025-02~2026-02/` | 按月分目录 |

**存储**：已入库 PostgreSQL `prices` 表。

---

## 4. Sprint 规划

| Sprint | 主题 | 核心交付物 |
|--------|------|-----------|
| Sprint 1 | 数据入库 + API 完善 | ✅ E1 定额入库；✅ E2 后端就绪 |
| Sprint 2 | 前端基础 + AI 匹配 | 🔜 AI 搜索联调 |
| Sprint 3 | 预算书生成 | 🔜 导出 Excel/PDF |
| Sprint 4 | 历史项目 + 成本分析 | 🔜 标签化管理 |
| Sprint 5 | 高级功能 + 优化 | 🔜 可选功能 |

**MVP 里程碑**：Sprint 3 结束时 → 核心功能可用

---

## 5. 当前状态

| 模块 | 状态 | 说明 |
|------|------|------|
| 定额数据入库 | ✅ 完成 | 1,859 条已入库 PostgreSQL |
| 信息价入库 | ✅ 完成 | 54,057 条已入库 |
| 向量索引 | ✅ 完成 | pgvector 1,859 条 |
| 后端 API | ✅ 完成 | FastAPI 5 个路由 |
| 前端页面 | ✅ 完成 | 4 个页面，可搜索/详情/清单 |
| AI 语义搜索 | ✅ 后端完成 | 联调完成，HMR bug 已记录 |
| 预算书导出 | 🔜 待开发 | 导出 Excel/PDF |
| 项目管理 | 🔜 待开发 | 历史项目复用 |
| 成本分析 | 🔜 待开发 | 费用占比图 |

---

## 6. 已知问题

| 问题 | 影响 | 状态 |
|------|------|------|
| 前端 SearchPage 按钮 `onclick=noop`（Vite HMR stub）| 搜索功能失效 | 🔜 重启 `pm2 restart budget-frontend` 可临时解决 |
| `management_fee` 字段计算无 bug | — | ✅ 数据正确 |
| 浏览器工具破坏 React 状态 | 前端调试困难 | 🔜 建议用 `pm2 restart` 后直接用 |

---

## 7. 环境变量参考

```bash
# backend/.env
DATABASE_URL=postgresql+asyncpg://user:pass@/budget_db
DEEPSEEK_API_KEY=sk-...
SILICONFLOW_API_KEY=sk-...
SECRET_KEY=your-secret-key
```

```javascript
// frontend/.env
VITE_API_BASE_URL=http://localhost:8001
```
