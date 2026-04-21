# AI模拟面试系统

基于 AI 的智能模拟面试平台，为计算机专业学生提供多岗位模拟面试、语音交互、智能评估和个性化反馈。

## 🎯 核心功能

- **多岗位面试**: 支持 Java 后端开发工程师、Web 前端开发工程师等岗位
- **语音交互**: 集成 Qwen-Omni Realtime 实现语音识别 (ASR) 与语音合成 (TTS)
- **智能评估**: 基于大语言模型 (LLM) 的答案评估与问题生成
- **RAG 增强**: 基于向量数据库的知识检索，提升面试专业性
- **报告生成**: 自动化面试报告与能力雷达图分析
- **历史追踪**: 面试记录保存与能力成长趋势查看

## 🏗️ 技术架构

| 组件 | 技术栈 | 说明 |
|------|--------|------|
| **前端** | Vue 3 + TypeScript + Vite + Element Plus | 现代化前端框架与UI |
| **后端** | Flask + Flask-SocketIO + SQLAlchemy | Python 微服务框架，支持 WebSocket |
| **数据库** | MySQL 8.0 (开发环境支持 SQLite) | 数据持久化 |
| **语音模型** | Qwen-Omni Realtime (阿里云百炼) | 实时音视频对话 |
| **文本模型** | 通义千问 / DeepSeek / 智谱 AI | 文本生成与评估 |
| **向量检索** | Sentence-Transformers + BGE-large-zh | 中文文本嵌入与相似度计算 |

## 📁 项目结构

```
ai_bot/
├── frontend/                 # 前端项目 (Vue 3 + TypeScript)
│   ├── src/                  # 源代码
│   ├── package.json          # 依赖配置
│   └── README.md             # 前端详细文档
├── backend/                  # 后端项目
│   └── flask-backend/        # Flask 后端
│       ├── app/              # 应用核心
│       ├── requirements.txt  # Python 依赖
│       └── README.md         # 后端详细文档
├── models/                   # AI 模型文件 (BGE-large-zh)
├── .md/                      # 项目文档目录
│   ├── read_me.md            # 完整项目文档
│   ├── 启动指南.md           # 服务启动指南
│   ├── 数据库初始化指南.md   # 数据库配置指南
│   ├── 错误排查.md           # 常见问题排查
│   ├── 验收清单.md           # 功能验收清单
│   ├── Qwen.md               # Qwen-Omni Realtime 部署指南
│   └── RAG部署指南.md        # RAG 知识库部署指南
└── realtime_video_chat_project/  # 实时视频对话测试项目
    └── README.md             # 视频聊天说明
```

## 🚀 快速开始

### 1. 环境准备

确保已安装：
- Python 3.8+ (后端)
- Node.js ^20.19.0 或 >=22.12.0 (前端)
- MySQL 8.0+ (或使用 SQLite)
- ffmpeg (音频格式转换，可选)

### 2. 后端启动

```bash
cd backend/flask-backend

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境 (Windows)
venv\Scripts\activate
# 激活虚拟环境 (Linux/Mac)
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件，设置数据库和 API 密钥

# 初始化数据库
python init_db.py

# 启动服务
python run.py
# 服务将在 http://localhost:8083 启动
```

### 3. 前端启动

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
# 前端将在 http://localhost:5173 启动
```

### 4. 访问系统

1. 打开浏览器访问：http://localhost:5173
2. 选择目标岗位 (Java 后端 / Web 前端)
3. 开始模拟面试

## ⚙️ 配置说明

主要环境变量（在 `.env` 文件中配置）：

```bash
# 数据库配置
DB_HOST=localhost
DB_PORT=3306
DB_NAME=ai_interview
DB_USER=root
DB_PASSWORD=123456

# Qwen-Omni Realtime 配置（视频面试）
QWEN_OMNI_API_KEY=your_qwen_api_key_here
QWEN_OMNI_MODEL=qwen3.5-omni-plus-realtime
QWEN_OMNI_VOICE=Ethan

# 大模型配置（文本生成与评估）
LLM_PROVIDER=tongyi
LLM_API_KEY=your_api_key_here
TONGYI_MODEL=qwen-plus
```

详细配置说明请参阅 [.md/read_me.md](.md/read_me.md)。

## 📚 详细文档

| 文档 | 说明 |
|------|------|
| [完整项目文档](.md/read_me.md) | 系统架构、API 接口、部署说明等 |
| [前端开发指南](.md/read_me_vue.md) | Vue 3 前端详细开发指南 |
| [启动指南](.md/启动指南.md) | 服务启动步骤与端口说明 |
| [数据库初始化指南](.md/数据库初始化指南.md) | MySQL 数据库配置与初始化 |
| [错误排查](.md/错误排查.md) | 常见问题与解决方案 |
| [验收清单](.md/验收清单.md) | 功能验收标准与检查项 |
| [Qwen-Omni 部署指南](.md/Qwen.md) | Qwen-Omni Realtime 配置与使用 |
| [RAG 部署指南](.md/RAG部署指南.md) | RAG 知识库部署与使用 |
| [后端文档](backend/flask-backend/README.md) | Flask 后端详细文档 |
| [前端文档](frontend/README.md) | Vue 前端详细文档 |
| [实时视频聊天项目](realtime_video_chat_project/README.md) | 实时视频对话测试项目说明 |

## 🔧 开发与贡献

### 前端开发
- 使用 Vue 3 组合式 API + TypeScript
- 组件位于 `frontend/src/components/`
- 状态管理使用 Pinia
- API 调用封装在 `frontend/src/api/`

### 后端开发
- Flask 应用采用工厂模式
- 路由定义在 `backend/flask-backend/app/routes/`
- 业务逻辑封装在 `backend/flask-backend/app/services/`
- 数据模型定义在 `backend/flask-backend/app/models/`

### RAG 功能
- 集成 Sentence-Transformers 进行文本嵌入
- 使用 BGE-large-zh 中文模型
- 向量检索增强面试问题专业性

## 📄 许可证

本项目仅供学习与研究使用。

## 🙏 致谢

- [阿里云百炼](https://bailian.console.aliyun.com/) 提供 Qwen-Omni Realtime 模型
- [通义千问](https://tongyi.aliyun.com/) 提供文本大模型支持
- [BAAI](https://www.baai.ac.cn/) 提供 BGE-large-zh 嵌入模型
- 所有开源技术栈的贡献者

---

**更新日期**: 2026-04-21  
**文档版本**: v2.0  
**项目状态**: 维护中