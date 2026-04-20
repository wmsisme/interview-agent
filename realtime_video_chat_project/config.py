# 千问实时多模态测试项目配置
import os

# API配置
API_KEY = "sk-206a776b2b1a4422bef8941e33e10cc5"
MODEL = "qwen3.5-omni-plus-realtime"
VOICE = "Ethan"  # 默认音色

# 地域配置
REGION = "cn"  # cn: 北京, intl: 新加坡
BASE_DOMAIN = "dashscope.aliyuncs.com" if REGION == "cn" else "dashscope-intl.aliyuncs.com"
URL = f"wss://{BASE_DOMAIN}/api-ws/v1/realtime"

# 音频配置
SAMPLE_RATE = 16000  # 输入音频采样率
AUDIO_CHUNK_SIZE = 800  # 音频块大小（400个样本，25ms）

# 图像配置
MAX_IMAGE_SIZE = 500 * 1024  # 最大图像大小500KB
IMAGE_FORMAT = "JPEG"  # 图像格式
IMAGE_QUALITY = 85  # JPEG质量

# 测试文件路径
TEST_IMAGE_PATH = "test_image.jpg"
TEST_VIDEO_PATH = "test_video.mp4"