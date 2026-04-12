# 项目索引 — 建设工程预算分析系统

> 最后更新：2026-04-09 | 负责人：策士 | 仓库：https://github.com/kismet84/budget-system

---

## 1. 文档总览

| 文档 | 说明 | 状态 |
|------|------|------|
| `README.md` | 项目概述、快速上手 | ✅ |
| `PRD.md` | 产品需求文档（v0.6）| ✅ |
| `BACKLOG.md` | 产品待办列表（v1.0）| ✅ 新增 |
| `docs/` | 每日报告/分项报告/进度报告 | ✅ |

---

## 2. 代码文件

| 文件 | 说明 | 状态 |
|------|------|------|
| `backend/routers/ai_search.py` | AI 语义搜索 API（核心）| ✅ |
| `backend/routers/import_excel.py` | Excel 导入路由（353行）| ✅ |
| `backend/routers/quota.py` | 定额查询 API | ✅ 基础 |
| `backend/services/vector_search.py` | 向量检索服务 | ✅ |
| `backend/services/llm_parse.py` | LLM 解析服务 | ✅ |
| `backend/services/price_agg.py` | 价格汇总服务 | ✅ |
| `backend/services/embedding.py` | Embedding 服务 | ✅ |
| `backend/models/quota.py` | 定额数据模型 | ✅ |
| `backend/main.py` | FastAPI 入口 | ⚠️ 骨架 |
| `backend/routers/auth.py` | 鉴权 API | ❌ 未开始 |
| `backend/routers/project.py` | 项目管理 API | ❌ 未开始 |
| `backend/routers/price.py` | 材料价格 API | ❌ 未开始 |

### 前端
**完全未开始** — React 脚手架待初始化

---

## 3. 数据资产

### 3.1 定额数据

**原始 PDF**：`data/定额/raw/装饰/`（2024版装饰工程定额）

**解析后 JSON**：`data/定额/parsed/装饰/`

| 文件 | 说明 |
|------|------|
| `quota_costs.json` | 定额单价（1,859条，含全费用/人工/材料/机械/增值税）|
| `materials.json` | 材料明细（1,781条）|
| `section_names.json` | 分部分项名称（1,859条）|
| `project_names.json` | 定额子目名称（1,859条）|
| `page_numbers.json` | 页码索引 |
| `machinery.json` | 机械台班单价（902条）|

**数据规模**：1,859 条 ⚠️ 待确认完整性（覆盖哪些章节）

### 3.2 信息价数据

| 索引文件 | 内容 |
|---------|------|
| `月份索引.json` | 13 个月 |
| `城市索引.json` | 18 城市 |
| `材料价格总索引.json` | 2,938 种材料 |
| `价格索引/2025-02~2026-02/` | 按月分目录 |

**数据规模**：54,057 条 ✅ 完整（2025-02 ~ 2026-02）

---

## 4. Sprint 规划（来自 BACKLOG.md）

| Sprint | 主题 | 核心交付物 |
|--------|------|-----------|
| Sprint 1（继续）| 数据入库 + API 完善 | E1 完成；E2 后端就绪 |
| Sprint 2 | 前端基础 + AI 匹配 | E2 前端；E3 价格管理 |
| Sprint 3 | 预算书生成 | E4 核心功能 |
| Sprint 4 | 历史项目 + 成本分析 | E5 + E6 |
| Sprint 5 | 高级功能 + 优化 | 可选功能 |

**MVP 里程碑**：Sprint 3 结束时 → E2 + E3 + E4 核心功能可用

---

## 5. 当前阻塞项

| 阻塞项 | 影响 | 状态 |
|--------|------|------|
| 定额数据完整性确认（1,859 条覆盖哪些章节）| E1 入库 | ⚠️ 待确认 |
| PostgreSQL + pgvector 部署 | E2 AI 匹配 | ⚠️ 待搭建 |
| 数据库迁移（models → 实际表）| 所有功能 | ⚠️ 待开发 |
| 前端项目初始化 | E2-E6 前端 | ⚠️ 待开始 |
| MiniMax API Key 申请 | E2 AI 匹配 | ⚠️ 待申请 |

---

## 6. 项目结构

```
budget-system/
├── backend/
│   ├── main.py              # FastAPI 入口 ⚠️ 骨架
│   ├── routers/             # API 路由
│   │   ├── ai_search.py     # ✅ AI 语义搜索
│   │   ├── import_excel.py  # ✅ Excel 导入
│   │   ├── quota.py         # ✅ 定额查询
│   │   ├── auth.py          # ❌ 鉴权
│   │   ├── project.py       # ❌ 项目管理
│   │   └── price.py         # ❌ 材料价格
│   ├── services/            # 业务服务
│   │   ├── vector_search.py # ✅ 向量检索
│   │   ├── llm_parse.py    # ✅ LLM 解析
│   │   ├── price_agg.py    # ✅ 价格汇总
│   │   └── embedding.py     # ✅ Embedding
│   └── models/              # 数据模型
├── frontend/                # ❌ 未开始
├── data/
│   ├── 定额/
│   │   ├── raw/装饰/       # 原始 PDF
│   │   └── parsed/装饰/     # 解析后 JSON（1,859条）
│   └── 信息价/
│       └── indexed/         # 54,057 条 ✅
├── PRD.md                  # 产品需求文档
└── BACKLOG.md              # 产品待办列表
```

---

## 7. 关键路径

```
Step 1: 确认定额数据完整性（哪些章节已解析）
    ↓
Step 2: 数据库迁移（models → 表结构）
    ↓
Step 3: 定额数据入库（S1.2 核心）
    ↓
Step 4: 向量索引生成（T4）
    ↓
Step 5: 前端初始化（React + Ant Design）
    ↓
Step 6: AI 匹配联调（S2.1 + S2.2）
```

---

_本文档随项目进展更新。如有变更，在此处记录。_
