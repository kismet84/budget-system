#!/bin/bash
# Budget System 启动脚本
# 用法: ./start.sh        — 启动（重建 PM2 进程）
#       ./start.sh dev     — 监听代码变动自动重载（开发模式）

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

MODE="${1:-prod}"

if [ "$MODE" = "dev" ]; then
  echo "=== Development mode: watching for file changes ==="
fi

# 删除旧进程，重新创建
pm2 delete budget-api budget-frontend budget-web 2>/dev/null

# 启动
pm2 start "$SCRIPT_DIR/ecosystem.config.js"
pm2 save

echo ""
echo "=== Budget System ==="
pm2 list
echo ""
echo "API:      http://localhost:8001"
echo "Docs:     http://localhost:8001/docs"
echo "Frontend: http://localhost:5173"
echo ""
echo "重启: pm2 restart budget-api"
