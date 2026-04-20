import logging
import json
import base64
import asyncio
import threading
from flask import request
from flask_socketio import SocketIO, emit, join_room, leave_room
from ..services.qwen_omni_service import (
    QwenOmniCallback, qwen_omni_service, RagIntegration, QWEN_OMNI_ENABLED
)
from ..services.voice_service import VoiceService

logger = logging.getLogger(__name__)

# RAG集成
rag_integration = RagIntegration()

# 存储活动会话
active_sessions = {}


class QwenOmniInterviewSession:
    """Qwen-Omni面试会话"""
    
    def __init__(self, session_id: str, interview_id: str, position: str, socketio: SocketIO):
        self.session_id = session_id
        self.interview_id = interview_id
        self.position = position
        self.socketio = socketio
        self.omni_session = None
        self.callback = None
        self.is_active = False
        self.interview_started = False
        
    def start(self):
        """启动Qwen-Omni面试会话"""
        try:
            if not QWEN_OMNI_ENABLED:
                raise Exception("Qwen-Omni服务未启用")
            
            # 创建回调处理器
            self.callback = QwenOmniCallback(self)
            
            # 设置回调函数
            self.callback.on_audio_callback = self._handle_audio
            self.callback.on_text_callback = self._handle_text
            self.callback.on_done_callback = self._handle_response_done
            self.callback.on_error_callback = self._handle_error
            
            # 创建面试官会话
            job_info = {"position": self.position, "interview_id": self.interview_id}
            self.omni_session = qwen_omni_service.create_session(
                self.session_id, 
                job_info=job_info
            )
            
            # 创建对话并配置
            conversation = self.omni_session.create_conversation(self.callback)
            self.omni_session.configure_interviewer()
            
            # 启动会话
            self.omni_session.start()
            self.is_active = True
            
            logger.info(f"Qwen-Omni面试会话已启动: {self.session_id}, 岗位: {self.position}")
            
            # 发送会话开始事件
            self._send_started()
            
        except Exception as e:
            logger.error(f"启动Qwen-Omni面试会话失败: {str(e)}")
            self._send_error(str(e))
            raise
    
    def send(self, message: str):
        """发送消息到前端"""
        if hasattr(self, 'socketio') and self.socketio:
            self.socketio.emit('message', message, room=self.session_id)
    
    def send_audio(self, audio_data: bytes):
        """发送音频到Qwen-Omni"""
        if not self.is_active or not self.omni_session:
            raise Exception("会话未激活")
        
        try:
            # 确保音频格式正确（PCM 16kHz 单声道 16-bit）
            logger.info(f"[Qwen-Omni] 发送音频数据到模型: {len(audio_data)}字节")
            
            # 简单检查PCM数据格式（16-bit = 2字节每样本）
            if len(audio_data) % 2 != 0:
                logger.warning(f"[Qwen-Omni] 音频数据大小不是2的倍数: {len(audio_data)}字节")
            
            self.omni_session.send_audio(audio_data)
            
        except Exception as e:
            logger.error(f"发送音频失败: {str(e)}")
            self._send_error(str(e))
    
    def send_image(self, image_base64: str):
        """发送图像到Qwen-Omni"""
        if not self.is_active or not self.omni_session:
            raise Exception("会话未激活")
        
        try:
            self.omni_session.send_image(image_base64)
            
        except Exception as e:
            logger.error(f"发送图像失败: {str(e)}")
            self._send_error(str(e))
    
    def _handle_audio(self, audio_base64: str):
        """处理接收到的音频数据"""
        try:
            self.socketio.emit('audio', {
                'type': 'audio',
                'data': audio_base64,
                'sessionId': self.session_id
            }, room=self.session_id)
            
        except Exception as e:
            logger.error(f"处理音频回调失败: {str(e)}")
    
    def _handle_text(self, text_chunk: str):
        """处理接收到的文本数据"""
        try:
            self.socketio.emit('text', {
                'type': 'text',
                'data': text_chunk,
                'sessionId': self.session_id
            }, room=self.session_id)
            
        except Exception as e:
            logger.error(f"处理文本回调失败: {str(e)}")
    
    def _handle_response_done(self):
        """处理响应完成"""
        logger.info(f"Qwen-Omni响应完成: {self.session_id}")
    
    def _handle_error(self, error_msg: str):
        """处理错误"""
        self._send_error(error_msg)
    
    def _send_started(self):
        """发送会话开始事件"""
        self.socketio.emit('started', {
            'sessionId': self.session_id,
            'message': '面试会话已开始'
        }, room=self.session_id)
    
    def _send_error(self, error_msg: str):
        """发送错误事件"""
        self.socketio.emit('error', {
            'message': error_msg,
            'sessionId': self.session_id
        }, room=self.session_id)
    
    def stop(self):
        """停止会话"""
        if self.omni_session:
            self.omni_session.stop()
            self.is_active = False
        
        # 清理会话
        qwen_omni_service.remove_session(self.session_id)
        if self.session_id in active_sessions:
            del active_sessions[self.session_id]
        
        logger.info(f"Qwen-Omni面试会话已停止: {self.session_id}")


def init_qwen_websocket(socketio: SocketIO):
    """初始化Qwen-Omni WebSocket路由"""
    
    @socketio.on('connect', namespace='/ws/qwen')
    def handle_connect():
        logger.info(f"[Qwen-Omni] 客户端连接: {request.sid}")
    
    @socketio.on('disconnect', namespace='/ws/qwen')
    def handle_disconnect():
        logger.info(f"[Qwen-Omni] 客户端断开: {request.sid}")
        
        # 清理会话
        if request.sid in active_sessions:
            session = active_sessions[request.sid]
            session.stop()
    
    @socketio.on('start_interview', namespace='/ws/qwen')
    def handle_start_interview(data):
        """开始面试会话"""
        try:
            interview_id = data.get('interviewId')
            position = data.get('position')
            
            if not interview_id or not position:
                emit('error', {'message': 'interviewId and position are required'})
                return
            
            session_id = request.sid
            logger.info(f"开始Qwen-Omni面试会话: {session_id}, interviewId: {interview_id}, position: {position}")
            
            # 创建新的面试会话
            session = QwenOmniInterviewSession(session_id, interview_id, position, socketio)
            active_sessions[session_id] = session
            
            # 启动会话
            session.start()
            
        except Exception as e:
            logger.error(f"处理start_interview消息失败: {str(e)}")
            emit('error', {'message': str(e)})
    
    @socketio.on('audio', namespace='/ws/qwen')
    def handle_audio(data):
        """处理音频数据"""
        try:
            session_id = request.sid
            if session_id not in active_sessions:
                emit('error', {'message': 'Session not found'})
                return
            
            session = active_sessions[session_id]
            
            # 解析音频数据
            if isinstance(data, dict):
                audio_base64 = data.get('data', '')
                audio_data = base64.b64decode(audio_base64) if audio_base64 else b''
            elif isinstance(data, str):
                audio_data = base64.b64decode(data)
            else:
                audio_data = data  # 假设是二进制数据
            
            logger.info(f"[Qwen-Omni] 接收到音频数据: {len(audio_data)}字节, 类型: {type(data).__name__}")
            
            if audio_data:
                session.send_audio(audio_data)
            
        except Exception as e:
            logger.error(f"处理音频数据失败: {str(e)}")
            emit('error', {'message': str(e)})
    
    @socketio.on('image', namespace='/ws/qwen')
    def handle_image(data):
        """处理图像数据"""
        try:
            session_id = request.sid
            if session_id not in active_sessions:
                emit('error', {'message': 'Session not found'})
                return
            
            session = active_sessions[session_id]
            
            # 解析图像数据
            if isinstance(data, dict):
                image_base64 = data.get('data', '')
            elif isinstance(data, str):
                image_base64 = data
            else:
                image_base64 = ''
            
            if image_base64:
                # 移除可能的数据URI前缀
                if image_base64.startswith('data:image'):
                    import re
                    image_base64 = re.sub(r'^data:image/\w+;base64,', '', image_base64)
                
                session.send_image(image_base64)
            
        except Exception as e:
            logger.error(f"处理图像数据失败: {str(e)}")
            emit('error', {'message': str(e)})
    
    @socketio.on('stop_interview', namespace='/ws/qwen')
    def handle_stop_interview():
        """停止面试会话"""
        try:
            session_id = request.sid
            if session_id not in active_sessions:
                emit('error', {'message': 'Session not found'})
                return
            
            session = active_sessions[session_id]
            session.stop()
            
            emit('stopped', {
                'sessionId': session_id,
                'message': '面试会话已结束'
            })
            
        except Exception as e:
            logger.error(f"处理stop_interview消息失败: {str(e)}")
            emit('error', {'message': str(e)})
    
    @socketio.on('rag_query', namespace='/ws/qwen')
    async def handle_rag_query(data):
        """处理RAG查询请求"""
        try:
            session_id = request.sid
            query = data.get('query', '')
            position = data.get('position', '')
            
            if not query or not position:
                emit('error', {'message': 'query and position are required'})
                return
            
            # 执行RAG搜索
            results = await rag_integration.search_relevant_content(query, position)
            
            emit('rag_results', {
                'query': query,
                'results': results
            })
            
        except Exception as e:
            logger.error(f"处理RAG查询失败: {str(e)}")
            emit('error', {'message': str(e)})