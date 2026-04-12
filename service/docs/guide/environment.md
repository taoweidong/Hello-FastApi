# 环境配置

项目支持多环境配置，通过环境变量和 `.env` 文件管理不同运行环境的设置。

[← 返回首页](../../README.md)

---

## 环境类型

| 环境 | 配置文件 | 说明 |
|------|----------|------|
| development | `.env.development` | 开发环境，DEBUG=true，使用 SQLite |
| production | `.env.production` | 生产环境，DEBUG=false，使用 PostgreSQL |
| testing | `.env.testing` | 测试环境，使用内存数据库 |

环境通过 `APP_ENV` 环境变量切换，默认为 `development`。

---

## 切换环境

### Linux / Mac

```bash
export APP_ENV=production
python -m scripts.cli runserver
```

### Windows (PowerShell)

```powershell
$env:APP_ENV = "production"
python -m scripts.cli runserver
```

### Windows (CMD)

```cmd
set APP_ENV=production
python -m scripts.cli runserver
```

---

## 配置加载顺序

配置按以下优先级加载，高优先级覆盖低优先级：

```
系统环境变量 > .env.{APP_ENV} > .env > 默认值
```

即：系统环境变量的值优先级最高，`.env.{APP_ENV}` 文件次之，通用 `.env` 文件再次之，代码中的默认值优先级最低。

---

## 配置项说明

所有配置项定义在 `src/config/settings.py` 中，使用 Pydantic Settings 管理。以下为主要配置项：

### 应用基础

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `APP_ENV` | 运行环境 | `development` |
| `DEBUG` | 调试模式 | `True`（开发环境） |
| `APP_NAME` | 应用名称 | `Hello-FastApi` |
| `APP_VERSION` | 应用版本 | - |

### 数据库

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `DATABASE_URL` | 数据库连接字符串 | SQLite（开发环境） |
| `DATABASE_ECHO` | 是否打印 SQL 语句 | `False` |

开发环境默认使用 SQLite，连接字符串示例：
```
sqlite+aiosqlite:///./sql/dev.db
```

生产环境使用 PostgreSQL，连接字符串示例：
```
postgresql+asyncpg://user:password@localhost:5432/dbname
```

### Redis 缓存

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `REDIS_URL` | Redis 连接地址 | `redis://localhost:6379/0` |
| `REDIS_PASSWORD` | Redis 密码 | - |

### JWT 认证

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `SECRET_KEY` | JWT 签名密钥 | - |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access Token 过期时间（分钟） | `30` |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Refresh Token 过期时间（天） | `7` |
| `ALGORITHM` | JWT 加密算法 | `HS256` |

### 服务器

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `HOST` | 监听地址 | `0.0.0.0` |
| `PORT` | 监听端口 | `8000` |
| `WORKERS` | Worker 数量 | `1`（开发环境） |

### CORS 跨域

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `CORS_ORIGINS` | 允许的跨域来源 | `["*"]` |
| `CORS_ALLOW_CREDENTIALS` | 允许携带凭证 | `True` |

---

## 自定义配置

如需添加新的配置项，在 `src/config/settings.py` 中的 `Settings` 类添加字段即可：

```python
class Settings(BaseSettings):
    # 新增配置项
    MY_NEW_CONFIG: str = "default_value"
    
    model_config = SettingsConfigDict(...)
```

然后在对应的 `.env` 文件中设置值：

```bash
# .env.development
MY_NEW_CONFIG=dev_value
```
