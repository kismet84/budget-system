#!/bin/bash
# Budget System Stop Script
# Stops all budget-system pm2 processes

echo "Stopping Budget System services..."
pm2 delete budget-api
pm2 delete budget-web

echo ""
echo "All Budget System services stopped."
pm2 list
