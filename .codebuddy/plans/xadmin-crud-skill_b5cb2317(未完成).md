---
name: xadmin-crud-skill
overview: 创建一个 CodeBuddy Skill，输入 MySQL 数据表定义后，自动生成后端 Django（Model + Serializer + ViewSet + Filter + URL + Config + Apps）和前端 Vue 3（API + Hook + Index 页面）的完整 CRUD 代码。
todos:
  - id: skill-config-naming
    content: 创建 skill_crud/config.py 和 skill_crud/naming.py，定义默认配置和命名转换工具
    status: pending
  - id: skill-parser-mapper
    content: 创建 skill_crud/parser.py 和 skill_crud/mapper.py，实现 MySQL DDL 解析和类型映射
    status: pending
    dependencies:
      - skill-config-naming
  - id: skill-generator
    content: 创建 skill_crud/generator.py，实现后端（Model/Serializer/ViewSet/Filter/URL/Config）和前端（API/Vue/Hook）代码生成
    status: pending
    dependencies:
      - skill-parser-mapper
  - id: skill-file-manager
    content: 创建 skill_crud/file_manager.py，实现文件创建/追加/检测逻辑
    status: pending
  - id: skill-main-cli
    content: 创建 skill_crud/__main__.py 和 __init__.py，实现 CLI 入口和主流程编排
    status: pending
    dependencies:
      - skill-generator
      - skill-file-manager
  - id: skill-verify
    content: 验证完整 skill 流程，使用 demo DDL 测试生成结果是否符合项目规范
    status: pending
    dependencies:
      - skill-main-cli
---

## 产品概述

开发一个 CRUD 代码生成器 Skill，输入 MySQL 数据表 DDL 定义或指定数据表名，自动生成完整的后端（Django + DRF）和前端（Vue 3 + RePlusPage）CRUD 代码。

## 核心功能

- 解析 MySQL CREATE TABLE DDL 语句，提取表名、字段、类型、约束、注释等信息
- 支持通过数据库连接读取指定表结构（INFORMATION_SCHEMA）
- 将 MySQL 字段类型映射为 Django Model 字段类型
- 后端生成：Django Model、DRF Serializer、ViewSet + FilterSet、URL 路由、App 配置
- 前端生成：API 类、Vue 页面组件、Hook 逻辑文件
- 支持指定已有 app 目录追加代码，或自动创建新 app
- 遵循"一个类一个文件"原则，已有目录则按表名创建 py/ts 文件追加
- 自动跳过 DbAuditModel 基类已有的字段（created_time, creator, modifier 等）
- ForeignKey 自动识别并生成关联字段及 extra_kwargs 配置

## 技术栈

- 语言：Python 3.10+
- MySQL 解析：正则表达式 + sqlparse 库（可选）
- 数据库读取：pymysql / mysqlclient（可选，用于从现有数据库读取表结构）
- 代码生成：Python f-string 模板
- 前端输出：TypeScript + Vue 3 SFC

## 实现方案

### 整体架构

Skill 作为一个独立的 Python 包 `skill_crud`，通过 CLI 运行。核心流程：

```
输入(MySQL DDL 或表名) → 解析器(提取表结构元数据) → 类型映射(MySQL→Django) → 代码生成器(后端+前端) → 文件管理器(创建/追加文件)
```

### 关键设计决策

1. **DDL 解析策略**：使用正则表达式解析 CREATE TABLE 语句，提取列定义、约束、注释。对于复杂场景，可选集成 sqlparse 库。优先支持标准 MySQL DDL 语法。

2. **类型映射表**（MySQL → Django）：

- TINYINT(1) → BooleanField；TINYINT → SmallIntegerField
- SMALLINT → SmallIntegerField；INT/INTEGER → IntegerField；BIGINT → BigIntegerField
- FLOAT → FloatField；DOUBLE → FloatField；DECIMAL → DecimalField
- CHAR/VARCHAR → CharField(max_length=N)；TEXT/MEDIUMTEXT/LONGTEXT → TextField
- DATE → DateField；DATETIME/TIMESTAMP → DateTimeField；TIME → TimeField
- BLOB → BinaryField；ENUM → CharField + choices

3. **基类选择**：默认使用 `DbAuditModel`（含 created_time, updated_time, description, creator, modifier, dept_belong），自动跳过这些重复字段。

4. **文件追加策略**：

- 新 app：创建完整目录结构（models/, serializers/, views/, filters/），每个类一个文件
- 已有 app：检测目录是否存在，存在则按表名创建新文件追加，不存在则创建目录
- urls.py：追加 router.register 行
- models/**init**.py：追加 import 行

5. **前端最小化**：利用 RePlusPage 组件 + 后端 search-columns/search-fields 接口自动渲染，前端只生成 API 类、页面组件和基础 hook。

### 核心数据结构

```python
@dataclass
class ColumnMeta:
    name: str                    # 列名
    db_type: str                 # MySQL 类型
    django_type: str             # Django 字段类名
    django_kwargs: dict          # Django 字段参数 {max_length, null, default, ...}
    verbose_name: str            # 中文注释/verbose_name
    is_primary_key: bool
    is_foreign_key: bool
    fk_ref_table: str | None     # 外键引用表
    fk_ref_column: str | None    # 外键引用列
    is_unique: bool
    is_indexed: bool
    choices: list | None         # ENUM 值列表
    skip: bool                   # 是否跳过(DbAuditModel已有)

@dataclass
class TableMeta:
    table_name: str              # MySQL 表名
    app_name: str                # Django app 名称
    model_name: str              # Django 模型类名
    model_name_lower: str        # 模型类名小写
    verbose_name: str            # 表注释
    columns: list[ColumnMeta]    # 列元数据列表
    base_model: str              # 基类名 (默认 DbAuditModel)
    is_new_app: bool             # 是否新建 app
```

### 代码生成模板（参考现有项目模式）

**Model 生成**：参考 `demo/models.py` 和 `system/models/department.py` 模式
**Serializer 生成**：参考 `demo/serializers/book.py` 模式，自动生成 fields、table_fields、extra_kwargs
**ViewSet 生成**：参考 `system/views/admin/dept.py` 模式（BaseModelSet + ImportExportDataAction）
**FilterSet 生成**：参考 `DeptFilter` 模式，字符串字段用 icontains，其他用精确匹配
**URL 生成**：参考 `demo/urls.py` 的 SimpleRouter 模式
**前端 API**：参考 `api/system/dept.ts` 的 BaseApi 继承模式
**前端页面**：参考 `views/demo/book/index.vue` 的 RePlusPage 模式
**前端 Hook**：参考 `views/demo/book/utils/hook.tsx` 的 useXxx 函数模式

## 目录结构

```
skill_crud/
├── __init__.py           # [NEW] 包初始化，导出主要类
├── __main__.py           # [NEW] CLI 入口，参数解析，主流程编排
├── parser.py             # [NEW] MySQL DDL 解析器，提取表/列元数据；支持 DB 连接读取
├── mapper.py             # [NEW] MySQL→Django 类型映射，字段参数转换
├── generator.py          # [NEW] 后端+前端代码生成器，基于 TableMeta 生成所有文件内容
├── file_manager.py       # [NEW] 文件管理器，处理创建/追加逻辑，检测已有目录和文件
├── naming.py             # [NEW] 命名转换工具，snake_case/PascalCase/camelCase 互转
└── config.py             # [NEW] 默认配置，基类映射，跳过字段列表，项目路径常量
```

## 实现要点

1. **DDL 解析**：使用正则逐行匹配列定义 `column_name TYPE [(size)] [UNSIGNED] [NULL|NOT NULL] [DEFAULT value] [AUTO_INCREMENT] [COMMENT 'xxx']`，以及 CONSTRAINT 行（PRIMARY KEY, FOREIGN KEY, UNIQUE KEY, KEY）

2. **ForeignKey 处理**：检测 FOREIGN KEY 约束，生成 `models.ForeignKey(to='app.ModelName', ...)` 并在 serializer 的 extra_kwargs 中添加 `attrs`、`format` 配置

3. **skip 字段检测**：对比列名与 DbAuditModel 已有字段（id, created_time, updated_time, description, creator_id, modifier_id, dept_belong_id），匹配则标记 skip=True

4. **追加模式**：读取已有文件内容，在合适位置插入新代码。models/**init**.py 追加 `from .xxx import *`，urls.py 追加 `router.register(...)` 行

5. **前端 locale-name 生成**：app 名 + 表名驼峰化，如 demo + book → "demoBook"，system + dept → "systemDept"

6. **错误处理**：DDL 解析失败时给出明确提示，文件写入前检查目标路径是否存在并备份

## Agent Extensions

### Skill

- **python-code-quality**: 编写 skill_crud 包的所有 Python 代码时，确保使用面向对象编程，函数入参和返回值使用类型注解，遵循 SOLID 原则和 Python 3.10+ 最佳实践
- **skill-creator**: 指导 skill 的结构和设计，确保 skill 符合最佳实践规范