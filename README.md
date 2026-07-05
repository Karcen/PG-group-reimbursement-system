# 实验室报销管理系统

> 面向高校实验室的本地化 AI 辅助报销管理平台

## 系统简介

本系统是一套完全自托管的报销管理解决方案，专为高校实验室设计。
支持 PDF 上传、PaddleOCR 识别、Ollama 本地 AI 提取发票信息，内置完整的审批流、通知中心、审计日志和统计面板。

**核心特性：**

- 🔒 本地部署，数据不出内网
- 🤖 AI 自动识别发票信息（Ollama + Qwen3）
- 📄 PDF 多页多票据自动拆分
- ✅ 多级审批流，支持按项目配置审批人
- 🔔 站内通知中心
- 📊 多维度统计与 Excel/CSV/PDF 导出
- 🔍 重复发票自动查重
- 📝 完整审计日志（不可篡改）
- 🌓 深色 / 浅色模式
- 🌐 全中文界面

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端 | Python 3.12 · FastAPI · SQLAlchemy 2.x · Alembic · SQLite |
| 前端 | Vue 3 · TypeScript · Vite · Pinia · Element Plus |
| OCR  | PaddleOCR · PyMuPDF |
| AI   | Ollama（Qwen3 / DeepSeek） |
| 部署 | Docker Compose / 本地直接运行 |

## 快速开始

### 方式一：Docker Compose（推荐）

```bash
# 1. 克隆项目
git clone <repo-url>
cd reimbursement-system

# 2. 复制并修改环境变量
cp backend/.env.example backend/.env

# 3. 启动所有服务
docker-compose up -d

# 4. 初始化数据库（首次运行）
docker-compose exec backend alembic upgrade head
docker-compose exec backend python -m app.scripts.init_db

# 5. 访问系统
# 前端：http://localhost:5173
# API 文档：http://localhost:8000/docs
```

### 方式二：本地直接运行

#### 环境要求

- Python 3.12+
- Node.js 20+
- Ollama（已安装并运行，已拉取 qwen3 模型）

#### 后端启动

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# 按需修改 .env

alembic upgrade head
python -m app.scripts.init_db  # 初始化管理员账号

uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

#### 前端启动

```bash
cd frontend
npm install
npm run dev
```

## 默认账号

| 角色 | 用户名 | 密码 |
|------|--------|------|
| 管理员 | admin | Admin@123456 |
| 教师示例 | teacher1 | Teacher@123456 |
| 学生示例 | student1 | Student@123456 |

**首次使用请立即修改默认密码。**

## 目录结构

```
reimbursement-system/
├── backend/          # FastAPI 后端
│   ├── app/
│   │   ├── api/      # 路由层（RESTful 接口）
│   │   ├── core/     # 核心配置（config, database, security）
│   │   ├── models/   # SQLAlchemy ORM 模型
│   │   ├── schemas/  # Pydantic 数据校验模型
│   │   ├── services/ # 业务逻辑层
│   │   ├── repositories/ # 数据访问层
│   │   ├── ocr/      # OCR 识别模块
│   │   ├── ai/       # AI 提取模块（Ollama）
│   │   └── tasks/    # 后台任务（提醒、定时）
│   └── migrations/   # Alembic 数据库迁移
├── frontend/         # Vue 3 前端
├── storage/          # 文件存储
│   ├── original/     # 原始 PDF（永久保存，不可覆盖）
│   ├── ocr/          # OCR 结果 JSON
│   └── preview/      # PDF 页面预览图
├── database/         # SQLite 数据库文件
├── docker/           # Docker 配置文件
└── docs/             # 文档
```

## 系统截图

（部署后可在 docs/screenshots/ 目录下添加截图）

## 常见问题

**Q: Ollama 连接失败？**
A: 确认 Ollama 已启动（`ollama serve`），且已拉取模型（`ollama pull qwen3`）。

**Q: PaddleOCR 首次运行很慢？**
A: 首次运行会自动下载模型，需要网络，之后离线可用。

**Q: 如何在局域网内访问？**
A: 将前端 Vite 和后端 Uvicorn 的监听地址改为 `0.0.0.0`，然后通过服务器 IP 访问。

## 许可证

MIT License

---

如有问题，请提交 Issue 或联系系统管理员。
