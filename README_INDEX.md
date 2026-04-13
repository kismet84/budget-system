# 项目索引 — 建设工程预算分析系统

> 最后更新：2026-04-13 | 负责人：策士 | 仓库：https://github.com/kismet84/budget-system

---

## 1. 文档总览

| 文档 | 说明 |
|------|------|
| `README.md` | 项目概述、快速上手、技术栈 |
| `PRD.md` | 产品需求文档（v0.6）|
| `BACKLOG.md` | 产品待办列表（v1.0）|

---

## 2. 代码结构

### 后端 `backend/`

| 文件 | 说明 | 状态 |
|------|------|------|
| `main.py` | FastAPI 入口，注册所有路由 | ✅ |
| `config.py` | 环境配置（pydantic-settings）| ✅ |
| `database.py` | PostgreSQL 连接（Unix socket / 127.0.0.1）| ✅ |
| `core/security.py` | JWT / 密码工具 | ✅ |
| `routers/quota.py` | 定额查询 API | ✅ |
| `routers/search.py` | 关键词搜索 API | ✅ |
| `routers/ai_search.py` | AI 语义搜索（DeepSeek + pgvector）| ✅ |
| `routers/price.py` | 材料价格 API | ✅ |
| `routers/auth.py` | 登录鉴权 | ✅ |
| `routers/import_excel.py` | Excel 导入（冗余，待清理）| ⚠️ |
| `services/vector_search.py` | pgvector 语义检索 | ✅ |
| `services/embedding.py` | SiliconFlow embedding | ✅ |
| `services/rerank.py` | 二阶段重排序 | ✅ |
| `services/llm_parse.py` | DeepSeek LLM 解析 | ✅ |
| `services/price_agg.py` | 价格汇总 + get_connection() | ✅ |
| `models/quota.py` | 定额模型（含 quantity 字段）| ✅ |
| `models/material.py` | 材料明细模型 | ✅ |
| `models/price.py` | 材料价格模型 | ✅ |
| `schemas/quota.py` | 定额 Pydantic schemas | ✅ |
| `schemas/price.py` | 价格 Pydantic schemas | ✅ |
| `scripts/parse_quota_cost.py` | 费用数据解析 | ✅ |
| `scripts/parse_quota_materials.py` | 材料明细解析 | ✅ |
| `scripts/parse_quota_section.py` | 分部工程解析 | ✅ |
| `scripts/parse_quota_project_name.py` | 项目名称解析 | ✅ |
| `scripts/extract_units.py` | 计量单位全量提取 | ✅ |
| `scripts/extract_units_post.py` | 计量单位 fallback 推断 | ✅ |
| `scripts/merge_quota_data.py` | 合并 6 个 JSON | ✅ |
| `scripts/import_quota_db.py` | 入库 PostgreSQL | ✅ |

### 前端 `frontend/src/`

| 文件 | 说明 | 状态 |
|------|------|------|
| `App.tsx` | React 根组件（BrowserRouter + Routes）| ✅ |
| `main.tsx` | createRoot 入口，React.StrictMode | ✅ |
| `pages/SearchPage.tsx` | 定额搜索页（核心，AI 语义搜索）| ✅ |
| `pages/DetailPage.tsx` | 定额详情页 + 材料明细表格 | ✅ |
| `pages/CartPage.tsx` | 清单/购物车页 | ✅ |
| `pages/MinePage.tsx` | 我的页面 | ✅ |
| `components/QuotaCard.tsx` | 定额卡片（含推荐标签）| ✅ |
| `components/QuotaDetail.tsx` | 定额详情组件 | ✅ |
| `components/CartItem.tsx` | 清单项组件 | ✅ |
| `components/BottomNav.tsx` | 底部导航 | ✅ |
| `store/cartStore.ts` | Zustand 状态管理 | ✅ |
| `api/quota.ts` | API 客户端 | ✅ |
| `types/quota.ts` | TypeScript 类型定义 | ✅ |
| `vite.config.ts` | Vite 配置 + proxy（HMR 已禁用）| ✅ |

---

## 3. 数据资产

### 定额数据（装饰工程）

| 文件 | 说明 | 数量 |
|------|------|------|
| `quota_costs.json` | 定额单价（全费用/人工/材料/机械/费用/增值税）| 1,859 条 |
| `materials.json` | 材料明细（名称/单位/单价/消耗量）| 1,781 条 |
| `section_names.json` | 分部分项名称 | 1,859 条 |
| `project_names.json` | 定额子目名称（全角字符，已同步 DB）| 1,859 条 |
| `计量单位.json` | 计量单位（quantity + unit 拆分）| 1,859 条 |
| `machinery.json` | 机械台班单价 | 902 条 |

**存储**：已入库 PostgreSQL `quotas` + `materials` 表，向量已生成。
quantity/unit 已拆分完毕（quantity=100, unit='m²' 等）。

### 信息价数据

| 索引文件 | 内容 |
|---------|------|
| `月份索引.json` | 13 个月（2025-02 ~ 2026-02）|
| `城市索引.json` | 18 城市 |
| `材料价格总索引.json` | 2,938 种材料 |
| `价格索引/2025-02~2026-02/` | 按月分目录 |

**存储**：已入库 PostgreSQL `prices` 表（54,057 条）。

---

## 4. Sprint 规划

| Sprint | 主题 | 核心交付物 | 状态 |
|--------|------|-----------|------|
| Sprint 1 | 数据入库 + API 完善 | ✅ 定额入库；✅ 后端就绪 | 完成 |
| Sprint 2 | 前端基础 + AI 匹配 | ✅ AI 搜索联调；✅ 详情页材料明细 | 完成 |
| Sprint 3 | 预算书生成 | 🔜 导出 Excel/PDF | 待开发 |
| Sprint 4 | 历史项目 + 成本分析 | 🔜 标签化管理 | 待开发 |
| Sprint 5 | 高级功能 + 优化 | 🔜 可选功能 | 待开发 |

**MVP 里程碑**：Sprint 3 结束时 → 核心功能可用

---

## 5. 当前状态

| 模块 | 状态 | 说明 |
|------|------|------|
| 定额数据入库 | ✅ 完成 | 1,859 条已入库，含 quantity + unit 拆分 |
| 信息价入库 | ✅ 完成 | 54,057 条已入库 |
| 向量索引 | ✅ 完成 | pgvector 1,859 条 |
| 后端 API | ✅ 完成 | FastAPI 7 个路由 |
| 前端页面 | ✅ 完成 | 4 个页面，可搜索/详情/清单 |
| AI 语义搜索 | ✅ 完成 | 前后端联调完成 |
| 材料明细 | ✅ 完成 | DetailPage 新增材料表格 |
| 预算书导出 | 🔜 待开发 | 导出 Excel/PDF |
| 项目管理 | 🔜 待开发 | 历史项目复用 |
| 成本分析 | 🔜 待开发 | 费用占比图 |

---

## 6. 已修复 Bug 记录

| Bug | 根因 | 修复方式 | 日期 |
|-----|------|---------|------|
| 前端搜索按钮无响应 | SearchPage finally 块导致状态跳过 | 移除 finally 中 isMounted 赋值 | 04-12 |
| CartPage 按钮被 BottomNav 遮挡 | z-index 50 vs 10 | 按钮 bottom-14, z-[60] | 04-12 |
| 精确 quota_id 搜索 500 | `SessionLocal` 无 `.cursor()` 方法 | 改用 `get_connection()` | 04-13 |
| 精确匹配排名错误 | Rerank 逻辑写在精确分支外 | 精确匹配时跳过 Rerank | 04-13 |
| Vite HMR onClick=noop | HMR + React 18 StrictMode 竞争 | `hmr: false` | 04-12 |

---

## 7. 关键技术细节

### 计量单位（quantity + unit）
PDF 原文中"计量单位：100m²"为行业惯例（每100平方米为一个计量单位）。已拆分为：
- `quantity` = 100（数量前缀）
- `unit` = 'm²'（单位）
- 前端显示：`${quantity}${unit}` → "100m²"

### 费用计算关系（已验证）
```
total_cost = labor + material + machinery + management + tax
           = (labor + material + machinery + management) × 1.09
tax = (labor + material + machinery + management) × 9%  ✓ 100%
```

### 数据库连接（macOS 注意事项）
- macOS `localhost` 走 IPv6（`::1`），PostgreSQL trust 认证失败
- 必须使用 `127.0.0.1`

---

## 8. 环境变量参考

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
