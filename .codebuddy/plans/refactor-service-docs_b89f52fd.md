---
name: refactor-service-docs
overview: 精简 service/README.md，保留核心内容（项目结构、架构简介、目录结构、本地开发初始化、单元测试、规范检查），将详细内容拆分到 docs/ 子目录下独立的说明文档中。
todos:
  - id: create-guide-dir
    content: 创建 docs/guide/ 目录及5个专题文档
    status: completed
  - id: slim-readme
    content: 精简 README.md 为核心内容并添加文档导航链接
    status: completed
    dependencies:
      - create-guide-dir
---

## 产品概述

将 service/README.md 精简为只保留最核心的内容（项目架构简介、目录结构、本地开发初始化流程、单元测试启动、规范检查执行），其他详细介绍拆分到 docs/ 目录下按不同功能创建独立的说明文档。

## 核心功能

- 精简 README.md，保留核心快速上手信息，增加文档导航链接
- 新建 `docs/guide/cli-commands.md`：管理命令详细说明（所有 CLI 命令、参数、示例）
- 新建 `docs/guide/environment.md`：环境配置详细说明（多环境切换、配置加载顺序、.env 文件说明）
- 新建 `docs/guide/development.md`：开发规范详细说明（代码风格、数据库规范、Ruff/MyPy 配置说明）
- 新建 `docs/guide/deployment.md`：部署详细说明（Docker 部署、生产环境 Gunicorn 部署）
- 新建 `docs/guide/testing.md`：测试详细说明（测试策略、单元/集成测试命令、覆盖率、conftest 配置）
- 保留已有 `docs/design/项目架构设计与约束.md` 和 `docs/api/` 目录不变

## 技术栈

- 文档格式：Markdown
- 文档目录：`service/docs/guide/`（新建）

## 实现方案

将现有 243 行的 README.md 拆分为 1 个精简入口文件 + 5 个专题文档：

### README.md 精简策略

保留约 80-100 行核心内容：

1. **项目概述**：1 段简介 + 5 个核心特性要点（保留原文）
2. **技术栈**：保留表格
3. **目录结构**：保留完整树形图
4. **快速开始**：环境要求 → 手动安装（去掉脚本安装，简化） → 数据库初始化 → 启动服务
5. **测试 & 规范检查**：各 3-4 行核心命令
6. **文档导航**：链接到各详细文档和已有架构文档

### 各专题文档内容来源

- `cli-commands.md`：从 README "管理命令"章节迁移并扩展
- `environment.md`：从 README "环境配置"章节迁移并扩展
- `development.md`：从 README "开发规范"章节迁移并扩展
- `deployment.md`：从 README "部署"章节迁移并扩展
- `testing.md`：从 README 测试相关命令扩展，结合已有 conftest.py 和 tests/ 目录结构

## 目录结构

```
service/
├── README.md                          # [MODIFY] 精简为核心快速上手 + 文档导航
├── docs/
│   ├── api/                           # [KEEP] API 文档占位目录，保持不变
│   ├── design/
│   │   └── 项目架构设计与约束.md       # [KEEP] 已有架构文档，保持不变
│   └── guide/                         # [NEW] 使用指南目录
│       ├── cli-commands.md            # [NEW] 管理命令详细说明
│       ├── environment.md             # [NEW] 环境配置详细说明
│       ├── development.md             # [NEW] 开发规范详细说明
│       ├── deployment.md              # [NEW] 部署详细说明
│       └── testing.md                 # [NEW] 测试详细说明
```

## 实现备注

- 所有文档使用中文编写，与项目现有风格一致
- README 中的文档导航使用相对路径链接，格式如 `[管理命令](docs/guide/cli-commands.md)`
- 各专题文档开头需有简短概述和返回 README 的链接，形成文档闭环
- 不修改任何代码文件，仅涉及 Markdown 文档