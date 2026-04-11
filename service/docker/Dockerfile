# FastAPI 生产环境 Dockerfile
# 多阶段构建：builder 安装依赖 → runner 仅保留运行时

# ── 构建阶段 ──
FROM python:3.10-slim AS builder

WORKDIR /app

# 安装 UV 包管理器
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# 先复制依赖文件，利用 Docker 缓存
COPY pyproject.toml uv.lock ./

# 仅安装生产依赖（锁定版本，不装可编辑模式）
RUN uv pip install --system --no-dev -r pyproject.toml

# ── 运行阶段 ──
FROM python:3.10-slim AS runner

WORKDIR /app

# 创建非 root 用户
RUN groupadd -r appgroup && useradd -r -g appgroup appuser

# 从构建阶段复制已安装的包
COPY --from=builder /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# 复制源代码
COPY --chown=appuser:appgroup . .

# 创建日志目录并赋权
RUN mkdir -p logs && chown appuser:appgroup logs

# 切换到非 root 用户
USER appuser

# 环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# 暴露端口
EXPOSE 8000

# 健康检查 - 使用 Python 内置 urllib，无需额外依赖
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "from urllib.request import urlopen; urlopen('http://localhost:8000/health')" || exit 1

# 启动命令 - 生产环境多 worker
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
