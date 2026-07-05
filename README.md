# 实验室报销管理系统

> 面向高校实验室的本地化 AI 辅助报销管理平台

## 系统简介

本系统是一套完全自托管的报销管理解决方案，专为高校实验室设计。支持 PDF 上传、PaddleOCR 识别、Ollama 本地 AI 提取发票信息，内置完整的审批流、通知中心、审计日志和统计面板。

**核心特性**

- 🔒 本地部署，数据不出内网
- 🤖 AI 自动识别发票信息（Ollama + Qwen3）
- 📄 PDF 多页多票据自动拆分，支持 9 种票据类型
- 🔍 重复发票自动查重（发票号码 + 票号双重检测）
- 💰 金额差值自动校验，差异超阈值禁止提交
- 🧾 大额报销（默认 >200 元）强制附上付款凭证截图
- ✅ 多级审批流，支持按项目配置不同审批人
- 💼 经费项目管理（管理员预置，学生直接选择）
- 🔔 站内通知中心（实时未读计数）
- 📊 多维度统计面板（学生 / 教师 / 管理员三版）
- 📤 Excel / CSV / PDF 摘要导出
- 📝 完整审计日志（不可篡改，可导出 Excel）
- 🏷️ 发票标签管理（差旅、会议、耗材等）
- ⏰ 审批超时自动催办提醒
- 🌓 深色 / 浅色模式
- 🌐 全中文界面

---

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端 | Python 3.12 · FastAPI · SQLAlchemy 2.x · Alembic · SQLite |
| 前端 | Vue 3 · TypeScript · Vite · Pinia · Element Plus |
| OCR  | PaddleOCR · PyMuPDF |
| AI   | Ollama（Qwen3 / DeepSeek） |
| 部署 | Docker Compose / 本地直接运行 |

---

## 快速开始

### 🚀 一键启动（推荐）

```bash
# Mac / Linux — 在项目根目录下运行
./start.sh

# Windows — 直接双击
start.bat
```

启动后自动打开浏览器，访问 `http://localhost:5173`。
停止：`./stop.sh`（Mac）或双击 `stop.bat`（Windows）。

---

### 首次部署（手动）

#### 第一步：创建 Python 3.12 环境

```bash
conda create -n reimb python=3.12 -c conda-forge -y
conda activate reimb
```

#### 第二步：安装依赖

```bash
cd backend
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

#### 第三步：初始化配置

```bash
cp .env.example .env
# 生产环境务必修改 SECRET_KEY
```

#### 第四步：初始化数据库

```bash
alembic upgrade head
python -m app.scripts.init_db
```

#### 第五步：启动服务

```bash
# 后端
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 前端（另开终端）
cd ../frontend
npm install
npm run dev
```

#### Docker Compose

```bash
cp backend/.env.example backend/.env
docker-compose up -d
docker-compose exec backend alembic upgrade head
docker-compose exec backend python -m app.scripts.init_db
```


## 默认账号

| 角色 | 用户名 | 密码 |
|------|--------|------|
| 管理员 | admin | Admin@123456 |
| 教师示例 | teacher1 | Teacher@123456 |
| 学生示例 | student1 | Student@123456 |

> ⚠️ **首次使用请立即修改默认密码！**

---

## 主要配置项

`backend/.env` 关键参数：

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `SECRET_KEY` | dev-secret-... | JWT 签名密钥，**生产必须修改** |
| `OLLAMA_BASE_URL` | http://localhost:11434 | Ollama 服务地址 |
| `OLLAMA_MODEL` | qwen3 | 使用的 AI 模型 |
| `AMOUNT_DIFF_THRESHOLD` | 1.0 | 金额差值容忍阈值（元） |
| `PAYMENT_RECORD_THRESHOLD` | 200.0 | 强制附付款凭证的金额门槛（元） |
| `APPROVAL_TIMEOUT_HOURS` | 72 | 审批超时阈值（小时） |
| `CORS_ORIGINS` | ["http://localhost:5173"] | 前端地址（JSON 数组格式） |

---

## 目录结构

```
PG-group-reimbursement-system/
├── start.sh / start.bat        ← 一键启动（Mac / Windows）
├── stop.sh  / stop.bat         ← 一键停止
├── backend/
│   ├── app/
│   │   ├── api/v1/             ← RESTful 接口（11 个端点模块）
│   │   ├── core/               ← 配置、数据库、安全、异常
│   │   ├── models/             ← SQLAlchemy ORM（12 张表）
│   │   ├── schemas/            ← Pydantic v2 校验
│   │   ├── repositories/       ← 数据访问层
│   │   ├── services/           ← 业务逻辑层
│   │   ├── ocr/                ← PaddleOCR + PyMuPDF
│   │   ├── ai/                 ← Ollama 客户端 + 发票提取
│   │   └── tasks/              ← OCR 后台任务 + APScheduler
│   └── migrations/             ← Alembic 迁移脚本
├── frontend/
│   └── src/
│       ├── views/              ← 11 个页面
│       ├── components/         ← 公共组件
│       ├── stores/             ← Pinia 状态管理
│       └── api/                ← Axios HTTP 客户端
├── storage/
│   ├── original/               ← 原始 PDF（永不覆盖）
│   ├── preview/                ← PDF 页面预览图
│   └── payment_records/        ← 付款凭证截图
├── database/                   ← SQLite 数据库
├── logs/                       ← 运行日志
└── docker/                     ← Docker 配置
```

---

## 常见问题

**Q: Ollama 连接失败？**
A: 确认 Ollama 已启动（`ollama serve`），且已拉取模型（`ollama pull qwen3`）。Docker 环境下需要将 `OLLAMA_BASE_URL` 改为 `http://host.docker.internal:11434`。

**Q: PaddleOCR 首次运行很慢？**
A: 首次运行会自动下载模型文件，需要网络连接，之后离线可用。

**Q: 如何在局域网内让其他人访问？**
A: `start.sh` 已默认绑定 `0.0.0.0`，局域网内通过服务器 IP 访问即可，例如 `http://192.168.1.100:5173`。

**Q: 如何修改付款凭证的金额门槛？**
A: 在 `backend/.env` 中修改 `PAYMENT_RECORD_THRESHOLD=200.0` 后重启后端。

**Q: `CORS_ORIGINS` 配置错误导致后端启动失败？**
A: 该字段必须使用 JSON 数组格式：`CORS_ORIGINS=["http://localhost:5173","http://localhost:80"]`

**Q: npm install 报依赖冲突？**
A: 执行 `npm install --legacy-peer-deps` 或升级 pinia 到 `^3.0.0`。

---

## 许可证

MIT License
