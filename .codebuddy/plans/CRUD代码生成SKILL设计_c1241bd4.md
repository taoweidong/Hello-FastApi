---
name: CRUD代码生成SKILL设计
overview: 设计并开发一个CRUD代码生成SKILL，输入数据库表结构，自动生成符合当前项目DDD架构的后端代码（ORM模型、仓储接口/实现、应用服务、DTO、API路由、依赖注入、单元测试）和前端代码（API类、类型定义、页面组件、表单组件、Hook逻辑），并通过测试验证正确性。
todos:
  - id: create-skill-definition
    content: 使用 [skill:skill-creator] 创建 CRUD 代码生成 SKILL 定义文件 .codebuddy/skills/crud-generator.md，包含完整的后端各层代码模板、前端各层代码模板、模块注册规范和验证清单
    status: completed
  - id: backend-templates
    content: 基于 Dictionary 模块提炼后端 DDD 各层代码模板（ORM/Entity/Repository/DTO/Service/Router/Dependency），提取变量占位符和条件逻辑（分页vs树形）
    status: completed
    dependencies:
      - create-skill-definition
  - id: frontend-templates
    content: 基于 Role/Dept 模块提炼前端各层代码模板（API/Hook/Form/Index/Types/Rule），提取变量占位符和字段类型到组件的映射规则
    status: completed
    dependencies:
      - create-skill-definition
  - id: test-template
    content: 使用 [skill:python-testing-patterns] 制定单元测试模板，包含 Mock 仓储 fixture、CRUD 成功/失败场景覆盖
    status: completed
    dependencies:
      - backend-templates
  - id: validation-checklist
    content: 制定验证清单：后端单元测试通过、前端编译无错误、前后端联调验证（使用 [mcp:Playwright MCP Server]）
    status: completed
    dependencies:
      - backend-templates
      - frontend-templates
---

## 产品概述

开发一个 SKILL（代码生成技能），能够根据给定的数据库表结构，自动遵循当前系统的 DDD 分层架构和前端组件模式，生成完整的前后端 CRUD 代码，并通过单元测试和前后端联调验证正确性。

## 核心功能

- **表结构解析**：接收数据库表结构定义（字段名、类型、约束、注释等），自动识别主键、状态字段、时间字段、外键关系、树形结构等模式
- **后端代码生成**：按照 DDD 分层（ORM模型→领域实体→仓储接口→仓储实现→DTO→应用服务→API路由→依赖注入→模块注册）自动生成完整的后端代码
- **单元测试生成**：基于应用服务层生成 Mock 仓储的单元测试，覆盖 CRUD 成功/失败场景
- **前端代码生成**：按照项目约定（API类→视图Hook→表单→表格→类型定义→校验规则）生成完整的前端 CRUD 页面
- **联调验证**：通过 Playwright 浏览器自动化验证前后端集成功能

## 技术栈

- 后端：FastAPI + SQLModel + FastCRUD + classy_fastapi + Pydantic
- 前端：Vue3 + TypeScript + Element Plus + PureTableBar + ReDialog
- 测试：pytest + pytest-asyncio + unittest.mock（后端）；Playwright MCP（前端联调）
- 代码质量：[skill:python-code-quality] 确保后端代码符合 Python 最佳实践

## 实现方案

### 核心策略

创建一个 SKILL 定义文件（`.codebuddy/skills/crud-generator.md`），该文件包含：

1. 完整的代码生成规范（基于对现有代码的模式提取）
2. 每层代码模板（含变量占位符，根据表结构填充）
3. 验证清单和测试模板

### 代码生成流水线

给定表结构后，按以下顺序生成代码：

```
表结构 → ORM Model → Domain Entity → Repository Interface → Repository Impl
       → DTO (Create/Update/Query/Response) → Application Service
       → API Router → Dependency Factory → Module Registration (__init__.py)
       → Unit Tests → Frontend API → Frontend View (hook/form/index/types/rule)
       → 联调验证
```

### 关键技术决策

1. **以 Dictionary 模块为参考蓝本**：Dictionary 是最新的模块，代码模式最完整且包含树形结构处理，比 Role/User 等老模块更通用
2. **区分分页列表 vs 树形列表**：通过表结构中是否有 `parent_id` 字段自动判断
3. **字段类型映射**：`str→el-input`，`int→el-input-number`，`datetime→日期格式化`，`is_active→el-switch`，`parent_id→el-cascader`，`description→el-input type=textarea`
4. **API路径约定**：列表用 `POST /{prefix}`，创建用 `POST /{prefix}/create`，更新用 `PUT /{prefix}/{id}`，删除用 `DELETE /{prefix}/{id}`
5. **表名前缀**：所有表名使用 `sys_` 前缀，主键为32位UUID字符串

### 后端各层生成规范

#### ORM 模型层 (`infrastructure/database/models/{name}.py`)

- 继承 `SQLModel, table=True`
- 主键: `id: str = Field(default_factory=lambda: uuid.uuid4().hex, primary_key=True, max_length=32)`
- 时间字段: `created_time/updated_time` 使用 `sa_column=Column(DateTime(6), server_default=func.now())`
- 状态字段: `is_active: int = Field(default=1)`
- 包含 `to_domain()` 和 `from_domain()` 转换方法
- 注意: 不使用 `from __future__ import annotations`

#### 领域实体层 (`domain/entities/{name}.py`)

- `@dataclass` 装饰器
- 纯 Python 数据类，无 ORM 依赖
- 命名: `{Name}Entity`

#### 仓储接口层 (`domain/repositories/{name}_repository.py`)

- `ABC` + `@abstractmethod`
- 命名: `{Name}RepositoryInterface`
- 使用 `TYPE_CHECKING` 避免循环导入
- 标准方法: `get_by_id`, `get_all`, `count`, `create`, `update`, `delete`
- 树形模式追加: `get_by_parent_id`, `get_max_sort`

#### 仓储实现层 (`infrastructure/repositories/{name}_repository.py`)

- 继承 `RepositoryInterface`
- 使用 `FastCRUD(Model)` 封装为 `self._crud`
- 构造函数注入 `AsyncSession`
- update 使用 `sqlalchemy update` 语句
- delete 使用 `sqlalchemy delete` 语句

#### DTO 层 (`application/dto/{name}_dto.py`)

- `Pydantic BaseModel`
- Create: 必填字段校验 + `field_validator` 空值处理
- Update: 所有字段 Optional + `field_validator`
- Response: 完整字段 + `model_config = {"from_attributes": True}`
- Query: `pageNum/pageSize` 分页参数 + 筛选字段
- 使用 `validators.py` 工具: `empty_str_to_none`, `normalize_optional_id`

#### 应用服务层 (`application/services/{name}_service.py`)

- 命名: `{Name}Service`
- 构造函数注入 `AsyncSession` + `RepositoryInterface`
- CRUD 方法 + 业务校验（重名检查、存在性检查）
- `_to_response()` 静态方法做模型→DTO转换

#### API路由层 (`api/v1/{name}_router.py`)

- `classy_fastapi.Routable` 类风格
- 命名: `{Name}Router`
- 权限依赖: `require_permission("{name}:view")`, `require_permission("{name}:manage")`
- 使用 `success_response` / `list_response` 统一响应

#### 依赖注入层 (`api/dependencies/{name}_service.py`)

- `get_{name}_service` 工厂函数
- `Depends(get_db)` 获取数据库会话
- 创建 `Repository` 实例并注入 `Service`

#### 模块注册

- `models/__init__.py` 追加导出
- `repositories/__init__.py` 追加导出
- `infrastructure/repositories/__init__.py` 追加导出
- `services/__init__.py` 追加导出
- `dependencies/__init__.py` 追加导出
- `api/v1/__init__.py` 追加路由注册
- `domain/__init__.py` 追加实体导出

### 前端各层生成规范

#### API层 (`api/system/{name}.ts`)

- 继承 `BaseApi`，构造函数传 `prefix`
- 树形模块覆写 `list` 方法为不分页
- 单例导出: `export const xxxApi = new XxxApi()`

#### 兼容层 (`api/system.ts`)

- 追加函数式重新导出

#### 类型定义 (`views/system/{name}/utils/types.ts`)

- `FormItemProps` + `FormProps` 接口

#### 校验规则 (`views/system/{name}/utils/rule.ts`)

- `reactive<FormRules>` 必填字段校验

#### 核心 Hook (`views/system/{name}/utils/hook.tsx`)

- `use{Name}()` 函数
- `form` reactive 搜索表单
- `columns` 表格列定义（含 `cellRenderer` 状态开关、时间格式化）
- `onSearch/resetForm/openDialog/handleDelete` 方法
- `addDialog` 弹框集成
- 分页: `PaginationProps`（分页模式）/ 树形: `handleTree`（树形模式）

#### 表单组件 (`views/system/{name}/form.vue`)

- `<script setup lang="ts">` + `defineProps<FormProps>`
- `el-form` + `el-form-item` 表单字段
- `defineExpose({ getRef })` 暴露验证方法

#### 主页面 (`views/system/{name}/index.vue`)

- `<script setup lang="ts">` + `defineOptions`
- 搜索表单 + `PureTableBar` + `pure-table`
- 从 hook 解构状态和方法

### 单元测试规范

- 文件: `tests/unit/test_{name}_service.py`
- 使用 `AsyncMock` 模拟仓储和会话
- pytest class 风格: `class Test{Name}Service`
- 覆盖: 创建成功、创建重复、获取不存在、更新成功、删除成功、删除不存在

### 联调验证

使用 [mcp:Playwright MCP Server] 进行浏览器自动化:

1. 启动前端页面
2. 登录系统
3. 导航到新模块页面
4. 测试列表加载、搜索、新增、编辑、删除操作
5. 验证页面响应和数据一致性

## 目录结构

### SKILL 定义文件

```
e:/GitHub/Hello-FastApi/.codebuddy/skills/
└── crud-generator.md    # [NEW] CRUD代码生成SKILL定义文件，包含完整的代码模板、生成规范、验证清单
```

### 生成目标文件（以示例模块 {name} 为例）

#### 后端文件

```
service/src/
├── infrastructure/database/models/{name}.py           # [NEW] ORM模型，含to_domain/from_domain
├── domain/entities/{name}.py                          # [NEW] 领域实体，@dataclass
├── domain/repositories/{name}_repository.py            # [NEW] 仓储接口，ABC+abstractmethod
├── infrastructure/repositories/{name}_repository.py    # [NEW] 仓储实现，FastCRUD
├── application/dto/{name}_dto.py                      # [NEW] DTO，Create/Update/Query/Response
├── application/services/{name}_service.py             # [NEW] 应用服务，业务逻辑编排
├── api/v1/{name}_router.py                            # [NEW] API路由，classy_fastapi.Routable
├── api/dependencies/{name}_service.py                 # [NEW] 依赖注入工厂
├── tests/unit/test_{name}_service.py                  # [NEW] 单元测试
├── infrastructure/database/models/__init__.py         # [MODIFY] 追加模型导出
├── domain/repositories/__init__.py                    # [MODIFY] 追加仓储接口导出
├── infrastructure/repositories/__init__.py            # [MODIFY] 追加仓储实现导出
├── application/services/__init__.py                   # [MODIFY] 追加服务导出
├── domain/entities/__init__.py                        # [MODIFY] 追加实体导出
├── domain/__init__.py                                 # [MODIFY] 追加实体和仓储接口导出
├── api/dependencies/__init__.py                       # [MODIFY] 追加依赖工厂导出
└── api/v1/__init__.py                                 # [MODIFY] 追加路由注册
```

#### 前端文件

```
web/src/
├── api/system/{name}.ts                               # [NEW] API调用类，继承BaseApi
├── api/system.ts                                      # [MODIFY] 追加兼容层导出
├── views/system/{name}/index.vue                      # [NEW] 主页面，搜索+表格
├── views/system/{name}/form.vue                       # [NEW] 表单组件，新增/编辑对话框
├── views/system/{name}/utils/hook.tsx                 # [NEW] 核心Hook，状态+逻辑
├── views/system/{name}/utils/types.ts                 # [NEW] TypeScript类型定义
└── views/system/{name}/utils/rule.ts                  # [NEW] 表单校验规则
```

## 实施注意事项

- 生成代码时严格遵循 Dictionary 模块的代码风格（最新、最通用）
- `__init__.py` 文件修改时需保持原有导出顺序和格式
- 所有中文注释，与项目约定一致
- DTO 字段命名使用 camelCase（前端约定），Python 内部使用 snake_case
- 时间字段统一使用 `DateTime(6)` 精度
- 树形结构通过 `parent_id` 字段自动识别，影响列表查询方式和前端展示
- 单元测试必须通过 `pytest tests/unit/test_{name}_service.py` 验证
- 前后端联调需确保后端服务(`localhost:8000`)和前端服务(`localhost:8848`)同时运行

## Skill

- **skill-creator**: 用于创建 CRUD 代码生成 SKILL 的定义文件。将分析出的代码模式、模板和规范写入 `.codebuddy/skills/crud-generator.md`，使 SKILL 可被后续调用
- **python-code-quality**: 确保生成的后端 Python 代码符合 SOLID 原则、类型注解规范和现代 Python 最佳实践，用于代码生成后的质量校验
- **python-testing-patterns**: 指导生成符合 pytest 最佳实践的单元测试，包括 Mock 模式、fixture 设计和异步测试规范

## MCP

- **Playwright MCP Server**: 用于前后端联调验证。通过浏览器自动化登录系统、导航到新模块页面、执行 CRUD 操作，验证前后端集成功能是否正常工作。具体使用 `playwright_navigate` 访问页面、`playwright_screenshot` 截图验证、`playwright_click/fill` 执行交互操作

## SubAgent

- **code-explorer**: 在 SKILL 定义创建过程中，用于深入探索特定模块的代码模式，确保 SKILL 中的模板和规范与项目实际代码完全一致