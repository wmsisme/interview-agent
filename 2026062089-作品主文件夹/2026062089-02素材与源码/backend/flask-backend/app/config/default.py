import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

# 数据库配置
DB_HOST = os.environ.get('DB_HOST', 'localhost')
DB_PORT = int(os.environ.get('DB_PORT', 3306))
DB_NAME = os.environ.get('DB_NAME', 'ai_interview')
DB_USER = os.environ.get('DB_USER', 'root')
DB_PASSWORD = os.environ.get('DB_PASSWORD', '123456')

DEFAULT_SQLITE_PATH = os.path.join(BASE_DIR, 'interview.db')
SQLALCHEMY_DATABASE_URI = os.environ.get(
    'SQLALCHEMY_DATABASE_URI',
    f"sqlite:///{DEFAULT_SQLITE_PATH.replace(os.sep, '/')}"
)
SQLALCHEMY_TRACK_MODIFICATIONS = False
SQLALCHEMY_ECHO = False

# 服务器配置
SERVER_HOST = os.environ.get('SERVER_HOST', '0.0.0.0')
SERVER_PORT = int(os.environ.get('SERVER_PORT', 8083))

# RAG服务配置
# 默认关闭本地RAG，避免在未准备好 torch/chroma/models 时阻塞本地开发启动。
RAG_SERVICE_URL = os.environ.get('RAG_SERVICE_URL', 'http://localhost:8083')
RAG_TOP_K = int(os.environ.get('RAG_TOP_K', 5))
RAG_ENABLED = os.environ.get('RAG_ENABLED', 'false').lower() == 'true'
RAG_MODE = os.environ.get('RAG_MODE', 'local')  # 'local' 或 'http'

# LLM配置 - 用于问题生成和评估（使用千问文本API）
LLM_PROVIDER = os.environ.get('LLM_PROVIDER', 'tongyi')  # 使用千问文本API
DASHSCOPE_API_KEY = os.environ.get('DASHSCOPE_API_KEY', 'REMOVED_API_KEY')
LLM_API_KEY = DASHSCOPE_API_KEY

# 千问文本API配置（通义千问）
TONGYI_URL = os.environ.get('TONGYI_URL', 'https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation')
TONGYI_MODEL = os.environ.get('TONGYI_MODEL', 'qwen-plus')

# OpenAI兼容API - qwen3.6-max-preview 等新模型需通过此接口调用
COMPATIBLE_URL = os.environ.get('COMPATIBLE_URL', 'https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions')

# 报告生成 - DeepSeek v4-flash 为主模型，qwen-plus 为降级兜底
DEEPSEEK_MODEL = os.environ.get('DEEPSEEK_MODEL', 'deepseek-v4-flash')
REPORT_MODEL = os.environ.get('REPORT_MODEL', 'qwen-plus')

# 计算绝对路径
CHROMA_DB_RELATIVE = os.environ.get('CHROMA_DB_PATH', '../../chroma_db')
EMBEDDING_MODEL_RELATIVE = os.environ.get('EMBEDDING_MODEL_PATH', '../../models/bge-large-zh')

CHROMA_DB_PATH = os.path.abspath(os.path.join(BASE_DIR, CHROMA_DB_RELATIVE))
EMBEDDING_MODEL_PATH = os.path.abspath(os.path.join(BASE_DIR, EMBEDDING_MODEL_RELATIVE))

# Qwen-Omni配置
QWEN_OMNI_API_KEY = os.environ.get('QWEN_OMNI_API_KEY', DASHSCOPE_API_KEY)
QWEN_OMNI_MODEL = os.environ.get('QWEN_OMNI_MODEL', 'qwen3.5-omni-plus-realtime')
QWEN_OMNI_WS_URL = os.environ.get('QWEN_OMNI_WS_URL', 'wss://dashscope.aliyuncs.com/api-ws/v1/realtime')
QWEN_OMNI_VOICE = os.environ.get('QWEN_OMNI_VOICE', 'Ethan')
QWEN_OMNI_ENABLED = os.environ.get('QWEN_OMNI_ENABLED', 'true').lower() == 'true'
QWEN_OMNI_ENABLE_TURN_DETECTION = os.environ.get('QWEN_OMNI_ENABLE_TURN_DETECTION', 'false').lower() == 'true'

# 视频聊天配置（基于Qwen-Omni-Realtime）- 核心视频AI面试服务
VIDEO_CHAT_API_KEY = os.environ.get('VIDEO_CHAT_API_KEY', QWEN_OMNI_API_KEY)
VIDEO_CHAT_MODEL = os.environ.get('VIDEO_CHAT_MODEL', 'qwen3.5-omni-plus-realtime')
VIDEO_CHAT_REGION = os.environ.get('VIDEO_CHAT_REGION', 'cn')  # cn: 北京, intl: 新加坡
VIDEO_CHAT_VOICE = os.environ.get('VIDEO_CHAT_VOICE', 'Ethan')
VIDEO_CHAT_ENABLED = os.environ.get('VIDEO_CHAT_ENABLED', 'true').lower() == 'true'

# 音频配置
VIDEO_CHAT_SAMPLE_RATE = int(os.environ.get('VIDEO_CHAT_SAMPLE_RATE', 16000))
VIDEO_CHAT_AUDIO_CHUNK_SIZE = int(os.environ.get('VIDEO_CHAT_AUDIO_CHUNK_SIZE', 800))  # 25ms

# 视频配置
VIDEO_CHAT_MAX_IMAGE_SIZE = int(os.environ.get('VIDEO_CHAT_MAX_IMAGE_SIZE', 500 * 1024))  # 500KB
VIDEO_CHAT_IMAGE_FORMAT = os.environ.get('VIDEO_CHAT_IMAGE_FORMAT', 'JPEG')
VIDEO_CHAT_IMAGE_QUALITY = int(os.environ.get('VIDEO_CHAT_IMAGE_QUALITY', 85))
VIDEO_CHAT_FPS = int(os.environ.get('VIDEO_CHAT_FPS', 1))  # 每秒发送帧数

# 根据区域设置URL
if VIDEO_CHAT_REGION == 'cn':
    VIDEO_CHAT_WS_URL = 'wss://dashscope.aliyuncs.com/api-ws/v1/realtime'
else:
    VIDEO_CHAT_WS_URL = 'wss://dashscope-intl.aliyuncs.com/api-ws/v1/realtime'
