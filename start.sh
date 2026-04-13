#!/bin/bash
# Budget System Startup Script

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# Clean up old processes
pm2 delete budget-api budget-web 2>/dev/null

# Start both services using ecosystem config
pm2 start "$SCRIPT_DIR/ecosystem.config.js"

pm2 save

echo "Budget System services started:"
pm2 list
