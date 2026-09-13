# AI 模拟面试与能力提升软件

面向计算机相关专业学生的 AI 模拟面试系统：用多轮语音 / 实时视频对话还原真实面试场景，对每一次回答做多维度量化评估，并生成可下载的面试报告。

> 参赛作品材料与完整设计文档见 [`2026062089-作品主文件夹/`](2026062089-作品主文件夹/)，内含「作品与答辩材料」「素材与源码」「设计与开发文档」三部分。

## 核心功能

| 模块 | 说明 |
| --- | --- |
| 多岗位面试 | 按岗位（Java 后端 / Web 前端等）加载对应题库与评估标准 |
| 实时视频面试 | 通过 WebSocket 把摄像头画面与麦克风音频实时送入多模态大模型，AI 面试官语音提问、动态追问 |
| 智能评估 | 每次回答按技术正确性、知识深度、表达逻辑、岗位匹配度四个维度打分并给出改进建议 |
| RAG 知识检索 | 基于 ChromaDB 的岗位知识库，为出题与评分提供参考 |
| 报告与导出 | 面试结束生成结构化报告（ECharts 雷达图 + 逐题点评），支持导出 PDF |

## 技术栈

**前端**：Vue 3 + TypeScript + Vite + Element Plus + Pinia + Vue Router + ECharts + socket.io-client

**后端**：Flask + Flask-SocketIO（eventlet）+ Flask-SQLAlchemy

**数据**：MySQL 8.0（未配置时回落 SQLite）；ChromaDB 向量库

**模型**（阿里云百炼 DashScope）：

- `qwen3.5-omni-plus-realtime` —— 实时音视频面试对话
- `qwen-plus` —— 文本出题与答案评估，并作为报告生成的兜底模型
- `deepseek-v4-flash` —— 报告生成主模型

**其他**：Sentence-Transformers（向量化）、OpenCV / PyAudio（音视频处理）、ReportLab（PDF 报告）

## 目录结构

```
README.md
项目概要介绍.md / 项目详细方案.md      # 项目概要与技术方案
测试.py                                # DashScope 调用最小示例
2026062089-作品主文件夹/
├── 2026062089-01作品与答辩材料/        # 概要介绍、详细方案（提交版）
├── 2026062089-02素材与源码/            # 可运行源码
│   ├── backend/flask-backend/          # Flask 后端：app/{config,routes,services,models,utils}
│   ├── frontend/                       # Vue 3 前端
│   ├── realtime_video_chat_project/    # Qwen-Omni 实时视频对话独立验证工程
│   ├── install.bat / start_fixed.bat / stop_fixed.bat / dev.ps1
│   └── package.json / requirements.txt
└── 2026062089-03设计与开发文档/        # 启动指南、数据库初始化、RAG 部署、错误排查、验收清单
```

## 快速开始

### 0. 配置 API Key（必填）

密钥只从环境变量读取，**不要写进代码或提交到仓库**：

```powershell
# Windows PowerShell
$env:DASHSCOPE_API_KEY="sk-你的百炼APIKey"
```

```bash
# Linux / macOS
export DASHSCOPE_API_KEY="sk-你的百炼APIKey"
```

后端可用的环境变量（定义在 `app/config/default.py`，除 Key 外都有默认值）：

| 变量 | 默认值 | 说明 |
| --- | --- | --- |
| `DASHSCOPE_API_KEY` | 空 | 百炼 API Key，出题 / 评估 / 实时视频都会用到 |
| `SERVER_HOST` / `SERVER_PORT` | `0.0.0.0` / `8083` | 后端监听地址 |
| `SQLALCHEMY_DATABASE_URI` | 本地 `interview.db` | 默认 SQLite；接 MySQL 时改为 `mysql+pymysql://user:pwd@host/db` |
| `DB_HOST` `DB_PORT` `DB_NAME` `DB_USER` `DB_PASSWORD` | `localhost` `3306` `ai_interview` `root` `123456` | 数据库连接参数（建库脚本使用） |
| `RAG_ENABLED` / `RAG_MODE` | `false` / `local` | 本地 RAG 默认关闭，避免在未准备 torch / ChromaDB 模型时阻塞启动 |
| `RAG_SERVICE_URL` / `RAG_TOP_K` | `http://localhost:8083` / `5` | RAG 服务地址与召回条数 |
| `VIDEO_CHAT_MODEL` / `VIDEO_CHAT_VOICE` | `qwen3.5-omni-plus-realtime` / `Ethan` | 实时视频面试的模型与音色 |
| `SECRET_KEY` | 开发占位值 | 生产环境必须替换 |

### 1. 启动后端

```bash
cd 2026062089-作品主文件夹/2026062089-02素材与源码/backend/flask-backend
pip install -r requirements.txt
python run.py                 # 开发模式：Flask-SocketIO，监听 8083
```

生产模式把 `FLASK_ENV` 设为 `production`，会走 gunicorn + eventlet（4 workers）。

### 2. 启动前端

```bash
cd 2026062089-作品主文件夹/2026062089-02素材与源码/frontend
npm install
npm run dev                   # Vite，监听 5173
```

Vite 已配置代理：`/api` 与 `/socket.io` 转发到 `http://localhost:8083`（`/socket.io` 开启 `ws: true`），前端直接访问 http://localhost:5173 即可。

## 页面与接口

**前端路由**

| 路径 | 页面 |
| --- | --- |
| `/` | 首页：岗位选择与面试入口 |
| `/interview/video` | 实时视频面试 |
| `/report/:id` | 面试报告 |
| `/about` | 关于 |

**HTTP 接口**

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| POST | `/api/interview/start` | 开始一场面试 |
| POST | `/api/interview/answer` | 提交文字回答 |
| POST | `/api/interview/answer/audio` | 提交语音回答 |
| POST | `/api/interview/end/<id>` | 结束面试 |
| POST | `/api/interview/conversation/<id>` | 保存对话记录 |
| GET | `/api/interview/report/<id>` | 获取面试报告 |
| GET | `/api/interview/report/pdf/<id>` | 下载 PDF 报告 |
| GET | `/api/rag/health` · `/api/rag/collections` | RAG 服务状态与知识库列表 |
| POST | `/api/rag/search` · `/api/rag/search/<collection>` | 知识库检索 |
| GET | `/health` · `/api/health` | 健康检查 |

**WebSocket**：命名空间 `/ws/video`，事件 `start_interview` / `audio` / `video_frame` / `image` / `stop_interview`

## 说明

- 实时视频面试链路：前端采集音频与视频帧 → `/ws/video` → 后端 `video_chat_service` 转发至百炼 Qwen-Omni 实时接口 → AI 的语音 / 文本结果回传前端播放。
- 未配置 MySQL 时后端默认使用本地 SQLite 文件，便于直接跑通；生产环境建议接 MySQL 8.0。
- 更细的部署与排障步骤见 `2026062089-作品主文件夹/2026062089-03设计与开发文档/`（启动指南、数据库初始化指南、RAG 部署指南、错误排查、验收清单）。
