# 测试指南

> 三层测试体系：unit（纯逻辑，mock/内存替身）→ integration（真实 SQLite 全链路）→
> e2e（Playwright 真实双端）。外加提交门禁。

[← 返回文档导航](../README.md)

---

## 1. 后端

### 1.1 目录与隔离机制

```
tests/
├── conftest.py             根级：APP_ENV=testing、禁用真实 Redis、每测试建表/删表（autouse）
├── unit/conftest.py        覆盖根级 setup_database 为 no-op（纯逻辑单测免 DDL，全量 45s）
│                           + 引擎泄漏兜底 dispose（aiosqlite 非守护线程会阻塞退出）
├── unit/                   纯逻辑：AsyncMock 或 fakes.py 内存仓储
├── integration/conftest.py flow_seed 种子 + flow_client（清库→种子→真实会话）
└── integration/            真实 DB 全链路 + 仓储契约对拍（fake↔real）
```

- 单测**不碰数据库**：需要 DB 的断言一律放 integration；
- **替身契约对拍**：`tests/integration/test_repository_contract.py` 保证 fakes.py
  与真实仓储语义一致——新增仓储方法时必须补对拍用例；
- xdist 安全：每个 worker 独立临时 SQLite 文件。

### 1.2 命令

```bash
pytest tests/unit/            # ~45s
pytest tests/integration/     # ~120s
pytest                        # 全量 ~170s
pytest -k "dict"              # 按名过滤
pytest --cov=src --cov-report=term-missing
```

### 1.3 写什么测试

| 层 | 必测分支 |
|---|---|
| Service | 正常路径 / 查重冲突 / 不存在 404 / 权限 403 / 缓存失效调用 |
| DTO | 必填、长度、值域边界（非法值必须 ValidationError） |
| Router | 依赖覆盖 + 200/403/404/400 分支（权限链用依赖覆盖 superuser/普通用户两种实体） |
| 基础设施 | mock 外部客户端；降级路径（Redis None）必须覆盖 |

## 2. 前端

### 2.1 vitest 单测

```
src/**/__tests__/*.spec.ts    # vitest + happy-dom + @vue/test-utils
pnpm test:unit                # 19 例（composables / websocket 客户端）
```

规范：不共享状态、不依赖执行顺序、mock 边界（`@/utils/message`、element-plus）。

### 2.2 Playwright e2e

```
web/e2e/crud-<m>.spec.ts      # 页面交互全链路
pnpm test:e2e                 # 需双端运行中（backend:8000 + frontend:8848）
```

- `auth.setup.ts` 登录一次复用 storageState（规避登录限流）；
- 四个 project：setup / auth（可并行）/ smoke（只读）/ crud（workers=1 串行防写竞争）；
- 页面元素断言注意 strict mode：同名按钮需限定作用域。

## 3. 提交门禁（AGENTS.md 协作规范，硬性）

```bash
# 后端（service/）
ruff check src/ tests/ && python -m mypy src/ && pytest tests/unit/
# 前端（web/）
pnpm lint && pnpm typecheck && pnpm test:unit
```

- 全部通过才允许提交；失败先修复再重跑，禁止注释用例"变绿"；
- 跨模块改动（路由契约/DTO/中间件/缓存/认证）必须加跑 `pytest tests/integration/`；
- 接口契约变更必须同步前端类型（`web/src/api/types.ts`）与对应单测。

## 4. 可重复性红线

- 单测禁止：真实网络、真实 Redis、执行顺序依赖、共享可变全局；
- 时间敏感断言用显式 mtime/注入时钟（参照 `test_log_file_service.py` 的 utime 手法）；
- 临时文件在用例内创建并清理（或交给 tmp_path fixture）。

## 5. 延伸阅读

- 后端测试规范：`service/docs/guide/testing.md`
- 全量功能验证清单（人工/Agent 用）：[reference/full-test-cases.md](../reference/full-test-cases.md)
