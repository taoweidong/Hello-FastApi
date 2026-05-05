# Hello-FastApi

> 基于 Vue3 + FastAPI 的全栈中后台管理系统，前端基于 [Pure Admin](https://pure-admin.cn)，后端将 [pure-admin-backend](https://github.com/pure-admin/pure-admin-backend) 完整迁移至 Python FastAPI 框架，保持 API 接口、数据表结构、业务逻辑完全一致。

## 快速开始

### 环境要求

- Python >= 3.10
- Node.js >= 20.19 或 >= 22.13
- pnpm >= 9

### 后端启动

```bash
cd service

# 创建虚拟环境
uv venv --python 3.10 && .venv\Scripts\activate

# 安装依赖并初始化
uv pip install -e ".[dev]"
python -m scripts.cli initall

# 启动服务
python -m scripts.cli runserver
```

### 前端启动

```bash
cd web && pnpm install && pnpm dev
```

| 服务 | 地址 | 说明 |
|------|------|------|
| 前端 | http://localhost:8848 | 管理后台 |
| 后端 API | http://localhost:8000 | FastAPI 服务 |
| API 文档 | http://localhost:8000/docs | Swagger UI |
| 默认账号 | admin / admin123 | 超级管理员 |

## 技术栈

| 层次 | 技术 |
|------|------|
| 前端 | Vue3 + TypeScript + Element Plus + Vite |
| 后端 | FastAPI + SQLModel + DDD 四层架构 |
| 数据库 | SQLite (开发) / PostgreSQL (生产) |
| 缓存 | Redis |
| 认证 | JWT 双令牌 + RBAC 权限控制 |

## 项目结构

```
Hello-FastApi/
├── service/          # 后端服务（FastAPI + DDD 架构）
│   ├── src/          # 源代码
│   ├── tests/        # 测试代码
│   ├── docker/       # Docker 配置
│   └── scripts/      # CLI 管理脚本
├── web/              # 前端项目（Vue3）
└── docs/             # 项目文档
```

## 文档导航

| 文档 | 说明 |
|------|------|
| [后端详细文档](service/README.md) | 后端安装、运行、CLI 命令、单元测试 |
| [前端详细文档](web/README.md) | 前端安装、运行、构建说明 |
| [开发规范](service/docs/guide/development.md) | 代码风格、DDD 分层约束、API 响应格式 |
| [环境配置](service/docs/guide/environment.md) | 多环境配置、.env 文件说明 |
| [管理命令](service/docs/guide/cli-commands.md) | initdb、seedrbac、createsuperuser 等命令 |
| [部署指南](service/docs/guide/deployment.md) | Docker Compose、生产环境部署 |
| [架构设计](service/docs/design/项目架构设计与约束.md) | DDD 四层架构、依赖约束、代码示例 |
| [代码质量报告](service/docs/code-quality-report.md) | Lint/Typecheck/测试结果、改进建议 |

## 修改记录

| 时间 | 修改人 | 主要修改内容 |
|------|--------|-------------|
| 2026-05-05 20:52 | Taowd | 统一换行符为 LF；开发环境数据库切换为 SQLite；修复字典仓库查询方法；修复 Alembic 测试编码和空输出问题；修复前端操作日志缩进 |
| 2026-04-30 | Taowd | P0 基础设施完善：集成 Alembic 数据库迁移、完善限流中间件（Redis 存储）、补全 Docker Compose（PostgreSQL + Redis）、添加 Jenkins CI/CD Pipeline |
| 2026-04-30 | Taowd | 重构 HTTP 限流模块：使用 SlowAPIMiddleware 全局中间件替代 @limiter.limit 装饰器 |
| 2026-04-26 09:38 | Taowd | 重构 .opencode 目录结构；agent-browser 技能迁移 |
| 2026-04-26 09:33 | Taowd | 新增 .opencode 目录（含 code-gen、git-release 技能配置） |
| 2026-04-26 09:27 | Taowd | 新增 commit-changelog 提交记录 Skill |

## 许可证

[MIT License](LICENSE)
