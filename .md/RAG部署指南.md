# RAG 知识库部署指南

本文档介绍如何在AI模拟面试系统中部署和使用RAG（检索增强生成）功能。RAG功能已集成到Flask后端中，使用`sentence-transformers`库进行文本嵌入和相似度检索。

## 1. 项目结构

```
ai_bot/
├── backend/
│   └── flask-backend/
│       ├── app/
│       │   ├── services/
│       │   │   └── rag_service.py      # RAG检索服务
│       │   └── config/
│       │       └── default.py          # RAG配置
│       └── requirements.txt
├── models/                              # 嵌入模型目录
│   └── bge-large-zh/                   # BGE中文嵌入模型
└── data/                                # 原始数据（可选）
    ├── 后端面试题.json
    └── 前端面试题.json
```

## 2. 环境要求

### 2.1 硬件要求
| 项目 | 最低配置 | 推荐配置 |
|------|---------|---------|
| CPU | 2核 | 4核+ |
| 内存 | 4GB | 8GB+ |
| 磁盘 | 5GB | 10GB+ |

### 2.2 软件要求
- Python 3.8+
- Flask 2.3+
- sentence-transformers 2.2+

## 3. 快速部署

### 3.1 模型文件准备

RAG功能使用BAAI/bge-large-zh模型进行文本嵌入。模型文件已存放在项目目录中：

```
models/bge-large-zh/
├── 1_Pooling/
├── README.md
├── config.json
├── model.safetensors
├── tokenizer.json
└── ...
```

如果模型文件不存在，首次运行时会自动从HuggingFace下载（需要网络连接）。

### 3.2 配置说明

RAG配置位于`backend/flask-backend/app/config/default.py`：

```python
# RAG服务配置
RAG_SERVICE_URL = os.environ.get('RAG_SERVICE_URL', 'http://localhost:5000')
RAG_TOP_K = int(os.environ.get('RAG_TOP_K', 5))
RAG_ENABLED = os.environ.get('RAG_ENABLED', 'true').lower() == 'true'
```

环境变量配置（在.env文件中）：
```bash
# RAG配置
RAG_SERVICE_URL=http://localhost:5000
RAG_TOP_K=5
RAG_ENABLED=true
```

### 3.3 启动服务

RAG功能已集成到Flask后端中，无需单独启动：

```bash
cd backend/flask-backend

# 安装依赖（已包含在requirements.txt中）
pip install -r requirements.txt

# 启动Flask后端
python run.py
```

后端启动时会自动初始化RAG服务，加载嵌入模型。

## 4. RAG服务使用

### 4.1 服务接口

RAG服务通过`rag_service.py`提供以下功能：

```python
# 文本嵌入
embed_text(text: str) -> List[float]

# 相似度检索
search_similar(query: str, collection: str, top_k: int = 5) -> List[Dict]

# 批量检索
search_similar_batch(queries: List[str], collection: str, top_k: int = 5) -> List[List[Dict]]
```

### 4.2 在业务中使用

在`interview_service.py`或其他服务中使用RAG功能：

```python
from app.services.rag_service import rag_service

# 检索相似问题
results = rag_service.search_similar(
    query="Java中的HashMap原理",
    collection="java_backend",
    top_k=5
)

# 使用检索结果增强大模型提示
context = "\n".join([r["document"] for r in results])
prompt = f"基于以下知识库内容回答问题：\n{context}\n\n问题：{question}"
```

## 5. 向量数据库

### 5.1 ChromaDB配置

项目使用ChromaDB作为向量数据库，配置如下：

```python
# 向量数据库路径
CHROMA_DB_PATH = os.path.join(BASE_DIR, "chroma_db")

# 集合名称
COLLECTIONS = {
    "backend": "java_backend",
    "frontend": "web_frontend"
}
```

### 5.2 数据导入

如需导入面试题数据到向量数据库：

```python
from app.services.rag_service import rag_service

# 添加文档到集合
rag_service.add_documents(
    collection="java_backend",
    documents=["问题1", "问题2"],
    metadatas=[{"category": "基础"}, {"category": "进阶"}],
    ids=["q1", "q2"]
)
```

## 6. 性能优化

### 6.1 模型加载优化
- 首次加载模型需要较长时间（约1-3分钟）
- 模型会缓存在内存中，后续请求响应更快
- 可考虑使用GPU加速（修改device="cuda"）

### 6.2 检索优化
- 调整`RAG_TOP_K`参数控制返回结果数量
- 使用元数据过滤缩小检索范围
- 对高频查询结果进行缓存

## 7. 故障排除

### 7.1 模型加载失败

**错误信息：** `OSError: Model not found`

**解决方案：**
1. 检查模型文件是否存在：`models/bge-large-zh/`
2. 确保网络连接（如需自动下载）
3. 手动下载模型并放置到指定目录

### 7.2 内存不足

**错误信息：** `RuntimeError: CUDA out of memory` 或系统内存不足

**解决方案：**
1. 使用CPU模式（默认配置）
2. 减少`RAG_TOP_K`值
3. 增加系统内存或使用更高配置服务器

### 7.3 检索结果不准确

**解决方案：**
1. 调整检索参数`top_k`
2. 检查向量数据库中的数据质量
3. 使用元数据过滤优化检索范围

## 8. 离线部署

如需在离线环境部署：

1. **提前下载模型：**
   ```bash
   # 在联网环境中下载模型
   from sentence_transformers import SentenceTransformer
   model = SentenceTransformer('BAAI/bge-large-zh')
   model.save('models/bge-large-zh')
   ```

2. **复制模型文件到离线环境：**
   ```bash
   # 复制整个models目录到目标服务器
   scp -r models/bge-large-zh user@server:/path/to/project/models/
   ```

3. **配置本地模型路径：**
   ```python
   # 确保模型路径配置正确
   MODEL_PATH = os.path.join(BASE_DIR, "models", "bge-large-zh")
   ```

## 9. API接口

### 9.1 检索接口

```http
POST /api/rag/search
Content-Type: application/json

{
    "query": "Java中的HashMap原理",
    "collection": "java_backend",
    "top_k": 5
}
```

响应示例：
```json
{
    "query": "Java中的HashMap原理",
    "collection": "java_backend",
    "results": [
        {
            "id": "q1",
            "document": "HashMap是Java中常用的数据结构...",
            "metadata": {"category": "基础", "difficulty": "中等"},
            "score": 0.92
        }
    ]
}
```

### 9.2 健康检查

```http
GET /api/rag/health
```

响应示例：
```json
{
    "status": "ok",
    "model_loaded": true,
    "collections": ["java_backend", "web_frontend"]
}
```

## 10. 相关文档

- **后端开发指南**: 参见 [backend/flask-backend/README.md](../backend/flask-backend/README.md)
- **启动指南**: 参见 [启动指南.md](启动指南.md)
- **模型说明**: 参见 [models/bge-large-zh/README.md](../models/bge-large-zh/README.md)

## 11. 参考资料

- [BGE模型GitHub](https://github.com/FlagOpen/FlagEmbedding)
- [Sentence-Transformers文档](https://www.sbert.net/