import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

# 数据库配置
DB_HOST = os.environ.get('DB_HOST', 'localhost')
DB_PORT = int(os.environ.get('DB_PORT', 3306))
DB_NAME = os.environ.get('DB_NAME', 'ai_interview')
DB_USER = os.environ.get('DB_USER', 'root')
DB_PASSWORD = os.environ.get('DB_PASSWORD', '123456')

SQLALCHEMY_DATABASE_URI = f'mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4'
SQLALCHEMY_TRACK_MODIFICATIONS = False
SQLALCHEMY_ECHO = False

# 服务器配置
SERVER_HOST = os.environ.get('SERVER_HOST', '0.0.0.0')
SERVER_PORT = int(os.environ.get('SERVER_PORT', 8083))

# 科大讯飞配置
IFLYTEK_APP_ID = os.environ.get('IFLYTEK_APP_ID', 'ad0d03e3')
IFLYTEK_API_KEY = os.environ.get('IFLYTEK_API_KEY', '3ac7a8d591e191628bb48afc9ea1873f')
IFLYTEK_API_SECRET = os.environ.get('IFLYTEK_API_SECRET', 'YzFjMjJmNmZhMzRjZDA4M2QxZDYxYWZm')
IFLYTEK_RES_ID = os.environ.get('IFLYTEK_RES_ID', 'YWQwZDAzZTMyMTY0NTQ3MDE1OWJtYw==')
IFLYTEK_ASR_URL = os.environ.get('IFLYTEK_ASR_URL', 'wss://iat-api.xfyun.cn/v2/iat')
IFLYTEK_TTS_URL = os.environ.get('IFLYTEK_TTS_URL', 'https://api.xfyun.cn/v1/service/v1/tts')
IFLYTEK_TTS_WS_URL = os.environ.get('IFLYTEK_TTS_WS_URL', 'wss://tts-api.xfyun.cn/v2/tts')

# 大模型配置
LLM_PROVIDER = os.environ.get('LLM_PROVIDER', 'deepseek')
LLM_API_KEY = os.environ.get('LLM_API_KEY', 'sk-ac7270f719ae48268240f0bdc715ed7e')

# DeepSeek配置
DEEPSEEK_URL = os.environ.get('DEEPSEEK_URL', 'https://api.deepseek.com/chat/completions')
DEEPSEEK_MODEL = os.environ.get('DEEPSEEK_MODEL', 'deepseek-chat')

# 通义千问配置
TONGYI_URL = os.environ.get('TONGYI_URL', 'https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation')
TONGYI_MODEL = os.environ.get('TONGYI_MODEL', 'qwen-plus')

# 智谱AI配置
ZHIPU_URL = os.environ.get('ZHIPU_URL', 'https://open.bigmodel.cn/api/paas/v4/chat/completions')
ZHIPU_MODEL = os.environ.get('ZHIPU_MODEL', 'glm-4')

# RAG服务配置
RAG_SERVICE_URL = os.environ.get('RAG_SERVICE_URL', 'http://localhost:8083')
RAG_TOP_K = int(os.environ.get('RAG_TOP_K', 5))
RAG_ENABLED = os.environ.get('RAG_ENABLED', 'false').lower() == 'true'
RAG_MODE = os.environ.get('RAG_MODE', 'local')  # 'local' 或 'http'

# 计算绝对路径
CHROMA_DB_RELATIVE = os.environ.get('CHROMA_DB_PATH', '../../chroma_db')
EMBEDDING_MODEL_RELATIVE = os.environ.get('EMBEDDING_MODEL_PATH', '../../models/bge-large-zh')

CHROMA_DB_PATH = os.path.abspath(os.path.join(BASE_DIR, CHROMA_DB_RELATIVE))
EMBEDDING_MODEL_PATH = os.path.abspath(os.path.join(BASE_DIR, EMBEDDING_MODEL_RELATIVE))

# Qwen-Omni配置
QWEN_OMNI_API_KEY = os.environ.get('QWEN_OMNI_API_KEY', 'sk-206a776b2b1a4422bef8941e33e10cc5')
QWEN_OMNI_MODEL = os.environ.get('QWEN_OMNI_MODEL', 'qwen3.5-omni-plus-realtime')
QWEN_OMNI_WS_URL = os.environ.get('QWEN_OMNI_WS_URL', 'wss://dashscope.aliyuncs.com/api-ws/v1/realtime')
QWEN_OMNI_VOICE = os.environ.get('QWEN_OMNI_VOICE', 'Cherry')
QWEN_OMNI_ENABLED = os.environ.get('QWEN_OMNI_ENABLED', 'true').lower() == 'true'

# 视频聊天配置（基于Qwen-Omni-Realtime）
VIDEO_CHAT_API_KEY = os.environ.get('VIDEO_CHAT_API_KEY', QWEN_OMNI_API_KEY)  # 默认使用Qwen-Omni密钥
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