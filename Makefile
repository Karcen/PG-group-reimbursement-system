# ============================================================
# 实验室报销管理系统 — Makefile
# 提供开发、构建、数据库迁移的快捷命令
# ============================================================

.PHONY: help dev build up down logs migrate init-db clean test lint

# 默认目标：显示帮助
help:
	@echo ""
	@echo "  实验室报销管理系统 — 快捷命令"
	@echo ""
	@echo "  开发模式（本地直接运行）"
	@echo "    make dev-backend    启动后端（热重载）"
	@echo "    make dev-frontend   启动前端（Vite dev server）"
	@echo ""
	@echo "  Docker"
	@echo "    make build          构建 Docker 镜像"
	@echo "    make up             启动所有服务"
	@echo "    make down           停止所有服务"
	@echo "    make logs           查看日志"
	@echo ""
	@echo "  数据库"
	@echo "    make migrate        执行数据库迁移"
	@echo "    make init-db        初始化数据（默认账号、系统配置）"
	@echo "    make new-migration  生成新的迁移文件（需指定 MSG=xxx）"
	@echo ""
	@echo "  测试"
	@echo "    make test           运行所有测试"
	@echo "    make lint           代码格式检查"
	@echo ""

# ─────────────────────────────────────────
# 本地开发
# ─────────────────────────────────────────
dev-backend:
	cd backend && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

dev-frontend:
	cd frontend && npm run dev

# ─────────────────────────────────────────
# Docker 操作
# ─────────────────────────────────────────
build:
	docker-compose build

up:
	mkdir -p data/database data/storage/original data/storage/ocr data/storage/preview data/storage/thumbnails data/logs
	docker-compose up -d

down:
	docker-compose down

logs:
	docker-compose logs -f

# ─────────────────────────────────────────
# 数据库操作
# ─────────────────────────────────────────
migrate:
	cd backend && alembic upgrade head

new-migration:
	cd backend && alembic revision --autogenerate -m "$(MSG)"

init-db:
	cd backend && python -m app.scripts.init_db

# ─────────────────────────────────────────
# 测试与代码质量
# ─────────────────────────────────────────
test:
	cd backend && pytest tests/ -v --cov=app --cov-report=html

lint:
	cd backend && ruff check app/ && mypy app/
	cd frontend && npm run lint

# ─────────────────────────────────────────
# 清理
# ─────────────────────────────────────────
clean:
	find backend -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find backend -type f -name "*.pyc" -delete 2>/dev/null || true
	cd frontend && rm -rf dist node_modules/.cache 2>/dev/null || true
