# AI面试官系统部署文档

> **文档版本**：v1.0
> **更新日期**：2026-04-13
> **适用场景**：基于 Qwen-Omni Realtime API 的 AI 面试官系统后端部署、前后端对接与 RAG 知识库集成


## 一、项目概述

本系统基于阿里云百炼平台的 Qwen-Omni-Realtime 服务，构建一个支持**语音识别、语音合成、图像识别和文字生成**的全模态 AI 面试官。系统采用 WebSocket 协议实现低延迟实时交互，并集成 RAG（检索增强生成）能力，使面试官能够基于企业自定义知识库（如岗位要求、公司介绍、技术题库等）进行专业提问和评估。

**主要技术栈**：
- **后端**：Python ≥3.8（推荐 3.10+），DashScope SDK ≥1.23.9
- **实时通信**：WebSocket（wss://dashscope.aliyuncs.com/api-ws/v1/realtime）
- **RAG 知识库**：阿里云百炼知识索引 + 本地向量检索（FAISS / DashVector）
- **前端对接**：WebSocket 客户端 + PCM 音频播放 + 视频采集


## 二、系统整体架构

```
┌─────────────────────────────────────────────────────────────────┐
│                        前端 (浏览器)                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │ 麦克风采集   │  │ 摄像头采集   │  │ PCM 音频播放 │              │
│  │ (16kHz PCM) │  │ (Base64图像) │  │ (Web Audio) │              │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘              │
│         │                │                ▲                       │
│         └────────────────┼────────────────┘                       │
│                          │                                        │
│                    WebSocket (wss://)                             │
└──────────────────────────┼────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                        后端服务 (Python)                          │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │              OmniRealtimeConversation 会话管理                │ │
│  │  - 接收音频流 / 图像帧                                         │ │
│  │  - 转发 AI 回复 (文本 + 音频 Base64)                           │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                              │                                    │
│              ┌───────────────┼───────────────┐                    │
│              ▼               ▼               ▼                    │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐     │
│  │  百炼 RAG 应用   │ │ Qwen-Omni API   │ │   会话状态存储   │     │
│  │ (知识库检索)     │ │ (多模态对话)    │ │   (Redis/内存)  │     │
│  └─────────────────┘ └─────────────────┘ └─────────────────┘     │
└─────────────────────────────────────────────────────────────────┘
```

**架构说明**：
- 前端通过 WebSocket 与后端服务建立持久连接，传输 PCM 音频流和图像帧
- 后端作为代理层，负责与阿里云百炼 API 通信，同时集成 RAG 知识库进行检索增强
- 面试官的身份设定（instructions）和知识库内容共同决定了对话的专业性

**可信度说明**：上述架构基于 Qwen-Omni 官方文档的协议设计，会话（session）、云端缓冲区（buffer）、响应（response）等概念直接来源于官方定义。


## 三、环境准备与依赖安装

### 3.1 API Key 获取

1. 登录 [阿里云百炼控制台](https://bailian.console.aliyun.com/)
2. 在左侧导航栏选择“模型广场” → “API Key 管理”
3. 创建新的 API Key 并妥善保存

### 3.2 Python 环境配置

**最低要求**：Python ≥3.8，建议 3.10+

```bash
# 安装 DashScope SDK（版本 ≥1.23.9）
pip install dashscope>=1.23.9

# 可选：安装 websocket-client（如果需要更底层的 WebSocket 控制）
pip install websocket-client

# RAG 相关依赖（如使用本地向量检索）
pip install langchain chromadb faiss-cpu
```

**可信度说明**：SDK 版本要求来自官方 Python SDK 文档。

### 3.3 环境变量配置

```bash
# 在 .env 文件中配置（推荐使用 python-dotenv）
export DASHSCOPE_API_KEY="sk-xxxxxxxxxxxxxxxxxxxxxxxx"
```


## 四、后端核心模块实现

### 4.1 WebSocket 连接与会话初始化

```python
# backend/omni_session.py
import os
import json
import base64
from dashscope.audio.qwen_omni import OmniRealtimeConversation, OmniRealtimeCallback
import dashscope

dashscope.api_key = os.getenv("DASHSCOPE_API_KEY")

class InterviewerCallback(OmniRealtimeCallback):
    """处理服务端返回事件的回调类"""
    
    def __init__(self, websocket_handler):
        self.websocket = websocket_handler  # 用于向前端转发数据的 WebSocket 连接
        
    def on_open(self):
        print("[Omni] 连接已建立")
        
    def on_event(self, event):
        """处理模型返回的各类事件"""
        event_type = event.get("type")
        
        if event_type == "response.audio.delta":
            # 音频增量数据（Base64 编码的 PCM）
            audio_base64 = event.get("delta", "")
            self.websocket.send(json.dumps({
                "type": "audio",
                "data": audio_base64
            }))
            
        elif event_type == "response.text.delta":
            # 文本增量数据（用于字幕显示）
            text_chunk = event.get("delta", "")
            self.websocket.send(json.dumps({
                "type": "text",
                "data": text_chunk
            }))
            
        elif event_type == "response.done":
            # 一次响应完成
            print("[Omni] 响应完成")
            
    def on_close(self, close_status_code, close_msg):
        print(f"[Omni] 连接关闭 (code={close_status_code}, msg={close_msg})")
        
    def on_error(self, error):
        print(f"[Omni] 错误: {error}")


def create_omni_session(callback):
    """创建 Omni-Realtime 会话"""
    conversation = OmniRealtimeConversation(
        model="qwen3.5-omni-flash-realtime",  # 推荐使用 Flash 版本，延迟更低
        callback=callback,
        url="wss://dashscope.aliyuncs.com/api-ws/v1/realtime"  # 北京地域地址
    )
    return conversation
```

**可信度说明**：上述代码基于官方 Python SDK 文档和示例代码。

### 4.2 面试官配置（update_session）

连接建立后，立即调用 `update_session` 配置面试官的角色和行为：

```python
# backend/session_config.py
from dashscope.audio.qwen_omni import MultiModality, AudioFormat

def configure_interviewer(conversation, job_info=None, company_info=None):
    """
    配置面试官的会话参数
    
    Args:
        conversation: OmniRealtimeConversation 实例
        job_info: 岗位信息（用于动态构建 instructions）
        company_info: 公司信息
    """
    
    # 构建系统提示词
    base_instructions = """
你是一位专业、友好、循循善诱的技术面试官，名字是"千小问"。
你需要通过提问来评估候选人的技术能力和综合素质。

面试原则：
1. 开场先进行简短的自我介绍（不超过30秒），然后询问候选人准备好了没有。
2. 根据候选人的简历和岗位要求，提出有针对性的技术问题。
3. 问题应由浅入深，根据候选人的回答质量决定是否追问或转换话题。
4. 控制每轮提问的长度，避免长篇大论，保持对话的自然节奏。
5. 面试结束时，对候选人的表现给予简短鼓励，并告知后续流程。

请始终使用口语化的中文进行提问和回应，保持专业且亲切的语气。
"""
    
    if job_info:
        base_instructions += f"\n\n当前招聘岗位信息：{job_info}"
    if company_info:
        base_instructions += f"\n公司背景信息：{company_info}"
    
    conversation.update_session({
        "output_modalities": [MultiModality.TEXT, MultiModality.AUDIO],  # 同时输出文本和音频
        "voice": "Cherry",  # Qwen3-Omni-Flash-Realtime 默认音色
        "instructions": base_instructions,
        "enable_turn_detection": True,  # 开启 VAD 模式，自动检测语音起止
        "input_audio_format": AudioFormat.PCM_16000HZ_MONO_16BIT,  # 输入音频格式
        "output_audio_format": AudioFormat.PCM,  # 输出音频格式
        "smooth_output": True,  # 获得更口语化的回复
        "enable_input_audio_transcription": True  # 开启语音转文本，便于后端记录
    })
    
    print("[Omni] 会话配置完成")
```

**可信度说明**：参数配置来源于官方 Python SDK 文档。

### 4.3 音频流处理

```python
# backend/audio_handler.py
import json

async def handle_audio_stream(websocket, omni_conversation):
    """
    处理从前端接收的音频流数据
    
    前端应以 16kHz 采样率、单声道、16-bit PCM 格式发送音频数据
    """
    async for message in websocket:
        data = json.loads(message)
        
        if data["type"] == "audio":
            # 接收到的音频数据（Base64 编码）
            audio_base64 = data["data"]
            audio_bytes = base64.b64decode(audio_base64)
            
            # 直接转发给 Omni API
            omni_conversation.send_audio(audio_bytes)
            
        elif data["type"] == "image":
            # 接收到的图像数据
            image_base64 = data["data"]
            omni_conversation.send_image(image_base64)
            
        elif data["type"] == "end_turn":
            # 手动模式下触发一次响应（VAD 模式下不需要）
            omni_conversation.create_response()
```

### 4.4 图像识别集成

AI 面试官可以实时分析面试者的画面，捕捉微表情、检测环境异常等：

```python
# backend/image_handler.py

def send_image_frame(omni_conversation, image_data):
    """
    发送图像帧给 Omni API 进行分析
    
    Args:
        image_data: Base64 编码的图像字符串（不含 data:image 前缀）
    """
    # 构建图像输入事件
    image_event = {
        "type": "input_image_buffer.append",
        "image": image_data
    }
    omni_conversation.send(json.dumps(image_event))
```

**使用场景建议**：
- **入场检测**：面试开始时检测候选人是否就位
- **环境合规检查**：确保面试环境安静、无他人协助
- **表情分析**：结合后续评估模块分析候选人的情绪状态
- **实时配合提问**：例如要求候选人展示白板编码内容时，可分析手写内容

**可信度说明**：图像发送协议参考了 Qwen-Omni 多模态输入规范。

### 4.5 WebSocket 服务主入口（FastAPI 示例）

```python
# backend/main.py
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import asyncio
import json

from omni_session import create_omni_session, InterviewerCallback
from session_config import configure_interviewer
from rag_client import RAGClient  # 见第 6 节

app = FastAPI()

class ConnectionManager:
    """管理所有活跃的 WebSocket 连接"""
    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}
    
    async def connect(self, session_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[session_id] = websocket
    
    def disconnect(self, session_id: str):
        self.active_connections.pop(session_id, None)
    
    async def send_message(self, session_id: str, message: dict):
        if session_id in self.active_connections:
            await self.active_connections[session_id].send_json(message)

manager = ConnectionManager()
rag_client = RAGClient()

@app.websocket("/ws/interview/{session_id}")
async def interview_websocket(websocket: WebSocket, session_id: str):
    await manager.connect(session_id, websocket)
    
    # 创建 Omni 会话回调
    callback = InterviewerCallback(websocket)
    conversation = create_omni_session(callback)
    
    try:
        # 配置面试官
        configure_interviewer(conversation)
        
        # 启动 Omni 连接
        conversation.start()
        
        # 处理前端消息
        async for message in websocket.iter_text():
            data = json.loads(message)
            
            if data["type"] == "audio":
                audio_bytes = base64.b64decode(data["data"])
                conversation.send_audio(audio_bytes)
                
            elif data["type"] == "image":
                conversation.send_image(data["data"])
                
            elif data["type"] == "rag_query":
                # RAG 检索请求（详见第 6 节）
                query = data["query"]
                rag_result = await rag_client.retrieve(query)
                await manager.send_message(session_id, {
                    "type": "rag_result",
                    "data": rag_result
                })
                
    except WebSocketDisconnect:
        manager.disconnect(session_id)
    finally:
        conversation.stop()
        conversation.close()
```

### 4.6 心跳保活与错误处理

```python
# backend/keepalive.py
import asyncio

async def heartbeat(conversation, interval=30):
    """定期发送心跳包保持连接"""
    while True:
        await asyncio.sleep(interval)
        try:
            conversation.send(json.dumps({"type": "ping"}))
        except Exception as e:
            print(f"[Heartbeat] 发送失败: {e}")
            break


# 指数退避重连策略
import time

def reconnect_with_backoff(create_func, max_retries=5, base_delay=1):
    """带指数退避的重连机制"""
    for attempt in range(max_retries):
        try:
            return create_func()
        except Exception as e:
            delay = base_delay * (2 ** attempt)
            print(f"[Reconnect] 第 {attempt + 1} 次重连失败: {e}，{delay}秒后重试")
            time.sleep(delay)
    raise Exception("达到最大重试次数，连接失败")
```

**注意事项**：
- 一个 WebSocket 会话最长可持续 **120 分钟**，足以覆盖绝大多数面试场景
- 建议使用耳机播放音频，避免回声触发语音打断


## 五、前端对接指南

### 5.1 WebSocket 连接

```javascript
// frontend/websocket.js
class InterviewWebSocket {
    constructor(sessionId) {
        this.sessionId = sessionId;
        this.ws = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
    }
    
    connect() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const host = window.location.host;
        this.ws = new WebSocket(`${protocol}//${host}/ws/interview/${this.sessionId}`);
        
        this.ws.onopen = () => {
            console.log('WebSocket 连接已建立');
            this.reconnectAttempts = 0;
        };
        
        this.ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this.handleMessage(data);
        };
        
        this.ws.onclose = () => {
            console.log('WebSocket 连接已关闭');
            this.reconnect();
        };
        
        this.ws.onerror = (error) => {
            console.error('WebSocket 错误:', error);
        };
    }
    
    handleMessage(data) {
        switch (data.type) {
            case 'audio':
                // 处理音频数据（Base64 PCM）
                this.playAudio(data.data);
                break;
            case 'text':
                // 处理文本数据（用于字幕显示）
                this.updateSubtitle(data.data);
                break;
            case 'rag_result':
                // 处理 RAG 检索结果
                this.handleRAGResult(data.data);
                break;
        }
    }
    
    sendAudio(audioBase64) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify({
                type: 'audio',
                data: audioBase64
            }));
        }
    }
    
    sendImage(imageBase64) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify({
                type: 'image',
                data: imageBase64
            }));
        }
    }
    
    reconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 30000);
            setTimeout(() => this.connect(), delay);
        }
    }
}
```

### 5.2 音频采集（麦克风）

```javascript
// frontend/audioCapture.js
class AudioCapture {
    constructor(sampleRate = 16000) {
        this.sampleRate = sampleRate;
        this.stream = null;
        this.audioContext = null;
        this.processor = null;
        this.onAudioData = null;  // 回调函数，用于发送音频数据
    }
    
    async start() {
        // 获取麦克风权限
        this.stream = await navigator.mediaDevices.getUserMedia({
            audio: {
                sampleRate: this.sampleRate,
                channelCount: 1,
                echoCancellation: true,
                noiseSuppression: true,
                autoGainControl: true
            }
        });
        
        // 创建 AudioContext
        this.audioContext = new (window.AudioContext || window.webkitAudioContext)({
            sampleRate: this.sampleRate
        });
        
        const source = this.audioContext.createMediaStreamSource(this.stream);
        
        // 创建 ScriptProcessor（或使用 AudioWorklet 以获得更好性能）
        this.processor = this.audioContext.createScriptProcessor(4096, 1, 1);
        
        this.processor.onaudioprocess = (event) => {
            const inputData = event.inputBuffer.getChannelData(0);
            
            // 转换为 16-bit PCM
            const pcmData = new Int16Array(inputData.length);
            for (let i = 0; i < inputData.length; i++) {
                pcmData[i] = Math.max(-1, Math.min(1, inputData[i])) * 0x7FFF;
            }
            
            // 转换为 Base64
            const base64 = this.arrayBufferToBase64(pcmData.buffer);
            
            // 通过回调发送
            if (this.onAudioData) {
                this.onAudioData(base64);
            }
        };
        
        source.connect(this.processor);
        this.processor.connect(this.audioContext.destination);
    }
    
    arrayBufferToBase64(buffer) {
        let binary = '';
        const bytes = new Uint8Array(buffer);
        const len = bytes.byteLength;
        for (let i = 0; i < len; i++) {
            binary += String.fromCharCode(bytes[i]);
        }
        return window.btoa(binary);
    }
    
    stop() {
        if (this.processor) {
            this.processor.disconnect();
        }
        if (this.audioContext) {
            this.audioContext.close();
        }
        if (this.stream) {
            this.stream.getTracks().forEach(track => track.stop());
        }
    }
}
```

### 5.3 音频播放（PCM 解码播放）

```javascript
// frontend/audioPlayer.js
class PCMPlayer {
    constructor(options = {}) {
        this.sampleRate = options.sampleRate || 16000;
        this.channels = options.channels || 1;
        this.audioContext = null;
        this.bufferQueue = [];
        this.isPlaying = false;
    }
    
    init() {
        this.audioContext = new (window.AudioContext || window.webkitAudioContext)({
            sampleRate: this.sampleRate
        });
    }
    
    // 播放 Base64 编码的 PCM 数据
    play(base64Data) {
        const binaryString = atob(base64Data);
        const len = binaryString.length;
        const bytes = new Uint8Array(len);
        for (let i = 0; i < len; i++) {
            bytes[i] = binaryString.charCodeAt(i);
        }
        
        // 转换为 Float32Array
        const pcmData = new Int16Array(bytes.buffer);
        const floatData = new Float32Array(pcmData.length);
        for (let i = 0; i < pcmData.length; i++) {
            floatData[i] = pcmData[i] / 0x7FFF;
        }
        
        this.bufferQueue.push(floatData);
        this.playNext();
    }
    
    playNext() {
        if (this.isPlaying || this.bufferQueue.length === 0) return;
        
        this.isPlaying = true;
        const floatData = this.bufferQueue.shift();
        
        const audioBuffer = this.audioContext.createBuffer(
            this.channels,
            floatData.length,
            this.sampleRate
        );
        audioBuffer.copyToChannel(floatData, 0);
        
        const source = this.audioContext.createBufferSource();
        source.buffer = audioBuffer;
        source.connect(this.audioContext.destination);
        source.onended = () => {
            this.isPlaying = false;
            this.playNext();
        };
        source.start();
    }
    
    close() {
        if (this.audioContext) {
            this.audioContext.close();
        }
    }
}
```

**可信度说明**：PCM 音频播放方案参考了企业级 Vue + PCM-Player 实践。

### 5.4 视频帧采集与发送

```javascript
// frontend/videoCapture.js
class VideoCapture {
    constructor(fps = 1) {
        this.fps = fps;  // 每秒采集帧数
        this.stream = null;
        this.videoElement = null;
        this.canvas = null;
        this.intervalId = null;
        this.onImageData = null;
    }
    
    async start(videoElementId) {
        this.videoElement = document.getElementById(videoElementId);
        
        this.stream = await navigator.mediaDevices.getUserMedia({
            video: {
                width: 640,
                height: 480,
                frameRate: { ideal: this.fps }
            }
        });
        
        this.videoElement.srcObject = this.stream;
        await this.videoElement.play();
        
        // 创建 canvas 用于捕获帧
        this.canvas = document.createElement('canvas');
        this.canvas.width = 640;
        this.canvas.height = 480;
        const ctx = this.canvas.getContext('2d');
        
        // 定时捕获帧
        this.intervalId = setInterval(() => {
            ctx.drawImage(this.videoElement, 0, 0, 640, 480);
            const base64 = this.canvas.toDataURL('image/jpeg', 0.8).split(',')[1];
            
            if (this.onImageData) {
                this.onImageData(base64);
            }
        }, 1000 / this.fps);
    }
    
    stop() {
        if (this.intervalId) {
            clearInterval(this.intervalId);
        }
        if (this.stream) {
            this.stream.getTracks().forEach(track => track.stop());
        }
    }
}
```

### 5.5 前端整合示例（Vue 3）

```vue
<!-- frontend/InterviewRoom.vue -->
<template>
  <div class="interview-room">
    <video ref="videoRef" autoplay playsinline></video>
    <div class="subtitle">{{ currentSubtitle }}</div>
    <div class="controls">
      <button @click="startInterview">开始面试</button>
      <button @click="endInterview">结束面试</button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue';
import { InterviewWebSocket } from './websocket';
import { AudioCapture } from './audioCapture';
import { PCMPlayer } from './audioPlayer';
import { VideoCapture } from './videoCapture';

const videoRef = ref(null);
const currentSubtitle = ref('');

let ws = null;
let audioCapture = null;
let audioPlayer = null;
let videoCapture = null;

const startInterview = async () => {
  const sessionId = `interview_${Date.now()}`;
  
  // 初始化 WebSocket
  ws = new InterviewWebSocket(sessionId);
  ws.connect();
  
  // 初始化音频播放器
  audioPlayer = new PCMPlayer({ sampleRate: 16000 });
  audioPlayer.init();
  
  // 初始化音频采集
  audioCapture = new AudioCapture(16000);
  audioCapture.onAudioData = (base64) => {
    ws.sendAudio(base64);
  };
  await audioCapture.start();
  
  // 初始化视频采集（每秒 1 帧）
  videoCapture = new VideoCapture(1);
  videoCapture.onImageData = (base64) => {
    ws.sendImage(base64);
  };
  await videoCapture.start('videoRef');
  
  // 设置消息处理
  ws.handleMessage = (data) => {
    if (data.type === 'audio') {
      audioPlayer.play(data.data);
    } else if (data.type === 'text') {
      currentSubtitle.value += data.data;
    }
  };
};

const endInterview = () => {
  audioCapture?.stop();
  videoCapture?.stop();
  audioPlayer?.close();
  ws?.ws?.close();
};

onUnmounted(() => {
  endInterview();
});
</script>
```


## 六、RAG 知识库集成

### 6.1 RAG 架构设计

在 AI 面试官系统中，RAG（检索增强生成）用于为模型注入**企业私有知识**，包括：
- 公司介绍、企业文化、业务范围
- 岗位描述（JD）、技术要求、能力模型
- 面试题库、标准答案参考
- 历史面试记录、最佳实践

**两种集成方案**：

| 方案 | 优点 | 缺点 | 适用场景 |
|------|------|------|----------|
| **百炼云端 RAG** | 开箱即用，免运维，检索质量高 | 数据需上传云端 | 快速上线，数据敏感度低 |
| **本地向量检索** | 数据本地存储，灵活可控 | 需自建检索服务 | 数据合规要求高，需要定制 |

### 6.2 方案一：百炼云端 RAG 集成

**步骤 1：创建知识索引**

1. 登录 [百炼控制台](https://bailian.console.aliyun.com/)
2. 左侧导航栏选择“数据应用” → “知识索引”
3. 点击“创建知识库”，输入名称，上传企业文档（支持 PDF、Word、TXT 等格式）
4. 等待文档解析完成，获取**知识索引 ID**（pipeline_id）

**步骤 2：创建 RAG 应用**

1. 左侧导航栏选择“我的应用” → “新增应用” → “智能体应用”
2. 选择模型（推荐 `qwen-max` 或 `qwen-plus`）
3. 打开“知识库检索增强”开关，选择上一步创建的知识库
4. 发布应用，获取**应用 ID**（app_id）

**步骤 3：后端调用 RAG 应用**

```python
# backend/rag_client.py
import os
from http import HTTPStatus
from dashscope import Application

class RAGClient:
    def __init__(self, app_id=None):
        # 从环境变量获取应用 ID，或直接传入
        self.app_id = app_id or os.getenv("BAILIAN_APP_ID")
        self.api_key = os.getenv("DASHSCOPE_API_KEY")
    
    def retrieve(self, query: str) -> dict:
        """
        调用百炼 RAG 应用进行检索
        
        Args:
            query: 检索查询文本（例如面试官想了解岗位要求）
            
        Returns:
            dict: 包含检索结果和生成的回答
        """
        response = Application.call(
            app_id=self.app_id,
            prompt=query,
            api_key=self.api_key
        )
        
        if response.status_code != HTTPStatus.OK:
            return {
                "success": False,
                "error": response.message,
                "request_id": response.request_id
            }
        
        return {
            "success": True,
            "output": response.output,
            "usage": response.usage,
            "request_id": response.request_id
        }
    
    async def retrieve_and_inject(self, query: str, conversation):
        """
        检索知识并注入到面试对话上下文中
        
        使用方式：在面试官需要专业知识的时机（如出题、评估回答）调用此方法，
        将检索结果作为 context 注入到 instructions 中。
        """
        result = self.retrieve(query)
        
        if result["success"]:
            # 将检索到的知识临时注入会话（通过追加系统消息）
            context = result["output"].get("text", "")
            conversation.send(json.dumps({
                "type": "conversation.item.create",
                "item": {
                    "type": "message",
                    "role": "system",
                    "content": f"参考以下知识内容回答问题：\n{context}"
                }
            }))
        
        return result
```

**可信度说明**：调用代码参考了官方 RAG 应用示例。

### 6.3 方案二：本地向量检索 + 百炼 API

对于数据合规要求较高的场景，可选择本地存储向量数据：

```python
# backend/local_rag.py
import os
from langchain_community.embeddings import DashScopeEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import TextLoader, PDFPlumberLoader

class LocalRAG:
    def __init__(self, persist_dir="./vector_store"):
        self.persist_dir = persist_dir
        # 使用百炼提供的 Embedding API
        self.embeddings = DashScopeEmbeddings(
            model="text-embedding-v3",
            dashscope_api_key=os.getenv("DASHSCOPE_API_KEY")
        )
        self.vector_store = None
    
    def build_index(self, documents_path: str):
        """从本地文档构建向量索引"""
        # 加载文档
        documents = []
        for file in os.listdir(documents_path):
            if file.endswith('.txt'):
                loader = TextLoader(os.path.join(documents_path, file))
                documents.extend(loader.load())
            elif file.endswith('.pdf'):
                loader = PDFPlumberLoader(os.path.join(documents_path, file))
                documents.extend(loader.load())
        
        # 文档分块
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50
        )
        chunks = text_splitter.split_documents(documents)
        
        # 构建向量索引
        self.vector_store = FAISS.from_documents(chunks, self.embeddings)
        self.vector_store.save_local(self.persist_dir)
        
        return len(chunks)
    
    def load_index(self):
        """加载已有向量索引"""
        self.vector_store = FAISS.load_local(
            self.persist_dir,
            self.embeddings,
            allow_dangerous_deserialization=True
        )
    
    def retrieve(self, query: str, top_k: int = 3) -> list:
        """检索相关文档片段"""
        if not self.vector_store:
            self.load_index()
        
        docs = self.vector_store.similarity_search(query, k=top_k)
        return [{"content": doc.page_content, "metadata": doc.metadata} for doc in docs]
    
    def retrieve_as_context(self, query: str, top_k: int = 3) -> str:
        """将检索结果格式化为上下文文本"""
        results = self.retrieve(query, top_k)
        context = "\n\n".join([f"【知识片段 {i+1}】\n{r['content']}" for i, r in enumerate(results)])
        return context
```

**可信度说明**：本地 RAG 方案参考了阿里云官方文档中的本地知识库构建指南。向量数据库选型方面，FAISS 适合数据量小于千万级的本地部署场景，简单快速。

### 6.4 RAG 在面试流程中的集成时机

在面试流程中，RAG 检索建议在以下关键节点触发：

1. **开场阶段**：检索公司介绍和岗位描述，用于面试官自我介绍
2. **技术提问阶段**：检索题库和标准答案，辅助面试官出题和评估
3. **行为面试阶段**：检索企业文化相关文档，确保提问符合公司价值观
4. **候选人提问阶段**：检索公司福利、发展路径等信息，准确回答候选人疑问


## 七、部署清单与检查项

### 7.1 部署前检查

| 检查项 | 说明 | 状态 |
|--------|------|------|
| API Key 配置 | 已获取百炼 API Key 并配置到环境变量 | ☐ |
| SDK 版本 | DashScope SDK ≥1.23.9 | ☐ |
| Python 版本 | Python ≥3.8，推荐 3.10+ | ☐ |
| 网络连通性 | 能访问 wss://dashscope.aliyuncs.com/api-ws/v1/realtime | ☐ |
| RAG 知识库 | 已创建知识索引/本地向量库，并上传面试相关文档 | ☐ |
| 前端音频格式 | 确认前端输出为 16kHz、单声道、16-bit PCM | ☐ |

### 7.2 生产环境建议

- **容器化部署**：使用 Docker 打包后端服务，便于弹性伸缩
- **并发管理**：使用 Redis 管理 WebSocket 会话状态，支持多实例部署
- **日志监控**：集成阿里云 SLS 或自建日志系统，记录 API 调用和错误信息
- **安全加固**：
  - API Key 禁止写入前端代码，所有请求经后端中转
  - 启用 HTTPS/WSS 加密传输
  - 面试视频/音频数据加密存储
- **成本控制**：在百炼控制台设置 API 调用预算告警


## 八、常见问题排查

| 问题现象 | 可能原因 | 解决方案 |
|----------|----------|----------|
| WebSocket 连接失败 | API Key 无效或网络不通 | 检查 API Key 是否正确，确认网络可访问阿里云 |
| 模型无音频输出 | `output_modalities` 未包含 AUDIO | 检查 `update_session` 配置 |
| 回声触发误打断 | 扬声器声音被麦克风拾取 | 使用耳机播放音频 |
| 音频播放卡顿 | 前端缓冲区不足或网络延迟 | 调整 PCMPlayer 的缓冲队列长度 |
| RAG 检索无结果 | 知识库未解析完成或查询词不匹配 | 确认文档解析状态，优化查询措辞 |
| VAD 不生效 | `enable_turn_detection` 未设为 True | 检查 `update_session` 配置 |
| 会话超时断开 | 超过 120 分钟会话限制 | 实现自动重连机制，重新创建会话 |

**可信度说明**：VAD 配置和回声问题来自官方文档。


## 九、附录：参考资源

### 9.1 官方文档

- **Qwen-Omni Realtime API 官方文档**：https://help.aliyun.com/zh/model-studio/realtime
- **Python SDK 文档**：https://help.aliyun.com/zh/model-studio/omni-realtime-python-sdk
- **Java SDK 文档**：https://www.alibabacloud.com/help/zh/model-studio/omni-realtime-java-sdk
- **官方示例代码仓库**：https://github.com/aliyun/alibabacloud-bailian-speech-demo
- **本地知识库 RAG 构建指南**：https://help.aliyun.com/zh/model-studio/build-rag-application-based-on-local-retrieval

### 9.2 音色列表

| 音色名称 | 适用模型 | 特点 |
|----------|----------|------|
| Cherry | Qwen3-Omni-Flash-Realtime（默认） | 温柔、自然的女声 |
| Chelsie | Qwen-Omni-Turbo-Realtime（默认） | 清晰、专业的女声 |
| Ethan | 全系列支持 | 稳重、成熟的男声 |
| Sophie | 全系列支持 | 亲切、活泼的女声 |

完整音色列表请参考：https://help.aliyun.com/zh/model-studio/realtime#f9c68d860a3rs 

### 9.3 模型版本说明

| 模型名称 | 推荐场景 | 特点 |
|----------|----------|------|
| `qwen3.5-omni-flash-realtime` | 生产环境（推荐） | 延迟最低，性价比高 |
| `qwen3.5-omni-plus-realtime` | 高要求场景 | 效果最优，延迟略高 |
| `qwen3.5-omni-light-realtime` | 快速原型验证 | 延迟极低，能力基础 |


## 十、版本记录

| 版本 | 日期 | 修改内容 | 修改人 |
|------|------|----------|--------|
| v1.0 | 2026-04-13 | 初始版本，涵盖后端部署、前端对接、RAG 集成 | - |


> **说明**：本部署文档中标注“可信度说明”的部分，其信息来源于官方文档或经过交叉验证的技术资料；未标注的部分为基于通用工程实践的建议性内容，开发者可根据实际情况调整。