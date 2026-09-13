# 实时视频对话项目

基于阿里云千问（Qwen-Omni-Realtime）模型的实时视频对话测试项目。本项目实现了摄像头视频流+音频双向对话功能，支持实时视频分析和语音交互。

## 🎯 功能特点

- **实时视频分析**：通过摄像头捕获视频流，每秒发送1帧到AI模型
- **智能音频对话**：麦克风采集音频，AI语音回复，支持双向语音交流
- **回声抑制**：智能增益控制减少回声，无需完全禁用麦克风
- **多线程处理**：音频、视频、网络传输分离处理，确保流畅性
- **VAD模式**：自动语音检测，自然对话体验

## 📁 项目结构

```
realtime_video_chat_project/
├── realtime_video_chat.py    # 主程序文件
├── config.py                 # 配置文件（API密钥、模型设置等）
├── requirements.txt          # Python依赖包列表
└── README.md                # 本说明文件
```

## 🚀 快速开始

### 1. 环境准备

确保已安装Python 3.8或更高版本。

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置API密钥

从[阿里云百炼控制台](https://bailian.console.aliyun.com/)获取 API Key 后，设置为环境变量 `DASHSCOPE_API_KEY`：

```bash
# Windows PowerShell
$env:DASHSCOPE_API_KEY="sk-你的百炼APIKey"

# Linux / macOS
export DASHSCOPE_API_KEY="sk-你的百炼APIKey"
```

`config.py` 会自动读取该环境变量：

```python
# API配置
API_KEY = os.environ.get("DASHSCOPE_API_KEY", "")  # 从环境变量读取您的DashScope API密钥
MODEL = "qwen3.5-omni-plus-realtime"             # 使用的模型
VOICE = "Ethan"                                   # AI语音音色
```

> **注意**：请勿将真实 API 密钥写进代码或提交到仓库；密钥一旦泄露请立即到百炼控制台删除并重建。

### 4. 运行程序

```bash
python realtime_video_chat.py
```

## 🎮 使用说明

1. **启动程序**：运行上述命令后，程序会自动初始化
2. **权限检查**：
   - 确保已授予Python摄像头访问权限
   - 确保已授予Python麦克风访问权限
3. **开始对话**：
   - 程序显示摄像头预览窗口
   - 对着麦克风说话，描述你看到的画面
   - AI会实时分析视频内容并语音回复
4. **退出程序**：按 `q` 键或关闭预览窗口

## ⚙️ 配置选项

在 `config.py` 中可调整以下参数：

### 音频配置
```python
SAMPLE_RATE = 16000        # 输入音频采样率
AUDIO_CHUNK_SIZE = 800     # 音频块大小（25ms）
```

### 视频配置
```python
MAX_IMAGE_SIZE = 500 * 1024  # 最大图像大小500KB
IMAGE_FORMAT = "JPEG"        # 图像格式
IMAGE_QUALITY = 85           # JPEG质量
```

### 模型配置
```python
REGION = "cn"  # 地域：cn（北京）或 intl（新加坡）
VOICE = "Ethan"  # 可选音色：Ethan, Ashley, Kevin等
```

## 🔧 技术实现

### 音频处理
- **独立播放线程**：确保AI回复音频流畅播放
- **麦克风采集线程**：实时采集用户语音
- **回声抑制算法**：动态增益控制，降低回声干扰
- **音频队列缓冲**：平滑处理网络波动

### 视频处理
- **OpenCV摄像头捕获**：实时获取视频流
- **智能图像压缩**：自动调整大小和质量
- **帧率控制**：1帧/秒（符合API推荐）
- **Base64编码**：图像数据传输

### 网络通信
- **WebSocket连接**：实时双向通信
- **DashScope SDK**：阿里云官方Python SDK
- **VAD模式**：自动语音起止检测
- **多模态输入**：音频+图像同时处理

## 🐛 常见问题

### Q1: 摄像头无法打开
- 检查摄像头权限设置
- 确保没有其他程序占用摄像头
- 尝试重启程序

### Q2: 麦克风无法工作
- 检查麦克风权限设置
- 确保麦克风硬件正常
- 检查系统音频设置

### Q3: 连接失败
- 检查网络连接
- 验证API密钥是否有效
- 确认地域配置是否正确

### Q4: 回声明显
- 降低播放音量（修改代码中的 `playback_volume`）
- 调整回声抑制参数（修改 `echo_suppression_duration`）
- 使用耳机而非扬声器

## 📊 性能优化

### 降低CPU占用
- 减少视频帧发送频率
- 降低视频分辨率
- 减少音频缓冲区大小

### 改善延迟
- 使用有线网络连接
- 关闭不必要的后台程序
- 调整音频块大小

## 📝 注意事项

1. **API使用限制**：请遵守阿里云DashScope API的使用条款和配额限制
2. **隐私保护**：视频数据会发送到阿里云服务器进行处理
3. **网络要求**：建议使用稳定、低延迟的网络连接
4. **硬件要求**：建议在性能较好的设备上运行

## 🔗 相关资源

- [阿里云DashScope文档](https://help.aliyun.com/zh/model-studio/)
- [Qwen-Omni-Realtime模型介绍](https://help.aliyun.com/zh/model-studio/developer-reference/qwen-omni-realtime)
- [OpenCV Python文档](https://docs.opencv.org/)
- [PyAudio文档](https://people.csail.mit.edu/hubert/pyaudio/)

## 📄 许可证

本项目仅供学习和测试使用。API使用请遵守阿里云相关服务条款。

## 🤝 贡献

欢迎提交Issue和Pull Request来改进本项目。

---

**开始体验实时视频对话：**
```bash
cd realtime_video_chat_project
python realtime_video_chat.py
```