#!/bin/bash
# 实验室报销管理系统 — 停止脚本（Mac / Linux）
cd "$(dirname "$0")"
echo "正在停止服务..."
pkill -f "uvicorn app.main:app" 2>/dev/null && echo "✅ 后端已停止" || echo "后端未在运行"
pkill -f "vite --host"          2>/dev/null && echo "✅ 前端已停止" || echo "前端未在运行"
rm -f logs/backend.pid logs/frontend.pid
echo "完成。"
