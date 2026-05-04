import os
import json
import base64
import logging
import asyncio
import threading
import time
import queue
import cv2
import numpy as np
from PIL import Image
import io
from typing import Dict, List, Optional, Callable, Any
from dashscope.audio.qwen_omni import OmniRealtimeConversation, OmniRealtimeCallback, MultiModality, AudioFormat
import dashscope

from ..config.default import (
    VIDEO_CHAT_API_KEY, VIDEO_CHAT_MODEL, VIDEO_CHAT_WS_URL,
    VIDEO_CHAT_VOICE, VIDEO_CHAT_ENABLED, VIDEO_CHAT_SAMPLE_RATE,
    VIDEO_CHAT_AUDIO_CHUNK_SIZE, VIDEO_CHAT_MAX_IMAGE_SIZE,
    VIDEO_CHAT_IMAGE_FORMAT, VIDEO_CHAT_IMAGE_QUALITY, VIDEO_CHAT_FPS,
    RAG_ENABLED, RAG_TOP_K, RAG_SERVICE_URL, RAG_MODE
)

logger = logging.getLogger(__name__)
MEDIA_DETAIL_LOG_INTERVAL_SECONDS = 30.0
_last_media_detail_log_times = {
    'image_send': 0.0,
    'warmup': 0.0,
}
MANUAL_TURN_SILENCE_SECONDS = 1.5
MANUAL_TURN_MIN_SPEECH_SECONDS = 0.8
PCM_SPEECH_THRESHOLD = 1200
MIN_RESPONSE_INTERVAL = 3.0
AI_SPEECH_COOLDOWN_AFTER_DONE = 2.0
AI_SPEECH_MAX_DURATION = 30.0


def _should_log_media_detail(kind: str) -> bool:
    now = time.time()
    last_logged_at = _last_media_detail_log_times.get(kind, 0.0)
    if now - last_logged_at >= MEDIA_DETAIL_LOG_INTERVAL_SECONDS:
        _last_media_detail_log_times[kind] = now
        return True
    return False

# 设置DashScope API密钥
dashscope.api_key = VIDEO_CHAT_API_KEY


class VideoChatCallback(OmniRealtimeCallback):
    """视频聊天回调处理类"""
    
    def __init__(self, session_id: str, websocket_handler=None):
        super().__init__()
        self.session_id = session_id
        self.websocket_handler = websocket_handler
        self.on_audio_callback = None
        self.on_text_callback = None
        self.on_video_callback = None
        self.on_done_callback = None
        self.on_error_callback = None
        self.on_interview_event_callback = None
        
        # 音频队列
        self.audio_queue = queue.Queue()
        self.is_playing = False
        self.last_response_text = ""
        self.connected_event = None  # 用于等待连接建立的Event对象
        self.response_received = False  # 跟踪是否收到response.created事件
        self.last_response_text = ""
        
    def on_open(self):
        logger.info(f"✅ [VideoChat] 连接成功建立: {self.session_id}")
        if self.connected_event:
            self.connected_event.set()
        
    def on_event(self, event: Dict):
        """处理模型返回的各类事件"""
        try:
            event_type = event.get('type')
            logger.info(f"🔔 [VideoChat] 收到事件类型: {event_type}")
            
            # 记录事件序列和时间间隔
            current_time = time.time()
            if not hasattr(self, 'last_event_time'):
                self.last_event_time = current_time
            time_since_last_event = current_time - self.last_event_time
            logger.info(f"⏱️ [VideoChat] 事件时间间隔: {time_since_last_event:.3f}秒")
            self.last_event_time = current_time
            
            # 检查是否在等待AI响应但长时间未收到
            if hasattr(self, 'assistant_item_created_time'):
                logger.info(f"🔍 [VideoChat] 调试 - assistant_item_created_time存在: {self.assistant_item_created_time}")
                logger.info(f"🔍 [VideoChat] 调试 - response_received值: {self.response_received}")
                logger.info(f"🔍 [VideoChat] 调试 - 当前时间: {current_time}")
                logger.info(f"🔍 [VideoChat] 调试 - 时间差: {current_time - self.assistant_item_created_time:.3f}秒")
                
                if not self.response_received:
                    time_since_assistant_item = current_time - self.assistant_item_created_time
                    logger.info(f"🔍 [VideoChat] 调试 - 检查超时: {time_since_assistant_item:.3f}秒 > 5.0秒? {time_since_assistant_item > 5.0}")
                    if time_since_assistant_item > 5.0:  # 5秒后仍未收到响应
                        logger.warning(f"⏰ [VideoChat] 警告：AI助理项创建已过去{time_since_assistant_item:.1f}秒，仍未收到response.created事件")
                        logger.warning(f"⚠️ [VideoChat] 可能原因：AI在等待输入，或VAD仍然启用，或指令不明确")
                        # 记录当前会话状态
                        logger.info(f"📊 [VideoChat] 当前已收到的事件类型: {self.received_event_types if hasattr(self, 'received_event_types') else '[]'}")
                        # 记录关键变量状态
                        logger.info(f"🔍 [VideoChat] 调试 - response_received状态: {self.response_received}")
                        logger.info(f"🔍 [VideoChat] 调试 - assistant_item_created_time: {self.assistant_item_created_time}")
                        logger.info(f"🔍 [VideoChat] 调试 - 当前时间: {current_time}")
            else:
                logger.info(f"🔍 [VideoChat] 调试 - assistant_item_created_time不存在")
            
            # 对于关键事件显示完整详情
            if event_type in ['response.created', 'response.done', 'conversation.item.created', 
                             'conversation.item.input_audio_transcription.completed', 
                             'input_audio_buffer.committed', 'session.updated', 'session.created']:
                logger.info(f"🔍 [VideoChat] 事件详情: {json.dumps(event, ensure_ascii=False, indent=2)}")
            
            # 记录时间戳用于调试
            if not hasattr(self, 'event_timestamps'):
                self.event_timestamps = {}
            self.event_timestamps[event_type] = current_time
            
            # 记录所有收到的事件类型
            if not hasattr(self, 'received_event_types'):
                self.received_event_types = []
            if event_type not in self.received_event_types:
                self.received_event_types.append(event_type)
                logger.info(f"📊 [VideoChat] 已收到的事件类型列表: {self.received_event_types}")
            
            # 添加事件序列分析
            if event_type == 'conversation.item.input_audio_transcription.completed':
                transcript = event.get('transcript', '')
                logger.info(f"🎤 [VideoChat] 语音识别结果: '{transcript}' (长度: {len(transcript)})")
                if transcript == "嗯。" or transcript == "嗯":
                    logger.warning(f"⚠️ [VideoChat] 静音帧可能被错误识别为语音: '{transcript}'")
                    logger.info(f"ℹ️ [VideoChat] 这可能意味着VAD检测到静音帧作为语音输入")
            
            if event_type == 'conversation.item.created':
                item = event.get('item', {})
                item_id = item.get('id', '未知')
                item_type = item.get('type', '未知')
                role = item.get('role', '未知')
                status = item.get('status', '未知')
                content = item.get('content', [])
                logger.info(f"📋 [VideoChat] 会话项创建: id={item_id}, type={item_type}, role={role}, status={status}")
                logger.info(f"📦 [VideoChat] 会话项内容: {json.dumps(content, ensure_ascii=False, indent=2)}")
                
                # 分析内容类型
                for i, content_item in enumerate(content):
                    content_type = content_item.get('type', '未知')
                    logger.info(f"📄 [VideoChat] 内容项 {i}: type={content_type}")
                    if content_type == 'input_audio':
                        logger.info(f"🎵 [VideoChat] 内容包含输入音频")
                    elif content_type == 'input_text':
                        text = content_item.get('text', '')
                        logger.info(f"📝 [VideoChat] 内容包含输入文本: '{text}'")
                    elif content_type == 'output_audio':
                        logger.info(f"🔊 [VideoChat] 内容包含输出音频")
                    elif content_type == 'output_text':
                        logger.info(f"📄 [VideoChat] 内容包含输出文本")
                
                if role == 'assistant' and status == 'in_progress':
                    logger.info(f"🤖 [VideoChat] AI助理项已创建，等待response.created事件...")
                    # 重置响应接收标志
                    self.response_received = False
                    logger.info(f"🔄 [VideoChat] 已重置response_received标志为False")
                    # 记录时间，用于后续检查是否收到response.created
                    if not hasattr(self, 'assistant_item_created_time'):
                        self.assistant_item_created_time = current_time
                        logger.info(f"⏰ [VideoChat] 记录助理项创建时间: {current_time}")
                    
                    # 检查是否有输入内容，如果没有，可能AI在等待输入
                    has_input = any(item.get('type') in ['input_audio', 'input_text'] for item in content)
                    if not has_input:
                        logger.warning(f"⚠️ [VideoChat] AI助理项没有输入内容，可能AI在等待输入")
                    else:
                        logger.info(f"✅ [VideoChat] AI助理项有输入内容，应该开始生成响应")
            
            if event_type == 'response.created':
                logger.info(f"🚀 [VideoChat] AI开始生成响应！这是关键事件")
                logger.info(f"🔍 [VideoChat] response.created事件详情: {json.dumps(event, ensure_ascii=False, indent=2)}")
                # 设置响应已接收标志
                self.response_received = True
                logger.info(f"✅ [VideoChat] 已设置response_received标志")
                # 检查从assistant item创建到response创建的时间
                if hasattr(self, 'assistant_item_created_time'):
                    time_to_response = current_time - self.assistant_item_created_time
                    logger.info(f"⏱️ [VideoChat] 从助理项创建到响应创建耗时: {time_to_response:.3f}秒")
            
            if event_type == 'error':
                error_msg = event.get('message', '未知错误')
                logger.error(f"❌ [VideoChat] API错误事件: {error_msg}")
                logger.info(f"🔍 [VideoChat] 错误事件详情: {json.dumps(event, ensure_ascii=False, indent=2)}")
            
            if event_type == 'response.audio.delta':
                # 音频增量数据
                audio_base64 = event.get('delta', '')
                logger.info(f"🔔 [VideoChat] 收到音频增量数据: size={len(audio_base64)} chars")
                if self.on_audio_callback:
                    self.on_audio_callback(audio_base64)
                if self.websocket_handler:
                    self.websocket_handler.send(json.dumps({
                        'type': 'audio',
                        'data': audio_base64
                    }))
                    
            elif event_type == 'response.text.delta':
                # 文本增量数据（用于字幕显示）
                text_chunk = event.get('delta', '')
                logger.info(f"🔔 [VideoChat] 收到文本增量数据: '{text_chunk}'")
                if self.on_text_callback:
                    self.on_text_callback(text_chunk)
                if self.websocket_handler:
                    self.websocket_handler.send(json.dumps({
                        'type': 'text',
                        'data': text_chunk
                    }))
                    
            elif event_type == 'response.audio_transcript.delta':
                # 音频转文字增量
                text_delta = event.get('delta', '')
                self.last_response_text += text_delta
                if self.on_text_callback:
                    self.on_text_callback(text_delta)
                if self.websocket_handler:
                    self.websocket_handler.send(json.dumps({
                        'type': 'text',
                        'data': text_delta
                    }))
                
            elif event_type == 'response.audio_transcript.done':
                # 音频转文字完成
                full_text = event.get('transcript', '')
                logger.info(f"🗣️ [VideoChat] AI回复文本: {full_text}")
                if full_text and self.on_text_callback and not self.last_response_text:
                    self.on_text_callback(full_text)
                self.last_response_text = ""
                if self.on_interview_event_callback:
                    self.on_interview_event_callback('ai_response', {'text': full_text})
                    
            elif event_type == 'conversation.item.input_audio_transcription.completed':
                # 用户语音转文字完成
                user_text = event.get('transcript', '')
                logger.info(f"🎤 [VideoChat] 用户语音转文字: {user_text}")
                if self.on_interview_event_callback:
                    self.on_interview_event_callback('user_speech', {'text': user_text})
                    
            elif event_type == 'response.created':
                # AI开始回复
                self.is_playing = True
                if self.on_interview_event_callback:
                    self.on_interview_event_callback('ai_start', {})
                    
            elif event_type == 'response.done':
                # 一次响应完成
                self.is_playing = False
                if self.on_done_callback:
                    self.on_done_callback()
                if self.on_interview_event_callback:
                    self.on_interview_event_callback('ai_end', {})
                    
            elif event_type == 'session.created':
                logger.info(f"✅ [VideoChat] 会话创建成功: {event.get('session', {}).get('id')}")
                
            elif event_type == 'session.updated':
                logger.info(f"🔄 [VideoChat] 会话配置已更新: {event.get('session', {}).get('id')}")
                # 检查turn_detection配置
                session_data = event.get('session', {})
                if 'turn_detection' in session_data:
                    turn_detection = session_data.get('turn_detection', {})
                    logger.info(f"🔍 [VideoChat] turn_detection配置: {turn_detection}")
                    # 检查是否启用了VAD
                    if turn_detection.get('type') == 'server_vad':
                        logger.info(f"⚠️ [VideoChat] VAD已启用，AI将等待用户说话")
                        # 检查create_response设置
                        create_response = turn_detection.get('create_response', True)
                        logger.info(f"🔧 [VideoChat] create_response: {create_response}")
                    else:
                        logger.info(f"✅ [VideoChat] VAD未启用或已禁用")
                else:
                    logger.warning(f"⚠️ [VideoChat] session.updated事件中没有turn_detection字段")
                    # 检查整个session对象的内容
                    logger.info(f"🔍 [VideoChat] session.updated事件完整session对象: {json.dumps(session_data, ensure_ascii=False, indent=2)}")
                
            elif event_type == 'error':
                error_msg = event.get('message', '未知错误')
                logger.error(f"❌ [VideoChat] 事件错误: {error_msg}")
                if self.on_error_callback:
                    self.on_error_callback(error_msg)
                    
        except Exception as e:
            logger.error(f"❌ [VideoChat] 处理事件失败: {str(e)}")
            if self.on_error_callback:
                self.on_error_callback(str(e))
                
    def on_close(self, close_status_code: int, close_msg: str):
        logger.info(f"🔌 [VideoChat] 连接关闭: code={close_status_code}, msg={close_msg}")
        
    def on_error(self, error):
        logger.error(f"❌ [VideoChat] 错误: {error}")
        if self.on_error_callback:
            self.on_error_callback(str(error))


class VideoInterviewSession:
    """视频面试会话管理类"""
    
    def __init__(self, session_id: str, interview_id: str, position: str, 
                 job_info: Optional[Dict] = None, company_info: Optional[Dict] = None):
        self.session_id = session_id
        self.interview_id = interview_id
        self.position = position
        self.job_info = job_info or {}
        self.company_info = company_info or {}
        self.conversation = None
        self.callback = None
        self.is_active = False
        self.audio_buffer = bytearray()
        self.video_buffer = queue.Queue(maxsize=10)
        self.video_thread = None
        self.stop_video = threading.Event()
        self.audio_sent = False  # 跟踪是否已发送音频帧
        self.startup_warmup_thread = None
        self.stop_startup_warmup = threading.Event()
        self.initial_response_requested = False
        self.last_user_response_request_at = 0.0
        self.manual_turn_active = False
        self.manual_turn_started_at = 0.0
        self.manual_turn_last_voice_at = 0.0
        self.ai_is_speaking = False
        self.ai_speaking_done_at = 0.0
        self.ai_speaking_started_at = 0.0
        
        # RAG集成
        self.rag_integration = None
        if RAG_ENABLED:
            try:
                from .rag_service import RagService
                self.rag_service = RagService()
                logger.info(f"[VideoChat] RAG服务已初始化")
            except Exception as e:
                logger.error(f"[VideoChat] 初始化RAG服务失败: {e}")
                self.rag_service = None
        else:
            self.rag_service = None
        
    def create_conversation(self, callback: VideoChatCallback):
        """创建Omni-Realtime会话"""
        logger.info(f"🔍 [VideoChat] DEBUG: 开始创建会话, VIDEO_CHAT_ENABLED={VIDEO_CHAT_ENABLED}, VIDEO_CHAT_MODEL={VIDEO_CHAT_MODEL}")
        logger.info(f"🔍 [VideoChat] DEBUG: VIDEO_CHAT_API_KEY前10位: {VIDEO_CHAT_API_KEY[:10]}...")
        logger.info(f"🔍 [VideoChat] DEBUG: VIDEO_CHAT_WS_URL={VIDEO_CHAT_WS_URL}")
        
        if not VIDEO_CHAT_ENABLED:
            logger.error(f"❌ [VideoChat] 视频聊天服务未启用!")
            raise Exception("视频聊天服务未启用")
            
        logger.info(f"[VideoChat] 创建会话: enabled={VIDEO_CHAT_ENABLED}, model={VIDEO_CHAT_MODEL}, url={VIDEO_CHAT_WS_URL}")
        self.callback = callback
        
        try:
            self.conversation = OmniRealtimeConversation(
                model=VIDEO_CHAT_MODEL,
                callback=callback,
                url=VIDEO_CHAT_WS_URL
            )
            logger.info(f"✅ [VideoChat] 会话已创建: {self.session_id}, 模型: {VIDEO_CHAT_MODEL}")
            
            # 设置连接事件并建立连接
            import threading
            callback.connected_event = threading.Event()
            
            logger.info(f"🔗 [VideoChat] 正在连接DashScope WebSocket...")
            self.conversation.connect()
            
            # 等待连接建立（最多10秒）
            if callback.connected_event.wait(timeout=10):
                logger.info(f"✅ [VideoChat] WebSocket连接已建立: {self.session_id}")
                logger.info(f"✅ [VideoChat] ws对象: {self.conversation.ws}")
                return self.conversation
            else:
                logger.error(f"❌ [VideoChat] 连接超时: 在10秒内未建立连接")
                raise Exception("连接DashScope超时")
                
        except Exception as e:
            logger.error(f"❌ [VideoChat] 创建会话失败: {str(e)}")
            logger.error(f"❌ [VideoChat] API Key: {VIDEO_CHAT_API_KEY[:10]}... (隐藏)")
            logger.error(f"❌ [VideoChat] Model: {VIDEO_CHAT_MODEL}")
            logger.error(f"❌ [VideoChat] URL: {VIDEO_CHAT_WS_URL}")
            raise Exception(f"创建视频聊天会话失败: {str(e)}")
        
    def configure_interviewer(self):
        """配置面试官的会话参数"""
        if not self.conversation:
            raise Exception("会话未创建")
        
        try:
            instructions = self._build_instructions()
            
            logger.info(f"🔄 [VideoChat] 正在更新会话配置...")
            logger.info(f"📝 [VideoChat] 配置参数:")
            logger.info(f"  - output_modalities: [AUDIO, TEXT]")
            logger.info(f"  - voice: Ethan")
            logger.info(f"  - instructions: {instructions}")
            logger.info(f"  - enable_turn_detection: False (主动开场模式)")
            
            # 更新会话配置 - 禁用VAD，让AI先开场
            update_params = {
                'output_modalities': [MultiModality.AUDIO, MultiModality.TEXT],
                'voice': 'Ethan',
                'instructions': instructions,
                'enable_turn_detection': False,
                'input_audio_format': AudioFormat.PCM_16000HZ_MONO_16BIT,
                'output_audio_format': AudioFormat.PCM_24000HZ_MONO_16BIT,
                'smooth_output': True,
                'enable_input_audio_transcription': True,
                'enable_output_audio_transcription': True
            }
            logger.info(f"📤 [VideoChat] 发送更新会话参数: {json.dumps(update_params, ensure_ascii=False, default=str)}")
            
            self.conversation.update_session(**update_params)
            logger.info(f"✅ [VideoChat] 会话配置更新完成（主动开场模式）")
            
            logger.info(f"✅ [VideoChat] 面试官会话已配置: {self.session_id}, 岗位: {self.position}")
            
            self.audio_sent = False
            logger.info(f"ℹ️ [VideoChat] 会话已配置，启动后将发送初始静音帧触发首轮响应")
            
        except Exception as e:
            logger.error(f"❌ [VideoChat] 配置会话失败: {str(e)}")
            raise
        
    def _build_instructions(self) -> str:
        """构建系统提示词"""
        if self.position:
            instructions = f"""你是一个专业的{self.position}岗位的AI面试官，正在进行视频面试。你可以看到候选人的视频画面。

【核心原则 - 必须严格遵守】
1. 你只负责提问和评估，绝对不要回答自己提出的问题
2. 每次只提出一个问题，等待候选人回答后再继续
3. 不要在问题中暗示答案、给出选项或自己解释答案
4. 保持面试官的角色定位：提问 → 倾听 → 追问，不要变成"讲解者"
5. 如果候选人回答不完整，请通过追问引导，而不是直接补充答案

【面试流程】
1. 第一句话必须是："你好，我是面试官，我们现在开始面试。"
2. 然后根据{self.position}岗位的要求，逐轮提出面试问题
3. 根据候选人的回答质量，灵活调整问题难度和方向"""

        else:
            instructions = """你是一个AI助手，正在进行测试。你可以看到视频画面。

请立即开始说话，不要等待任何用户输入。你的第一句话必须是："测试成功，我可以说话了。"然后等待进一步指令。"""
        
        logger.info(f"📝 [VideoChat] 构建的指令内容: {instructions}")
        return instructions
        
    def _get_rag_collection(self) -> str:
        """根据岗位类型获取对应的RAG集合"""
        position = self.position.lower()
        if 'frontend' in position or '前端' in position or 'web' in position:
            return 'web_frontend'
        elif 'backend' in position or '后端' in position or 'java' in position:
            return 'java_backend'
        elif 'fullstack' in position or 'full_stack' in position or '全栈' in position:
            return 'fullstack_engineer'
        elif 'bigdata' in position or 'big_data' in position or '大数据' in position:
            return 'bigdata_engineer'
        else:
            return 'java_backend'
        
    def start(self):
        """启动会话（兼容性方法，实际连接在update_session时建立）"""
        if not self.conversation:
            raise Exception("会话未创建")
            
        logger.info(f"🚀 [VideoChat] 正在启动会话...")
        logger.info(f"📊 [VideoChat] 会话状态检查:")
        logger.info(f"  - conversation对象: {self.conversation}")
        logger.info(f"  - is_active当前值: {self.is_active}")
        logger.info(f"  - audio_sent: {self.audio_sent}")
        
        # OmniRealtimeConversation没有start方法，连接在发送第一个消息时建立
        self.is_active = True
        logger.info(f"✅ [VideoChat] 会话已激活: {self.session_id}, is_active={self.is_active}")
        
        if not self.audio_sent:
            try:
                empty_audio = b'\x00' * 320  # 20ms静音帧
                audio_base64 = base64.b64encode(empty_audio).decode('utf-8')
                self.conversation.append_audio(audio_base64)
                self.audio_sent = True
                logger.info(f"✅ [VideoChat] 已发送初始静音帧，触发AI主动开场")
            except Exception as e:
                logger.warning(f"⚠️ [VideoChat] 发送初始静音帧失败: {e}")

        self._request_initial_response()
        self._start_startup_warmup()

    def _request_initial_response(self):
        """在关闭VAD的模式下，显式提交输入并要求模型开始响应。"""
        if self.initial_response_requested:
            return
        if not self.conversation or not self.is_active:
            return

        try:
            logger.info("🚀 [VideoChat] 显式提交初始输入缓冲区")
            self.conversation.commit()
            logger.info("🚀 [VideoChat] 显式请求模型生成首轮回复")
            self.conversation.create_response(
                output_modalities=[MultiModality.AUDIO, MultiModality.TEXT]
            )
            self.initial_response_requested = True
            self.ai_is_speaking = True
            self.ai_speaking_started_at = time.time()
            self.last_user_response_request_at = time.time()
            logger.info("✅ [VideoChat] 首轮response.create已发送，AI说话状态已锁定")
        except Exception as e:
            logger.warning(f"⚠️ [VideoChat] 显式触发首轮回复失败: {e}")

    def _start_startup_warmup(self):
        """在会话启动后的短窗口内持续发送静音帧，逼近测试脚本行为。"""
        if self.startup_warmup_thread and self.startup_warmup_thread.is_alive():
            return

        self.stop_startup_warmup.clear()

        def _worker():
            max_duration_seconds = 6.0
            interval_seconds = 0.2
            start_time = time.time()
            frames_sent = 0
            logger.info("🔄 [VideoChat] 启动静音预热线程")

            while not self.stop_startup_warmup.is_set():
                if not self.conversation or not self.is_active:
                    break

                if self.callback and getattr(self.callback, 'response_received', False):
                    logger.info("✅ [VideoChat] 已收到response.created，停止静音预热")
                    break

                if time.time() - start_time >= max_duration_seconds:
                    logger.info("⏹️ [VideoChat] 静音预热超时结束")
                    break

                try:
                    empty_audio = b'\x00' * 320
                    audio_base64 = base64.b64encode(empty_audio).decode('utf-8')
                    self.conversation.append_audio(audio_base64)
                    frames_sent += 1
                    if frames_sent == 1 or (frames_sent % 5 == 0 and _should_log_media_detail('warmup')):
                        logger.info(f"🎤 [VideoChat] 预热静音帧已发送: {frames_sent}")
                except Exception as e:
                    logger.warning(f"⚠️ [VideoChat] 预热静音帧发送失败: {e}")
                    break

                time.sleep(interval_seconds)

            logger.info(f"✅ [VideoChat] 静音预热线程结束，共发送{frames_sent}帧")

        self.startup_warmup_thread = threading.Thread(
            target=_worker,
            name=f"video-chat-warmup-{self.session_id}",
            daemon=True
        )
        self.startup_warmup_thread.start()

    def trigger_followup_response(self, transcript: str = ""):
        """在禁用VAD时，根据用户转写手动触发下一轮回复。"""
        if not self.conversation or not self.is_active:
            return

        cleaned_text = (transcript or "").strip()
        if not cleaned_text:
            logger.info("ℹ️ [VideoChat] 用户转写为空，跳过后续response.create")
            return

        if cleaned_text in {"嗯", "嗯。", "呃", "呃。", "啊", "啊。"}:
            logger.info(f"ℹ️ [VideoChat] 用户转写疑似静音误识别，跳过: {cleaned_text!r}")
            return

        now = time.time()
        if now - self.last_user_response_request_at < 1.0:
            logger.info("ℹ️ [VideoChat] response.create触发过于频繁，本次跳过")
            return

        try:
            logger.info(f"🚀 [VideoChat] 为用户输入触发新一轮回复: {cleaned_text!r}")
            self.conversation.commit()
            self.conversation.create_response(
                output_modalities=[MultiModality.AUDIO, MultiModality.TEXT]
            )
            self.last_user_response_request_at = now
        except Exception as e:
            logger.warning(f"⚠️ [VideoChat] 触发后续回复失败: {e}")

    def _pcm_has_speech(self, audio_data: bytes) -> bool:
        """非常粗略的语音活动检测，用于手动commit后续轮次。"""
        if len(audio_data) < 2:
            return False
        pcm = np.frombuffer(audio_data, dtype=np.int16)
        if pcm.size == 0:
            return False
        peak = int(np.max(np.abs(pcm)))
        return peak >= PCM_SPEECH_THRESHOLD

    def _maybe_commit_manual_turn(self, audio_data: bytes):
        """在关闭VAD时，用简单静音检测切分用户后续发言。"""
        if not self.conversation or not self.is_active:
            return

        now = time.time()

        if self.ai_is_speaking:
            if self.ai_speaking_started_at > 0 and now - self.ai_speaking_started_at > AI_SPEECH_MAX_DURATION:
                logger.warning(f"⚠️ [VideoChat] AI说话超时({AI_SPEECH_MAX_DURATION}s)，强制释放锁")
                self.ai_is_speaking = False
                self.ai_speaking_done_at = now
                self.ai_speaking_started_at = 0.0
            else:
                return

        if self.ai_speaking_done_at > 0 and now - self.ai_speaking_done_at < AI_SPEECH_COOLDOWN_AFTER_DONE:
            return

        if now - self.last_user_response_request_at < MIN_RESPONSE_INTERVAL:
            return

        has_speech = self._pcm_has_speech(audio_data)

        if has_speech:
            if now - self.ai_speaking_done_at < AI_SPEECH_COOLDOWN_AFTER_DONE:
                self.manual_turn_active = False
                self.manual_turn_started_at = 0.0
                self.manual_turn_last_voice_at = 0.0
                return
            if not self.manual_turn_active:
                self.manual_turn_active = True
                self.manual_turn_started_at = now
                logger.info("🎙️ [VideoChat] 检测到用户开始说话")
            self.manual_turn_last_voice_at = now
            return

        if not self.manual_turn_active:
            return

        speech_duration = self.manual_turn_last_voice_at - self.manual_turn_started_at
        silence_duration = now - self.manual_turn_last_voice_at
        if speech_duration < MANUAL_TURN_MIN_SPEECH_SECONDS:
            return
        if silence_duration < MANUAL_TURN_SILENCE_SECONDS:
            return
        if now - self.last_user_response_request_at < MIN_RESPONSE_INTERVAL:
            return

        try:
            logger.info(
                f"🚀 [VideoChat] 手动检测到用户发言结束，提交下一轮输入: "
                f"speech={speech_duration:.2f}s silence={silence_duration:.2f}s"
            )
            self.conversation.commit()
            self.conversation.create_response(
                output_modalities=[MultiModality.AUDIO, MultiModality.TEXT]
            )
            self.last_user_response_request_at = now
            self.ai_is_speaking = True
            self.ai_speaking_started_at = now
        except Exception as e:
            logger.warning(f"⚠️ [VideoChat] 手动提交用户发言失败: {e}")
        finally:
            self.manual_turn_active = False
            self.manual_turn_started_at = 0.0
            self.manual_turn_last_voice_at = 0.0
        
    def send_audio(self, audio_data: bytes):
        """发送音频数据
        注意：音频帧应为800字节（25ms @ 16kHz）或320字节（20ms @ 16kHz）
        """
        if not self.is_active or not self.conversation:
            raise Exception("会话未激活")
            
        # 验证音频帧大小
        expected_sizes = [320, 800]  # 20ms和25ms
        if len(audio_data) not in expected_sizes:
            logger.warning(f"⚠️ [VideoChat] 音频帧大小不标准: {len(audio_data)}字节, 期望: {expected_sizes}")
            
        # 将音频数据编码为base64
        audio_base64 = base64.b64encode(audio_data).decode('utf-8')
        self.conversation.append_audio(audio_base64)
        # 设置音频已发送标志
        self.audio_sent = True
        self._maybe_commit_manual_turn(audio_data)
        
    def send_image(self, image_base64: str):
        """发送图像数据
        重要：必须在发送音频帧之后调用，否则会触发"Error append image before append audio"错误
        """
        if not self.is_active or not self.conversation:
            raise Exception("会话未激活")
        
        # 检查是否已发送音频帧，如果没有则先发送一个空音频帧
        if not self.audio_sent:
            logger.info(f"🔔 [VideoChat] 尚未发送音频帧，先发送空音频帧初始化...")
            try:
                empty_audio = b'\x00' * 320  # 20ms静音帧
                audio_base64 = base64.b64encode(empty_audio).decode('utf-8')
                self.conversation.append_audio(audio_base64)
                self.audio_sent = True
                logger.info(f"✅ [VideoChat] 已发送空音频帧初始化音频流")
            except Exception as e:
                logger.warning(f"⚠️ [VideoChat] 发送初始音频帧失败: {e}")
                # 继续尝试发送图像，但可能失败
            
        try:
            self.conversation.append_video(image_base64)
            if _should_log_media_detail('image_send'):
                logger.info(f"🖼️ [VideoChat] 图像数据发送正常: size={len(image_base64)} chars")
        except Exception as e:
            logger.error(f"❌ [VideoChat] 发送图像数据失败: {e}")
            raise
        
    def send_video_frame(self, frame_data: bytes):
        """发送视频帧数据
        重要：必须在发送音频帧之后调用，否则会触发"Error append image before append audio"错误
        """
        if not self.is_active or not self.conversation:
            raise Exception("会话未激活")
        
        # 检查是否已发送音频帧，如果没有则先发送一个空音频帧
        if not self.audio_sent:
            logger.info(f"🔔 [VideoChat] 尚未发送音频帧，先发送空音频帧初始化...")
            try:
                empty_audio = b'\x00' * 320  # 20ms静音帧
                audio_base64 = base64.b64encode(empty_audio).decode('utf-8')
                self.conversation.append_audio(audio_base64)
                self.audio_sent = True
                logger.info(f"✅ [VideoChat] 已发送空音频帧初始化音频流")
            except Exception as e:
                logger.warning(f"⚠️ [VideoChat] 发送初始音频帧失败: {e}")
                # 继续尝试发送图像，但可能失败
            
        # 将图像数据转换为base64
        image_base64 = base64.b64encode(frame_data).decode('utf-8')
        self.conversation.append_video(image_base64)
        # 注意：参考文件没有调用commit()，先注释掉
        # self.conversation.commit()
        
    def prepare_video_frame(self, frame: np.ndarray) -> Optional[bytes]:
        """准备视频帧数据，压缩为JPEG格式"""
        try:
            # 转换BGR到RGB
            if len(frame.shape) == 3 and frame.shape[2] == 3:
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            else:
                rgb_frame = frame
                
            # 创建PIL图像
            pil_image = Image.fromarray(rgb_frame)
            
            # 调整大小（如果需要）
            max_dimension = 720  # 推荐720P
            if max(pil_image.size) > max_dimension:
                ratio = max_dimension / max(pil_image.size)
                new_size = tuple(int(dim * ratio) for dim in pil_image.size)
                pil_image = pil_image.resize(new_size, Image.Resampling.LANCZOS)
            
            # 保存为JPEG字节流
            img_byte_arr = io.BytesIO()
            pil_image.save(img_byte_arr, format=VIDEO_CHAT_IMAGE_FORMAT, 
                          quality=VIDEO_CHAT_IMAGE_QUALITY, optimize=True)
            img_data = img_byte_arr.getvalue()
            
            # 检查大小
            if len(img_data) > VIDEO_CHAT_MAX_IMAGE_SIZE:
                # 进一步压缩
                quality = max(50, VIDEO_CHAT_IMAGE_QUALITY - 20)
                img_byte_arr = io.BytesIO()
                pil_image.save(img_byte_arr, format=VIDEO_CHAT_IMAGE_FORMAT, 
                              quality=quality, optimize=True)
                img_data = img_byte_arr.getvalue()
                
                if len(img_data) > VIDEO_CHAT_MAX_IMAGE_SIZE:
                    logger.warning(f"[VideoChat] 视频帧大小 {len(img_data)}B 超过限制 {VIDEO_CHAT_MAX_IMAGE_SIZE}B")
                    return None
            
            return img_data
            
        except Exception as e:
            logger.error(f"[VideoChat] 视频帧处理失败: {e}")
            return None
        
    def stop(self):
        """停止会话"""
        self.stop_startup_warmup.set()
        self.initial_response_requested = False
        self.last_user_response_request_at = 0.0
        self.manual_turn_active = False
        self.manual_turn_started_at = 0.0
        self.manual_turn_last_voice_at = 0.0
        self.ai_is_speaking = False
        self.ai_speaking_done_at = 0.0
        self.ai_speaking_started_at = 0.0
        if self.conversation:
            try:
                self.conversation.stop()
            except Exception as e:
                logger.warning(f"[VideoChat] 停止会话时出错: {str(e)}")
            finally:
                self.conversation.close()
                self.is_active = False
                logger.info(f"[VideoChat] 会话已停止: {self.session_id}")
                
        # 停止视频线程
        if self.video_thread and self.video_thread.is_alive():
            self.stop_video.set()
            self.video_thread.join(timeout=2.0)


class VideoChatService:
    """视频聊天服务主类"""
    
    def __init__(self):
        self.active_sessions: Dict[str, VideoInterviewSession] = {}
        
    def create_session(self, session_id: str, interview_id: str, position: str, 
                       job_info: Dict = None, company_info: Dict = None) -> VideoInterviewSession:
        """创建新的视频面试会话"""
        if session_id in self.active_sessions:
            logger.warning(f"[VideoChat] 会话已存在: {session_id}")
            return self.active_sessions[session_id]
            
        session = VideoInterviewSession(session_id, interview_id, position, job_info, company_info)
        self.active_sessions[session_id] = session
        return session
        
    def get_session(self, session_id: str) -> Optional[VideoInterviewSession]:
        """获取会话"""
        return self.active_sessions.get(session_id)
        
    def remove_session(self, session_id: str):
        """移除会话"""
        if session_id in self.active_sessions:
            session = self.active_sessions[session_id]
            session.stop()
            del self.active_sessions[session_id]
            logger.info(f"[VideoChat] 会话已移除: {session_id}")
            
    def cleanup(self):
        """清理所有会话"""
        for session_id in list(self.active_sessions.keys()):
            self.remove_session(session_id)


# 全局服务实例
video_chat_service = VideoChatService()
