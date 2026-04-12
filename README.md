# 建设工程预算分析系统

> 施工单位自用轻量级工程预算工具

## 项目概述

- **定位**：专注投标报价估算 + 成本分析，不替代广联达
- **目标用户**：施工单位预算负责人
- **工程类型**：房建 / 市政 / 园林
- **开发周期**：6 个月（业余时间自投）

## 核心功能

| 优先级 | 功能 | 说明 |
|--------|------|------|
| **Must** | AI 定额语义匹配 | 用户描述施工场景 → 推荐定额 Top3 |
| **Must** | 数据手动维护 | 定额/信息价均从官方 Excel 导入 |
| **Must** | 预算书生成 | 一键导出 Excel / PDF |
| **Should** | 历史项目复用 | 标签化管理，快速复制调整 |
| **Should** | 成本分析 | 费用占比图 + 单方指标对比 |

## 技术栈

| 层级 | 技术 | 说明 |
|------|------|------|
| 前端 | React + Ant Design Pro | 企业级 UI |
| AI 层 | DeepSeek API + SiliconFlow 向量 + pgvector | 语义匹配核心 |
| 后端 | Python FastAPI | 开发快，异步支持好 |
| 数据库 | PostgreSQL + pgvector | 向量存储，定额+材料+项目 |

## 数据规模

| 数据 | 来源 | 数量 | 状态 |
|------|------|------|------|
| 定额 | 湖北数字造价平台 | 1,859 条（`parsed/装饰/` 目录，含 quota_costs / materials / section_names / project_names / machinery）| ⚠️ 待确认完整性 |
| 信息价 | 湖北数字造价平台 | 54,057 条（13个月，2025-02 ~ 2026-02）| ✅ 完整 |

## 快速开始

### 后端

```bash
cd backend
pip install -r requirements.txt
python -c "from main import app; print('✅ FastAPI OK')"
uvicorn main:app --reload
```

### 前端

```bash
cd frontend
npm install
npm run dev
```

## 项目结构

```
budget-system/
├── backend/              # FastAPI 后端
│   ├── routers/          # API 路由
│   ├── models/           # 数据库模型
│   ├── schemas/          # Pydantic schemas
│   ├── services/         # 业务服务
│   ├── scripts/          # 数据处理脚本（解析/入库/向量生成）
│   └── main.py           # FastAPI 入口
├── frontend/             # React 前端（待开发）
│   └── src/
├── data/                 # 数据文件（不提交到 Git）
│   ├── 定额/
│   │   ├── raw/装饰/    # 原始 PDF
│   │   └── parsed/装饰/  # 解析后 JSON
│   └── 信息价/
│       └── indexed/      # 按月份索引
├── PRD.md               # 产品需求文档
├── BACKLOG.md           # 产品待办列表
└── README.md           # 本文件
```

## 数据目录结构

```
data/
├── 定额/
│   ├── raw/装饰/           # 原始 PDF（2024版装饰工程定额）
│   └── parsed/装饰/        # 解析后 JSON（quota_costs / materials / section_names / project_names / machinery）
└── 信息价/
    ├── indexed/月份索引.json
    ├── indexed/城市索引.json
    ├── indexed/材料价格总索引.json
    └── indexed/价格索引/   # 按月份（2025-02 ~ 2026-02）
```

## 文档

- [产品需求文档 PRD.md](PRD.md)
- [产品待办列表 BACKLOG.md](BACKLOG.md)
- [项目索引 docs/README_INDEX.md](docs/README_INDEX.md)
