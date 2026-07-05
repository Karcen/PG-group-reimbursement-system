#!/bin/bash
# ============================================================
# 实验室报销管理系统 — 一键启动脚本（Mac / Linux）
# 用法：./start.sh
#        双击 Finder 中的 start.command（改名后）
# ============================================================

set -e
cd "$(dirname "$0")"          # 切换到脚本所在目录（项目根目录）

BACKEND_PORT=8000
FRONTEND_PORT=5173
LOG_DIR="logs"
mkdir -p "$LOG_DIR"

# ─── 颜色输出 ──────────────────────────────────────────────
GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'
info()  { echo -e "${GREEN}[✓]${NC} $1"; }
warn()  { echo -e "${YELLOW}[!]${NC} $1"; }
error() { echo -e "${RED}[✗]${NC} $1"; }

echo ""
echo "  ██████╗ ███████╗██╗███╗   ███╗██████╗ "
echo "  ██╔══██╗██╔════╝██║████╗ ████║██╔══██╗"
echo "  ██████╔╝█████╗  ██║██╔████╔██║██████╔╝"
echo "  ██╔══██╗██╔══╝  ██║██║╚██╔╝██║██╔══██╗"
echo "  ██║  ██║███████╗██║██║ ╚═╝ ██║██████╔╝"
echo "  ╚═╝  ╚═╝╚══════╝╚═╝╚═╝     ╚═╝╚═════╝ "
echo "        实验室报销管理系统  v1.0"
echo ""

# ─── 停止残留进程 ──────────────────────────────────────────
pkill -f "uvicorn app.main:app" 2>/dev/null && warn "已停止旧的后端进程" || true
pkill -f "vite --host"          2>/dev/null && warn "已停止旧的前端进程" || true
sleep 1

# ─── 选择 Python 解释器 ────────────────────────────────────
PYTHON=""
if conda env list 2>/dev/null | grep -q "reimb"; then
    PYTHON="conda run -n reimb python"
    UVICORN="conda run -n reimb uvicorn"
    info "使用 conda 环境: reimb"
elif [ -f "backend/.venv/bin/python" ]; then
    PYTHON="backend/.venv/bin/python"
    UVICORN="backend/.venv/bin/uvicorn"
    info "使用 backend/.venv 虚拟环境"
else
    PYTHON="python3"
    UVICORN="python3 -m uvicorn"
    warn "未找到专用环境，使用系统 Python（可能缺少依赖）"
fi

# ─── 启动后端 ──────────────────────────────────────────────
echo ""
echo "⏳ 启动后端服务..."
cd backend
$UVICORN app.main:app --host 0.0.0.0 --port $BACKEND_PORT \
    > "../$LOG_DIR/backend.log" 2>&1 &
BACKEND_PID=$!
echo $BACKEND_PID > "../$LOG_DIR/backend.pid"
cd ..

# 等待后端就绪（最多20秒）
for i in $(seq 1 20); do
    if curl -s "http://localhost:$BACKEND_PORT/health" >/dev/null 2>&1; then
        info "后端就绪  http://localhost:$BACKEND_PORT"
        break
    fi
    if [ $i -eq 20 ]; then
        error "后端启动超时，请查看 $LOG_DIR/backend.log"
        exit 1
    fi
    sleep 1
done

# ─── 启动前端 ──────────────────────────────────────────────
echo ""
echo "⏳ 启动前端服务..."
cd frontend
npm run dev > "../$LOG_DIR/frontend.log" 2>&1 &
FRONTEND_PID=$!
echo $FRONTEND_PID > "../$LOG_DIR/frontend.pid"
cd ..

# 等待前端就绪（最多15秒）
for i in $(seq 1 15); do
    if curl -s "http://localhost:$FRONTEND_PORT" >/dev/null 2>&1; then
        info "前端就绪  http://localhost:$FRONTEND_PORT"
        break
    fi
    sleep 1
done

# ─── 完成 ──────────────────────────────────────────────────
echo ""
echo "═══════════════════════════════════════════"
echo "  ✅  系统已成功启动！"
echo ""
echo "  🌐  前端地址:    http://localhost:$FRONTEND_PORT"
echo "  📡  API 文档:    http://localhost:$BACKEND_PORT/docs"
echo ""
echo "  👤  管理员:    admin / Admin@123456"
echo "  👩‍🏫  示例教师:  teacher1 / Teacher@123456"
echo "  🎓  示例学生:  student1 / Student@123456"
echo ""
echo "  📄  日志目录:    logs/"
echo "  🛑  停止系统:    ./stop.sh"
echo "═══════════════════════════════════════════"
echo ""

# 自动打开浏览器（如果有 GUI）
if command -v open >/dev/null 2>&1; then
    sleep 1 && open "http://localhost:$FRONTEND_PORT" &
fi

# 保持脚本运行，Ctrl+C 退出并停止服务
trap 'echo ""; echo "正在停止服务..."; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit 0' INT
wait
