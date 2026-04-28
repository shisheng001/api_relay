#!/bin/bash
# api_relay 阿里云 ECS 部署脚本
# 适用于 Ubuntu 20.04+ / Debian 11+

set -e

echo "=== 1. 更新系统 ==="
apt update && apt upgrade -y

echo "=== 2. 安装 Docker ==="
if command -v docker &> /dev/null; then
    echo "Docker 已安装，跳过"
else
    curl -fsSL https://get.docker.com | sh
    systemctl start docker
    systemctl enable docker
fi

echo "=== 3. 安装 Docker Compose ==="
if command -v docker-compose &> /dev/null; then
    echo "Docker Compose 已安装，跳过"
else
    curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
    ln -sf /usr/local/bin/docker-compose /usr/bin/docker-compose
fi

echo "=== 4. 创建项目目录 ==="
mkdir -p /opt/api_relay
cd /opt/api_relay

echo "=== 5. 下载项目文件 ==="
# 方式1: Git clone（如果已有仓库）
# git clone https://github.com/你的用户名/api_relay.git .

# 方式2: 上传文件（手动上传 docker-compose.yml 和相关文件到 /opt/api_relay）

echo "=== 6. 创建 docker-compose.yml ==="
cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  api_relay:
    build: .
    container_name: api_relay
    restart: always
    ports:
      - "8000:8000"
    environment:
      - PORT=8000
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    networks:
      - api_network

networks:
  api_network:
    driver: bridge
EOF

echo "=== 7. 创建必要的目录 ==="
mkdir -p /opt/api_relay/data /opt/api_relay/logs

echo "=== 8. 拉取并启动容器 ==="
docker-compose pull
docker-compose up -d --build

echo "=== 9. 检查状态 ==="
docker-compose ps
docker-compose logs --tail=20

echo ""
echo "=== 部署完成 ==="
echo "访问 http://你的服务器IP:8000"
echo ""
echo "常用命令："
echo "  查看日志: docker-compose logs -f"
echo "  重启服务: docker-compose restart"
echo "  停止服务: docker-compose down"
echo "  更新代码: docker-compose up -d --build"
