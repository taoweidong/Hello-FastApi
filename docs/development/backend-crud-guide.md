# 后端开发指南：新增一个 CRUD 模块

> 以「公告(notice)」与「岗位(post)」为模板，走通新增一个业务模块的全流程。
> 最新完整范例：**示例数据表（`example_data`，commit `aa0587b`）**——严格按本指南落地，
> 并示范了电子表格批量回写扩展模式（`batch-save` 差异保存，供 Univer 页面使用）。
> 全程约 13 个文件 / 600-700 行；照本清单执行可避免遗漏注册点。

[← 返回文档导航](../README.md)

---

## 0. 前置约定

- DDD 四层依赖方向与事务约定见[设计架构](architecture.md)——违反会被评审打回；
- DTO 字段用 camelCase（前端契约，ruff 对 dto 目录豁免 N815）；
- 错误消息统一进 `domain/error_messages.py`（EM），禁止内联 f-string 散落。

## 1. 领域层（domain/）

| 步骤 | 文件 | 内容 |
|---|---|---|
| 1 | `entities/<m>.py` | 实体类：字段 + `create_new` 工厂 + `update_info`（None=不更新的条件式更新） |
| 2 | `repositories/<m>_repository.py` | 仓储接口 ABC：get_by_id / get_all(分页+过滤) / count / create / update / delete / batch_delete |
| 3 | `error_messages.py` | EM 追加 `<m>_not_found_by_id` / `<m>_xxx_exists` 参数化方法 |

## 2. 基础设施层（infrastructure/）

| 步骤 | 文件 | 内容 |
|---|---|---|
| 4 | `database/models/<m>.py` | SQLModel 表模型：`to_domain()` / `from_domain()` 手写映射 |
| 4a | `database/models/__init__.py` | 注册导出（漏了 conftest 建表会缺表） |
| 5 | Alembic 迁移 | `alembic revision --autogenerate -m "add <m>"` → 检查 → `upgrade head` |
| 6 | `repositories/<m>_repository.py` | 继承 `GenericRepository[Model, Entity]` + 实现接口；**update 建议用 `_build_update_values` + sa_update 模式**（参照 post_repository，避免基类 merge 丢字段坑） |

## 3. 应用层（application/）

| 步骤 | 文件 | 内容 |
|---|---|---|
| 7 | `dto/<m>_dto.py` | Create/Update/Response/ListQuery DTO；ListQuery 继承 `BaseListQueryDTO`（分页勿手抄）；校验规则写进 DTO（Field/validator） |
| 8 | `services/<m>_service.py` | 用例：查重 → 实体操作 → 仓储落库 → **`_to_response` 统一转换**（转换只发生在 service 尾部，router 只做 model_dump） |

## 4. 接口层（api/）

| 步骤 | 文件 | 内容 |
|---|---|---|
| 9 | `dependencies/<m>_service.py` | 工厂：`Depends(get_db)` 取 session → 仓储 → 服务；多仓储务必复用同一 db |
| 9a | `dependencies/__init__.py` | 导出工厂 |
| 10 | `v1/<m>_router.py` | Routable 类：`@post("")` 列表 / `@post("/create")` / `@put("/{id}")` / `@delete("/{id}")` / `@post("/batch-delete")`；权限依赖 `require_permission("<m>:xxx")` |
| 10a | `v1/__init__.py` | 注册路由 + prefix |

## 5. 菜单与权限

- 菜单管理页（或 `rbac_defaults.py`）新增页面节点 + 按钮权限节点（`<m>:view/add/edit/delete`）；
- 重跑 `seedrbac`（或页面配置）并给角色勾选；详见 [RBAC](../features/rbac.md#5-二次开发新增一个权限码)。

## 6. 测试（与代码同提交）

| 测试 | 位置 | 要点 |
|---|---|---|
| Service 单测 | `tests/unit/application/test_<m>_service.py` | mock 仓储（AsyncMock 或 fakes.py）；覆盖查重冲突/不存在/正常路径 |
| DTO 单测 | `tests/unit/application/dto/test_<m>_dto.py` | 校验边界（必填/长度/值域） |
| Router 单测 | `tests/unit/api/v1/test_<m>_router.py` | 依赖覆盖 + 权限 403/404 分支 |
| 集成用例 | `tests/integration/test_<m>_flow.py` | 真实 DB 全链路（登录→增→查→改→删） |

## 7. 前端（见[前端开发指南](frontend-guide.md)）

新增 `api/system/<m>.ts`（继承 BaseApi）+ `views/system/<m>/`（组合 useCrudTable/useDialogForm）
+ 菜单管理页配置页面菜单与按钮权限。

## 8. 提交前自检

```bash
ruff check src/ tests/ && python -m mypy src/
pytest tests/unit/ && pytest tests/integration/
# 前端（如有改动）
pnpm lint && pnpm typecheck && pnpm test:unit
```

全绿才允许提交（AGENTS.md 协作规范）。
