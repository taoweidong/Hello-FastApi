# MySQL → Django 类型映射表

> 本文件为通用的类型映射规则。项目特定的基类已有字段列表见 `project-config.md`。

## 字段类型映射

| MySQL 类型 | Django 字段类型 | 说明 |
|------------|----------------|------|
| `INT` / `INTEGER` | `models.IntegerField` | 普通整数 |
| `TINYINT` | `models.SmallIntegerField` | 小整数，常用于布尔或枚举 |
| `TINYINT(1)` | `models.BooleanField` | 布尔值（MySQL 中 TINYINT(1) 常表示布尔） |
| `SMALLINT` | `models.SmallIntegerField` | 小整数 |
| `MEDIUMINT` | `models.IntegerField` | 中等整数 |
| `BIGINT` | `models.BigIntegerField` | 大整数 |
| `FLOAT` | `models.FloatField` | 单精度浮点 |
| `DOUBLE` / `DOUBLE PRECISION` | `models.FloatField` | 双精度浮点 |
| `DECIMAL(p,s)` / `NUMERIC(p,s)` | `models.DecimalField(max_digits=p, decimal_places=s)` | 精确小数 |
| `CHAR(n)` | `models.CharField(max_length=n)` | 定长字符串 |
| `VARCHAR(n)` | `models.CharField(max_length=n)` | 变长字符串 |
| `TEXT` | `models.TextField` | 长文本 |
| `MEDIUMTEXT` | `models.TextField` | 中等文本 |
| `LONGTEXT` | `models.TextField` | 超长文本 |
| `DATE` | `models.DateField` | 日期 |
| `TIME` | `models.TimeField` | 时间 |
| `DATETIME` | `models.DateTimeField` | 日期时间 |
| `TIMESTAMP` | `models.DateTimeField` | 时间戳 |
| `YEAR` | `models.IntegerField` | 年份 |
| `BOOLEAN` / `BOOL` | `models.BooleanField` | 布尔值 |
| `JSON` | `models.JSONField` | JSON 数据 |
| `BLOB` | `models.BinaryField` | 二进制数据 |
| `ENUM` | `models.CharField` + `choices` | 枚举（用 choices 实现） |
| `SET` | `models.JSONField` 或 `models.CharField` | 集合（需自定义） |

## 字段参数转换规则

| MySQL 约束/属性 | Django 参数 | 说明 |
|-----------------|------------|------|
| `NOT NULL` | 默认行为（不添加 null=True） | Django 默认 null=False |
| `NULL` | `null=True` | 允许数据库为 NULL |
| `DEFAULT value` | `default=value` | 默认值 |
| `COMMENT 'xxx'` | `verbose_name="xxx"` | 字段注释转为 verbose_name |
| `UNIQUE` | `unique=True` | 唯一约束 |
| `AUTO_INCREMENT` | 跳过（基类有主键） | 见 project-config.md 中的基类字段 |
| `PRIMARY KEY` | 跳过（基类有主键） | 见 project-config.md 中的基类字段 |
| `ON UPDATE CURRENT_TIMESTAMP` | 不需要 | 由框架的 auto_now 处理 |

## 默认值转换

| MySQL 默认值 | Django default | 说明 |
|-------------|----------------|------|
| `DEFAULT NULL` | `null=True, blank=True` | 允许为空 |
| `DEFAULT 0` | `default=0` | 数字零 |
| `DEFAULT ''` | `default=''` | 空字符串 |
| `DEFAULT FALSE` / `DEFAULT 0` (TINYINT(1)) | `default=False` | 布尔假 |
| `DEFAULT TRUE` / `DEFAULT 1` (TINYINT(1)) | `default=True` | 布尔真 |
| `DEFAULT CURRENT_TIMESTAMP` | `default=timezone.now` | 当前时间（需 `from django.utils import timezone`） |
| `DEFAULT 'xxx'` | `default='xxx'` | 字符串默认值 |

## ForeignKey 识别规则

```sql
-- 模式1：字段名以 _id 结尾
`user_id` INT NOT NULL COMMENT '用户ID'
-- → 去除 _id 后缀作为字段名，推断关联模型

-- 模式2：显式 REFERENCES
`dept_id` INT REFERENCES department(id) COMMENT '部门'
-- → 去除 _id 后缀，按 REFERENCES 指定关联表
```

**规则**：
- 字段名去除 `_id` 后缀作为 Django 字段名
- `to` 参数需要推断关联模型（见 project-config.md 中的系统内置模型）
- `related_name` 格式：`{表名}_{字段名}`（避免冲突）
- `on_delete` 默认 `models.CASCADE`，允许 NULL 时用 `models.SET_NULL`

## ManyToManyField 识别规则

```sql
-- 关联表模式
CREATE TABLE book_tags (book_id INT, tag_id INT, ...);
-- → 识别为主模型中的 ManyToManyField
```

## 命名转换规则

### MySQL 表名 → Model 类名

| MySQL 表名 | Model 类名 | 规则 |
|-----------|------------|------|
| `book` | `Book` | snake_case → PascalCase |
| `book_info` | `BookInfo` | snake_case → PascalCase |
| `sys_user_role` | `SysUserRole` | snake_case → PascalCase |
| `t_order_detail` | `OrderDetail` | 去除常见前缀后 PascalCase |

**常见表名前缀**（生成 Model 类名时去除）：`t_`、`tb_`、`tbl_`
