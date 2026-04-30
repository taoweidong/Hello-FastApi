#!/bin/bash
# deploy.sh - Jenkins 部署辅助脚本
# 用法: ./deploy.sh <environment> <registry> <app_name> <image_tag>

set -e

ENVIRONMENT="${1:-dev}"
REGISTRY="${2:-registry.example.com}"
APP_NAME="${3:-hello-fastapi}"
IMAGE_TAG="${4:-latest}"

echo "============================================"
echo "部署 Hello-FastApi 到 ${ENVIRONMENT} 环境"
echo "镜像: ${REGISTRY}/${APP_NAME}:${IMAGE_TAG}"
echo "============================================"

# 根据环境执行不同部署策略
deploy_dev() {
    echo "部署到开发环境 (docker-compose)..."
    cd "$(dirname "$0")/.."
    
    # 停止旧服务
    docker compose down || true
    
    # 拉取新镜像并启动
    docker compose pull || true
    docker compose up -d
    
    # 等待服务就绪
    echo "等待服务启动..."
    sleep 10
    
    # 健康检查
    for i in {1..30}; do
        if curl -sf http://localhost:8000/health > /dev/null 2>&1; then
            echo "服务已就绪!"
            exit 0
        fi
        echo "等待中... (${i}/30)"
        sleep 2
    done
    
    echo "警告: 服务可能未完全启动，请手动检查"
    exit 1
}

deploy_staging() {
    echo "部署到预发布环境..."
    echo "通过 SSH 连接到预发布服务器执行部署"
    echo "请配置 staging 服务器的 SSH 部署"
}

deploy_prod() {
    echo "部署到生产环境..."
    echo "通过 SSH 连接到生产服务器执行滚动部署"
    echo "请配置 production 服务器的部署策略"
}

case "${ENVIRONMENT}" in
    dev)
        deploy_dev
        ;;
    staging)
        deploy_staging
        ;;
    prod)
        deploy_prod
        ;;
    *)
        echo "未知环境: ${ENVIRONMENT}"
        exit 1
        ;;
esac
