# AI模拟面试系统 - 全栈项目文档

## 项目概述

AI模拟面试系统是一个面向计算机专业学生的智能面试平台，提供多岗位模拟面试、语音交互、智能评估和个性化反馈功能。系统采用前后端分离架构，后端使用Python Flask框架，前端使用Vue 3 + TypeScript。

### 核心功能

- **多岗位面试管理**: 支持Java后端、Web前端等岗位的模拟面试
- **语音交互**: 集成科大讯飞语音识别(ASR)和语音合成(TTS)功能
- **智能评估**: 基于大语言模型(LLM)的答案评估和问题生成
- **RAG集成**: 基于向量数据库的知识检索增强
- **报告生成**: 自动化面试报告与能力分析
- **历史记录**: 面试历史查看和能力成长追踪

### 技术架构

| 组件 | 技术选型 | 说明 |
|------|----------|------|
| **前端** | Vue 3 + TypeScript | 渐进式JavaScript框架 |
| **前端构建** | Vite | 现代前端构建工具 |
| **UI组件库** | Element Plus | Vue 3组件库 |
| **状态管理** | Pinia | Vue状态管理库 |
| **HTTP客户端** | axios | REST API调用 |
| **WebSocket** | socket.io-client | 实时语音流通信 |
| **后端框架** | Flask 2.3+ | Python Web框架 |
| **WebSocket服务** | Flask-SocketIO | 实时语音流处理 |
| **数据库ORM** | Flask-SQLAlchemy | 数据库操作 |
| **数据库** | MySQL 8.0 | 数据持久化 |
| **语音服务** | 科大讯飞SDK | 语音识别和合成 |
| **大模型** | DeepSeek/通义千问等 | 智能对话与评估 |
| **向量检索** | Sentence-Transformers | 文本嵌入与相似度计算 |

## 项目结构

```
ai_bot/
├── frontend/                      # 前端项目（Vue 3 + TypeScript）
│   ├── src/
│   │   ├── api/                  # API接口封装
│   │   ├── assets/               # 静态资源
│   │   ├── components/           # 通用组件
│   │   ├── router/               # 路由配置
│   │   ├── stores/               # 状态管理（Pinia）
│   │   ├── utils/                # 工具函数
│   │   ├── views/                # 页面视图
│   │   ├── App.vue               # 根组件
│   │   └── main.ts               # 应用入口
│   ├── package.json              # 依赖包配置
│   ├── vite.config.ts            # Vite配置
│   └── README.md                 # 前端说明文档
├── backend/                      # 后端项目
│   └── flask-backend/            # Flask后端主目录
│       ├── app/                  # 应用核心代码
│       │   ├── config/           # 配置文件
│       │   ├── models/           # 数据模型
│       │   ├── routes/           # API路由
│       │   ├── services/         # 业务逻辑
│       │   └── utils/            # 工具函数
│       ├── requirements.txt      # Python依赖包
│       ├── run.py               # 应用启动脚本
│       ├── init_db.py           # 数据库初始化
│       └── README.md            # 后端详细说明
├── models/                       # AI模型文件
│   └── bge-large-zh/             # BGE中文嵌入模型
├── .md/                          # 项目文档目录
│   ├── read_me_vue.md           # Vue前端开发指南
│   ├── 启动指南.md              # 系统启动指南
│   ├── 数据库初始化指南.md      # 数据库配置指南
│   ├── 错误排查.md              # 常见问题排查
│   ├── 验收清单.md              # 功能验收清单
│   ├── 讯飞星火.md              # 讯飞语音配置指南
│   └── RAG部署指南.md           # RAG部署指南
└── 语音功能测试/                 # 语音功能测试项目
    └── README.md                 # 语音测试说明
```

## 快速开始

### 1. 后端启动

```bash
# 进入后端目录
cd backend/flask-backend

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑.env文件，配置数据库和API密钥

# 初始化数据库
python init_db.py

# 启动服务
python run.py
# 服务将在 http://localhost:8083 启动
```

### 2. 前端启动

```bash
# 进入前端目录
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
# 前端将在 http://localhost:5173 启动
```

### 3. 访问系统

1. 打开浏览器访问：http://localhost:5173
2. 系统会自动代理API请求到后端服务（http://localhost:8083）

## 详细文档

- **后端开发指南**: 参见 [backend/flask-backend/README.md](backend/flask-backend/README.md)
- **前端开发指南**: 参见 [.md/read_me_vue.md](.md/read_me_vue.md)
- **语音服务配置**: 参见 [.md/讯飞星火.md](.md/讯飞星火.md)
- **数据库配置**: 参见 [.md/数据库初始化指南.md](.md/数据库初始化指南.md)
- **错误排查**: 参见 [.md/错误排查.md](.md/错误排查.md)
- **功能验收**: 参见 [.md/验收清单.md](.md/验收清单.md)
- **RAG部署**: 参见 [.md/RAG部署指南.md](.md/RAG部署指南.md)

## 配置说明

### 环境变量配置

后端服务需要以下环境变量：

```bash
# 数据库配置
DB_HOST=localhost
DB_PORT=3306
DB_NAME=ai_interview
DB_USER=root
DB_PASSWORD=123456

# 科大讯飞配置
IFLYTEK_APP_ID=ad0d03e3
IFLYTEK_API_KEY=3ac7a8d591e191628bb48afc9ea1873f
IFLYTEK_API_SECRET=YzFjMjJmNmZhMzRjZDA4M2QxZDYxYWZm

# 大模型配置
LLM_PROVIDER=deepseek
LLM_API_KEY=your_api_key_here
```

### 前端代理配置

前端Vite配置已设置代理到后端：

```typescript
// vite.config.ts
server: {
  proxy: {
    '/api': {
      target: 'http://localhost:8083',
      changeOrigin: true
    }
  }
}
```

## API接口

### 面试管理
- `POST /api/interview/start` - 开始新面试
- `POST /api/interview/answer` - 提交文本回答
- `POST /api/interview/answer/audio` - 提交音频回答
- `POST /api/interview/end/{id}` - 结束面试
- `GET /api/interview/report/{id}` - 获取面试报告

### 语音服务
- `POST /api/asr` - 语音识别（ASR）
- `POST /api/tts` - 文本转语音（TTS）
- `GET /api/voice/status` - 语音服务状态检查

### 健康检查
- `GET /health` - 健康检查
- `GET /api/health` - API健康检查
- `GET /api/test` - 测试接口

## 部署说明

### 生产环境部署

1. **后端部署**:
   ```bash
   # 使用gunicorn部署Flask应用
   gunicorn -w 4 -b 0.0.0.0:8083 "app:create_app()"
   ```

2. **前端部署**:
   ```bash
   # 构建生产版本
   npm run build
   # 使用nginx或类似静态文件服务器部署dist目录
   ```

3. **数据库迁移**:
   - 使用`init_db.py`脚本在生产环境初始化数据库
   - 确保MySQL服务已正确配置和优化

### 注意事项

1. **API密钥安全**: 生产环境务必使用自己的API密钥，不要使用默认测试凭证
2. **数据库备份**: 定期备份MySQL数据库
3. **日志管理**: 配置适当的日志记录和监控
4. **性能优化**: 根据实际负载调整gunicorn工作进程数

## 开发指南

### 前端开发
- 使用Vue 3组合式API和TypeScript
- 组件存放在`src/components/`目录
- 页面视图存放在`src/views/`目录
- API调用封装在`src/api/`目录
- 状态管理使用Pinia，存放在`src/stores/`目录

### 后端开发
- Flask应用使用工厂模式创建
- 数据模型定义在`app/models/`目录
- API路由定义在`app/routes/`目录
- 业务逻辑封装在`app/services/`目录
- 配置文件位于`app/config/`目录

### RAG功能
- RAG服务集成在Flask后端中，使用`sentence-transformers`进行文本嵌入
- 向量检索用于增强大模型的知识库
- 模型文件存放在`models/bge-large-zh/`目录