import os
import json
import base64
import logging
import asyncio
import threading
import time
from typing import Dict, List, Optional, Callable
from dashscope.audio.qwen_omni import OmniRealtimeConversation, OmniRealtimeCallback
from dashscope.audio.qwen_omni import MultiModality, AudioFormat
import dashscope

from ..config.default import (
    QWEN_OMNI_API_KEY, QWEN_OMNI_MODEL, QWEN_OMNI_WS_URL,
    QWEN_OMNI_VOICE, QWEN_OMNI_ENABLED, RAG_SERVICE_URL,
    RAG_ENABLED, RAG_TOP_K, RAG_MODE
)

logger = logging.getLogger(__name__)

# 设置DashScope API密钥
dashscope.api_key = QWEN_OMNI_API_KEY


class QwenOmniCallback(OmniRealtimeCallback):
    """处理Qwen-Omni服务端返回事件的回调类"""
    
    def __init__(self, websocket_handler=None):
        self.websocket_handler = websocket_handler
        self.on_audio_callback = None
        self.on_text_callback = None
        self.on_done_callback = None
        self.on_error_callback = None
        
    def on_open(self):
        logger.info("[Qwen-Omni] 连接已建立")
        
    def on_event(self, event):
        """处理模型返回的各类事件"""
        try:
            event_type = event.get("type")
            
            if event_type == "response.audio.delta":
                # 音频增量数据（Base64 编码的 PCM）
                audio_base64 = event.get("delta", "")
                if self.on_audio_callback:
                    self.on_audio_callback(audio_base64)
                if self.websocket_handler:
                    self.websocket_handler.send(json.dumps({
                        "type": "audio",
                        "data": audio_base64
                    }))
                    
            elif event_type == "response.text.delta":
                # 文本增量数据（用于字幕显示）
                text_chunk = event.get("delta", "")
                if self.on_text_callback:
                    self.on_text_callback(text_chunk)
                if self.websocket_handler:
                    self.websocket_handler.send(json.dumps({
                        "type": "text",
                        "data": text_chunk
                    }))
                    
            elif event_type == "response.done":
                # 一次响应完成
                logger.info("[Qwen-Omni] 响应完成")
                if self.on_done_callback:
                    self.on_done_callback()
                    
        except Exception as e:
            logger.error(f"[Qwen-Omni] 处理事件失败: {str(e)}")
            if self.on_error_callback:
                self.on_error_callback(str(e))
        
    def on_close(self, close_status_code, close_msg):
        logger.info(f"[Qwen-Omni] 连接关闭 (code={close_status_code}, msg={close_msg})")
        
    def on_error(self, error):
        logger.error(f"[Qwen-Omni] 错误: {error}")
        if self.on_error_callback:
            self.on_error_callback(str(error))


class InterviewerSession:
    """面试官会话管理类"""
    
    def __init__(self, session_id: str, job_info: Optional[Dict] = None, company_info: Optional[Dict] = None):
        self.session_id = session_id
        self.job_info = job_info or {}
        self.company_info = company_info or {}
        self.conversation = None
        self.callback = None
        self.is_active = False
        self.audio_buffer = bytearray()
        
    def create_conversation(self, callback: QwenOmniCallback):
        """创建Omni-Realtime会话"""
        if not QWEN_OMNI_ENABLED:
            raise Exception("Qwen-Omni服务未启用")
            
        self.callback = callback
        self.conversation = OmniRealtimeConversation(
            model=QWEN_OMNI_MODEL,
            callback=callback,
            url=QWEN_OMNI_WS_URL
        )
        return self.conversation
        
    def configure_interviewer(self):
        """配置面试官的会话参数"""
        if not self.conversation:
            raise Exception("会话未创建")
            
        # 构建系统提示词
        instructions = self._build_instructions()
        
        # 更新会话配置
        self.conversation.update_session({
            "output_modalities": [MultiModality.TEXT, MultiModality.AUDIO],  # 同时输出文本和音频
            "voice": QWEN_OMNI_VOICE,
            "instructions": instructions,
            "enable_turn_detection": True,  # 开启VAD模式，自动检测语音起止
            "input_audio_format": AudioFormat.PCM_16000HZ_MONO_16BIT,  # 输入音频格式
            "output_audio_format": AudioFormat.PCM,  # 输出音频格式
            "smooth_output": True,  # 获得更口语化的回复
            "enable_input_audio_transcription": True  # 开启语音转文本，便于后端记录
        })
        
        logger.info(f"[Qwen-Omni] 面试官会话已配置: {self.session_id}")
        
    def _build_instructions(self) -> str:
        """构建面试官系统提示词"""
        base_instructions = """你是一位专业、友好、循循善诱的技术面试官，名字是"千小问"。
你需要通过提问来评估候选人的技术能力和综合素质。

面试原则：
1. 开场先进行简短的自我介绍（不超过30秒），然后询问候选人准备好了没有。
2. 根据候选人的简历和岗位要求，提出有针对性的技术问题。
3. 问题应由浅入深，根据候选人的回答质量决定是否追问或转换话题。
4. 控制每轮提问的长度，避免长篇大论，保持对话的自然节奏。
5. 面试结束时，对候选人的表现给予简短鼓励，并告知后续流程。

请始终使用口语化的中文进行提问和回应，保持专业且亲切的语气。"""
        
        # 添加岗位信息
        if self.job_info:
            job_desc = json.dumps(self.job_info, ensure_ascii=False)
            base_instructions += f"\n\n当前招聘岗位信息：{job_desc}"
            
        # 添加公司信息
        if self.company_info:
            company_desc = json.dumps(self.company_info, ensure_ascii=False)
            base_instructions += f"\n公司背景信息：{company_desc}"
            
        return base_instructions
        
    def start(self):
        """启动会话"""
        if not self.conversation:
            raise Exception("会话未创建")
            
        self.conversation.start()
        self.is_active = True
        logger.info(f"[Qwen-Omni] 会话已启动: {self.session_id}")
        
    def send_audio(self, audio_data: bytes):
        """发送音频数据"""
        if not self.is_active or not self.conversation:
            raise Exception("会话未激活")
            
        self.conversation.send_audio(audio_data)
        
    def send_image(self, image_base64: str):
        """发送图像数据"""
        if not self.is_active or not self.conversation:
            raise Exception("会话未激活")
            
        self.conversation.send_image(image_base64)
        
    def stop(self):
        """停止会话"""
        if self.conversation:
            try:
                self.conversation.stop()
            except Exception as e:
                logger.warning(f"停止会话时出错: {str(e)}")
            finally:
                self.conversation.close()
                self.is_active = False
                logger.info(f"[Qwen-Omni] 会话已停止: {self.session_id}")


class QwenOmniService:
    """Qwen-Omni服务主类"""
    
    def __init__(self):
        self.active_sessions: Dict[str, InterviewerSession] = {}
        
    def create_session(self, session_id: str, job_info: Dict = None, company_info: Dict = None) -> InterviewerSession:
        """创建新的面试官会话"""
        if session_id in self.active_sessions:
            logger.warning(f"会话已存在: {session_id}")
            return self.active_sessions[session_id]
            
        session = InterviewerSession(session_id, job_info, company_info)
        self.active_sessions[session_id] = session
        return session
        
    def get_session(self, session_id: str) -> Optional[InterviewerSession]:
        """获取会话"""
        return self.active_sessions.get(session_id)
        
    def remove_session(self, session_id: str):
        """移除会话"""
        if session_id in self.active_sessions:
            session = self.active_sessions[session_id]
            session.stop()
            del self.active_sessions[session_id]
            logger.info(f"会话已移除: {session_id}")
            
    def cleanup(self):
        """清理所有会话"""
        for session_id in list(self.active_sessions.keys()):
            self.remove_session(session_id)


# 全局服务实例
qwen_omni_service = QwenOmniService()


class RagIntegration:
    """RAG集成类，用于将RAG结果注入对话"""
    
    def __init__(self, rag_service_url: str = None):
        self.rag_service_url = rag_service_url or RAG_SERVICE_URL
        self.enabled = RAG_ENABLED
        self.mode = RAG_MODE
        self.rag_service = None
        
        # 如果RAG启用，初始化RAG服务
        if self.enabled:
            try:
                from .rag_service import RagService
                self.rag_service = RagService()
                logger.info(f"RagIntegration已初始化RAG服务，模式: {self.rag_service.mode}")
            except Exception as e:
                logger.error(f"RagIntegration初始化RAG服务失败: {e}")
                self.rag_service = None
        
    async def search_relevant_content(self, query: str, position: str, top_k: int = None) -> List[Dict]:
        """搜索相关RAG内容"""
        if not self.enabled or not self.rag_service or not self.rag_service.enabled:
            return []
            
        try:
            top_k = top_k or RAG_TOP_K
            collection = self._get_collection_by_position(position)
            
            logger.info(f"RagIntegration搜索: collection={collection}, query长度={len(query)}, top_k={top_k}")
            
            # 使用RagService搜索
            results = self.rag_service.search_questions(query, collection, top_k)
            
            # 转换结果格式
            formatted_results = []
            for result in results:
                formatted_results.append({
                    "document": result.get("content", ""),
                    "id": result.get("id", ""),
                    "metadata": result.get("metadata", {}),
                    "score": result.get("score", 0.0),
                    "distance": result.get("distance", 0.0)
                })
            
            logger.info(f"RagIntegration返回 {len(formatted_results)} 条结果")
            return formatted_results
            
        except Exception as e:
            logger.error(f"RAG搜索失败: {str(e)}")
            return []
            
    def _get_collection_by_position(self, position: str) -> str:
        """根据岗位类型获取对应的RAG集合"""
        position = position.lower()
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