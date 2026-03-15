# FastAPI 生产环境 Dockerfile
# 使用多阶段构建优化镜像大小

# 构建阶段
FROM python:3.10-slim AS builder

WORKDIR /app

# 安装构建依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 安装 UV 包管理器
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:$PATH"

# 复制依赖文件
COPY pyproject.toml .

# 安装依赖
RUN uv pip install --system -e "."

# 运行阶段
FROM python:3.10-slim AS runner

WORKDIR /app

# 创建非 root 用户
RUN groupadd -r appgroup && useradd -r -g appgroup appuser

# 从构建阶段复制已安装的包
COPY --from=builder /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# 复制源代码
COPY --chown=appuser:appgroup . .

# 创建日志目录
RUN mkdir -p logs && chown -appuser:appgroup logs

# 切换到非 root 用户
USER appuser

# 环境变量
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# 暴露端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/health')" || exit 1

# 启动命令 - 使用 uvicorn 直接运行
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
