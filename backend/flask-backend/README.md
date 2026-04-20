# AI模拟面试系统 - Flask后端

基于Flask重构的AI模拟面试系统后端，替代原有的Java后端。

## 功能特性

- **面试管理**: 开始面试、提交回答、结束面试、生成报告
- **语音交互**: 语音识别(STT)和语音合成(TTS)
- **智能评估**: 基于大模型的答案评估和问题生成
- **RAG集成**: 基于向量数据库的知识检索增强
- **数据库**: MySQL数据持久化

## 项目结构

```
flask-backend/
├── app/
│   ├── __init__.py          # 应用工厂
│   ├── config/              # 配置文件
│   │   ├── default.py
│   │   ├── development.py
│   │   └── production.py
│   ├── models/              # 数据模型
│   │   ├── __init__.py
│   │   ├── database.py
│   │   ├── interview_record.py
│   │   ├── question_answer.py
│   │   └── user.py
│   ├── routes/              # API路由
│   │   ├── __init__.py
│   │   ├── interview.py     # 面试相关接口
│   │   ├── voice.py         # 语音服务接口
│   │   ├── health.py        # 健康检查接口
│   │   └── websocket.py     # WebSocket实时通信
│   ├── services/            # 业务逻辑
│   │   ├── __init__.py
│   │   ├── interview_service.py  # 面试服务
│   │   ├── llm_service.py        # 大模型服务
│   │   ├── voice_service.py      # 语音服务
│   │   ├── rag_service.py        # RAG检索服务
│   │   └── pdf_service.py        # PDF报告生成服务
│   └── utils/               # 工具函数
│       ├── __init__.py
│       ├── response.py      # 统一响应格式
│       └── audio_utils.py   # 音频处理工具
├── requirements.txt         # Python依赖
├── run.py                  # 应用启动脚本
├── init_db.py              # 数据库初始化脚本
├── .env.example            # 环境变量示例
├── test_api.py             # API测试脚本
├── test_db.py              # 数据库测试脚本
├── test_voice.py           # 语音服务测试脚本
└── README.md               # 说明文档
```

## 快速开始

### 1. 环境准备

```bash
# 克隆项目
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
```

### 2. 配置环境变量

```bash
# 复制环境变量文件
cp .env.example .env

# 编辑.env文件，配置数据库、API密钥等
```

### 3. 数据库初始化

确保MySQL服务正在运行，并创建数据库：

```sql
CREATE DATABASE IF NOT EXISTS ai_interview DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

然后初始化表结构：

```bash
python init_db.py
```

### 4. 启动服务

```bash
# 开发模式
python run.py

# 或者使用flask命令
export FLASK_APP=app
export FLASK_ENV=development
flask run --host=0.0.0.0 --port=8083
```

服务将在 http://localhost:8083 启动。

## API文档

### 健康检查

```
GET /health
GET /api/health
GET /api/test
```

### 面试管理

| 方法 | 端点 | 描述 |
|------|------|------|
| POST | `/api/interview/start` | 开始新面试 |
| POST | `/api/interview/answer` | 提交文本回答 |
| POST | `/api/interview/answer/audio` | 提交音频回答 |
| POST | `/api/interview/end/{id}` | 结束面试 |
| GET  | `/api/interview/report/{id}` | 获取面试报告 |

### 语音服务（基于语音功能测试项目改进）

基于提供的语音功能测试模板项目(`d:\system\Desktop\ai_bot\语音功能测试`)，我们对语音功能进行了全面改进：

#### 改进内容
1. **ASR（语音识别）**: 使用WebSocket接口，支持WebM格式音频自动转换为PCM格式
2. **TTS（文本转语音）**: 使用WebSocket接口，返回MP3格式音频
3. **音频格式转换**: 自动检测WebM格式并转换为PCM 16kHz单声道
4. **API兼容性**: 保持与原有GET接口的兼容性，同时新增POST接口

#### API端点

| 方法 | 端点 | 描述 | 请求格式 |
|------|------|------|----------|
| POST | `/api/asr` | 语音识别（ASR） | `multipart/form-data`，字段：`audio` (WebM文件) |
| GET  | `/api/asr` | ASR API信息 | - |
| POST | `/api/tts` | 文本转语音（TTS） | `application/json`，字段：`{"text": "文本内容"}` |
| GET  | `/api/tts?text={text}` | 文本转语音（兼容旧版本） | 查询参数：`text` |
| GET  | `/api/voice/status` | 语音服务状态检查 | - |

#### 使用示例

**ASR（语音识别）**:
```bash
curl -X POST http://localhost:8083/api/asr \
  -F "audio=@recording.webm"
```

**TTS（文本转语音） - POST方法**:
```bash
curl -X POST http://localhost:8083/api/tts \
  -H "Content-Type: application/json" \
  -d '{"text": "你好，世界"}' \
  --output speech.mp3
```

**TTS（文本转语音） - GET方法（兼容旧版本）**:
```bash
curl "http://localhost:8083/api/tts?text=你好世界" \
  --output speech.mp3
```

#### 依赖要求
- **ffmpeg**: 需要安装ffmpeg并添加到PATH环境变量，用于音频格式转换
- **网络连接**: 需要能够访问讯飞星火API
- **API凭证**: 使用默认测试凭证或配置自己的讯飞星火API凭证

## 配置说明

### 数据库配置
- `DB_HOST`: 数据库主机
- `DB_PORT`: 数据库端口
- `DB_NAME`: 数据库名称
- `DB_USER`: 数据库用户
- `DB_PASSWORD`: 数据库密码

### 科大讯飞配置
- `IFLYTEK_APP_ID`: 讯飞应用ID
- `IFLYTEK_API_KEY`: 讯飞API密钥
- `IFLYTEK_API_SECRET`: 讯飞API密钥
- `IFLYTEK_RES_ID`: 讯飞资源ID

### 大模型配置
- `LLM_PROVIDER`: 大模型提供商 (deepseek/tongyi/zhipu)
- `LLM_API_KEY`: 大模型API密钥

### RAG服务配置
- `RAG_SERVICE_URL`: RAG服务地址
- `RAG_TOP_K`: RAG检索数量
- `RAG_ENABLED`: 是否启用RAG

## 依赖服务

1. **MySQL数据库**: 存储面试数据
2. **RAG服务**: 向量检索服务（默认端口5000）
3. **科大讯飞API**: 语音识别和合成
4. **大模型API**: DeepSeek/通义千问/智谱AI

## 测试

```bash
# 测试API连通性
curl http://localhost:8083/health

# 测试开始面试
curl -X POST http://localhost:8083/api/interview/start \
  -H "Content-Type: application/json" \
  -d '{"position": "java_backend"}'
```

## 部署

### 生产环境部署

```bash
# 使用gunicorn
gunicorn -w 4 -b 0.0.0.0:8083 "app:create_app()"

# 使用Docker
docker build -t ai-interview-flask .
docker run -p 8083:8083 --env-file .env ai-interview-flask
```

### Dockerfile示例

```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV FLASK_ENV=production
EXPOSE 8083

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8083", "run:main"]
```

## 故障排除

### 常见问题

1. **数据库连接失败**
   - 检查MySQL服务状态
   - 验证数据库配置
   - 确保数据库用户有访问权限

2. **语音服务异常**
   - 检查科大讯飞API密钥
   - 验证网络连接
   - 查看日志错误信息

3. **大模型API错误**
   - 检查API密钥是否有效
   - 验证模型提供商配置
   - 查看API调用频率限制

### 日志查看

应用日志输出到控制台，可以通过以下方式查看详细日志：

```bash
# 设置日志级别
export LOG_LEVEL=DEBUG
python run.py
```

## 许可证

MIT License