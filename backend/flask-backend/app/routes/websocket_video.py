import logging
import json
import base64
import threading
import time
from flask import request
from flask_socketio import SocketIO, emit, join_room, leave_room
from ..services.video_chat_service import (
    VideoChatCallback, video_chat_service, VideoInterviewSession, VIDEO_CHAT_ENABLED
)
from ..services.interview_service import InterviewService
from ..services.rag_service import RagService

logger = logging.getLogger(__name__)

# 存储活动会话
active_sessions = {}

# 面试服务
interview_service = InterviewService()

# RAG服务
rag_service = None
try:
    rag_service = RagService()
    logger.info("RAG服务已初始化")
except Exception as e:
    logger.warning(f"初始化RAG服务失败: {e}")


class VideoInterviewWebSocketHandler:
    """视频面试WebSocket处理器"""
    
    def __init__(self, session_id: str, socketio: SocketIO):
        self.session_id = session_id
        self.socketio = socketio
        self.video_session = None
        self.callback = None
        self.interview_id = None
        self.position = None
        self.is_active = False
        self.interview_record = None
        
        # 音频缓冲
        self.audio_buffer = bytearray()
        self.last_audio_time = 0
        
    def start_interview(self, data: dict):
        """开始视频面试"""
        try:
            logger.info(f"🎯🎯🎯 [VideoChat] DEBUG: VideoInterviewWebSocketHandler.start_interview() 被调用!")
            logger.info(f"🎯🎯🎯 [VideoChat] DEBUG: self.session_id={self.session_id}, data={json.dumps(data, ensure_ascii=False, default=str)}")
            logger.info(f"VIDEO_CHAT_ENABLED: {VIDEO_CHAT_ENABLED}")
            if not VIDEO_CHAT_ENABLED:
                raise Exception("视频聊天服务未启用")
            
            self.interview_id = data.get('interviewId')
            self.position = data.get('position', 'java_backend')
            
            if not self.interview_id:
                raise Exception("interviewId is required")
            
            logger.info(f"开始视频面试: session={self.session_id}, interview={self.interview_id}, position={self.position}")
            
            # 创建面试记录（如果不存在）
            self.interview_record = interview_service.get_interview_record(self.interview_id)
            if not self.interview_record:
                # 创建新的面试记录
                self.interview_record = interview_service.create_interview_record(
                    user_id=None,  # 实际应用中应从用户会话获取
                    position=self.position,
                    start_time=None  # 自动设置当前时间
                )
                self.interview_id = str(self.interview_record['id'])
                logger.info(f"创建新的面试记录: {self.interview_id}")
            
            # 创建视频聊天会话
            job_info = {
                "position": self.position,
                "interview_id": self.interview_id,
                "requirements": self._get_position_requirements(self.position)
            }
            
            self.video_session = video_chat_service.create_session(
                self.session_id, 
                self.interview_id,
                self.position,
                job_info=job_info
            )
            
            # 创建回调处理器
            self.callback = VideoChatCallback(self.session_id, self)
            
            # 设置回调函数
            self.callback.on_audio_callback = self._handle_audio
            self.callback.on_text_callback = self._handle_text
            self.callback.on_done_callback = self._handle_response_done
            self.callback.on_error_callback = self._handle_error
            self.callback.on_interview_event_callback = self._handle_interview_event
            
            # 创建对话
            logger.info(f"[VideoChat] 开始创建OmniRealtimeConversation...")
            conversation = self.video_session.create_conversation(self.callback)
            logger.info(f"✅ [VideoChat] 启动视频会话: session={self.video_session}, conversation={conversation}")
            if not conversation:
                logger.error(f"❌ [VideoChat] 会话创建失败，conversation为None")
                raise Exception("会话创建失败，conversation为None")
            
            logger.info(f"✅ [VideoChat] 会话创建成功，开始配置面试官...")
            # 先配置会话参数（update_session可能会建立连接）
            self.video_session.configure_interviewer()
            logger.info(f"✅ [VideoChat] 面试官配置完成")
            
            logger.info(f"[VideoChat] 激活会话...")
            # 然后激活会话
            self.video_session.start()
            
            self.is_active = True
            logger.info(f"✅ [VideoChat] 会话已激活，is_active={self.is_active}")
            
            # 发送会话开始事件
            self._send_started()
            
            logger.info(f"✅ 视频面试会话已启动: {self.session_id}")
            
        except Exception as e:
            logger.error(f"启动视频面试失败: {str(e)}", exc_info=True)  # 添加完整堆栈
            self._send_error(str(e))
            raise
    
    def _get_position_requirements(self, position: str) -> str:
        """根据岗位获取要求描述"""
        position_map = {
            'java_backend': 'Java后端开发工程师，要求掌握Java基础、Spring框架、数据库设计等',
            'web_frontend': 'Web前端开发工程师，要求掌握HTML/CSS/JavaScript、Vue/React框架、前端工程化等',
            'fullstack_engineer': '全栈工程师，要求掌握前后端技术栈、系统设计、DevOps等',
            'bigdata_engineer': '大数据工程师，要求掌握Hadoop/Spark、数据仓库、数据挖掘等'
        }
        return position_map.get(position, '技术开发岗位')
    
    def handle_audio(self, audio_data: bytes):
        """处理音频数据"""
        if not self.is_active or not self.video_session:
            raise Exception("会话未激活")
        
        try:
            # 检查音频数据格式
            if len(audio_data) == 0:
                return
            
            # 发送音频到视频会话
            self.video_session.send_audio(audio_data)
            self.last_audio_time = time.time()
            
            # 记录到音频缓冲区（用于可能的后续处理）
            self.audio_buffer.extend(audio_data)
            
        except Exception as e:
            logger.error(f"处理音频数据失败: {str(e)}")
            self._send_error(str(e))
    
    def handle_video_frame(self, frame_data: bytes):
        """处理视频帧数据"""
        if not self.is_active or not self.video_session:
            raise Exception("会话未激活")
        
        try:
            # 发送视频帧到视频会话
            self.video_session.send_video_frame(frame_data)
            
        except Exception as e:
            logger.error(f"处理视频帧数据失败: {str(e)}")
            self._send_error(str(e))
    
    def handle_image(self, image_base64: str):
        """处理图像数据（base64编码）"""
        if not self.is_active or not self.video_session:
            raise Exception("会话未激活")
        
        try:
            logger.info(f"[WebSocket] 发送图像到视频会话: session={self.session_id}, data_size={len(image_base64)} chars")
            # 发送图像到视频会话
            self.video_session.send_image(image_base64)
            
        except Exception as e:
            logger.error(f"处理图像数据失败: {str(e)}")
            self._send_error(str(e))
    
    def stop_interview(self):
        """停止视频面试"""
        try:
            if self.video_session:
                self.video_session.stop()
                self.is_active = False
            
            # 更新面试记录结束时间
            if self.interview_record and self.interview_id:
                interview_service.update_interview_end_time(self.interview_id)
                logger.info(f"面试记录已更新: {self.interview_id}")
            
            # 清理会话
            if self.session_id in active_sessions:
                del active_sessions[self.session_id]
            
            # 发送停止事件
            self._send_stopped()
            
            logger.info(f"视频面试已停止: {self.session_id}")
            
        except Exception as e:
            logger.error(f"停止视频面试失败: {str(e)}")
    
    # 回调处理函数
    def _handle_audio(self, audio_base64: str):
        """处理AI音频回复"""
        try:
            # 发送音频数据到前端
            self.socketio.emit('audio', {
                'type': 'ai_audio',
                'data': audio_base64,
                'sessionId': self.session_id
            }, room=self.session_id)
            
        except Exception as e:
            logger.error(f"发送音频数据失败: {str(e)}")
    
    def _handle_text(self, text_chunk: str):
        """处理AI文本回复（字幕）"""
        try:
            # 发送文本数据到前端
            self.socketio.emit('text', {
                'type': 'ai_text',
                'data': text_chunk,
                'sessionId': self.session_id
            }, room=self.session_id)
            
        except Exception as e:
            logger.error(f"发送文本数据失败: {str(e)}")
    
    def _handle_response_done(self):
        """处理AI响应完成"""
        try:
            self.socketio.emit('response_done', {
                'sessionId': self.session_id
            }, room=self.session_id)
            
        except Exception as e:
            logger.error(f"发送响应完成事件失败: {str(e)}")
    
    def _handle_error(self, error_msg: str):
        """处理错误"""
        self._send_error(error_msg)
    
    def _handle_interview_event(self, event_type: str, data: dict):
        """处理面试事件（用户语音、AI回复等）"""
        try:
            # 记录面试对话到数据库
            if event_type == 'user_speech' and self.interview_id:
                user_text = data.get('text', '')
                if user_text:
                    # 保存用户回答
                    interview_service.save_answer(
                        interview_id=self.interview_id,
                        question_text="",  # 这里需要获取当前问题
                        answer_text=user_text,
                        audio_url=None
                    )
            
            elif event_type == 'ai_response' and self.interview_id:
                ai_text = data.get('text', '')
                if ai_text:
                    # 保存AI问题
                    interview_service.save_question(
                        interview_id=self.interview_id,
                        question_text=ai_text
                    )
            
        except Exception as e:
            logger.error(f"处理面试事件失败: {str(e)}")
    
    # WebSocket消息发送函数
    def send(self, message: str):
        """发送消息到前端"""
        if hasattr(self, 'socketio') and self.socketio:
            self.socketio.emit('message', message, room=self.session_id)
    
    def _send_started(self):
        """发送会话开始事件"""
        self.socketio.emit('started', {
            'sessionId': self.session_id,
            'interviewId': self.interview_id,
            'message': '视频面试已开始'
        }, room=self.session_id)
    
    def _send_stopped(self):
        """发送会话停止事件"""
        self.socketio.emit('stopped', {
            'sessionId': self.session_id,
            'interviewId': self.interview_id,
            'message': '视频面试已结束'
        }, room=self.session_id)
    
    def _send_error(self, error_msg: str):
        """发送错误事件"""
        self.socketio.emit('error', {
            'sessionId': self.session_id,
            'message': error_msg
        }, room=self.session_id)


def init_video_websocket(socketio: SocketIO):
    """初始化视频WebSocket路由"""
    
    @socketio.on('connect', namespace='/ws/video')
    def handle_connect():
        try:
            session_id = request.sid
            logger.info(f"🎯 [WebSocket] 视频客户端连接请求到达: {session_id}")
            logger.info(f"📋 [WebSocket] 连接详细信息: headers={dict(request.headers)}, args={request.args}, environ={request.environ.get('REMOTE_ADDR')}")
            logger.info(f"🔗 [WebSocket] WebSocket环境: {request.environ.get('wsgi.websocket')}")
            logger.info(f"🌐 [WebSocket] 请求方法: {request.method}, 路径: {request.path}")
            
            # 创建处理器
            handler = VideoInterviewWebSocketHandler(session_id, socketio)
            active_sessions[session_id] = handler
            
            logger.info(f"✅ [WebSocket] 会话处理器已创建: {session_id}")
            
            emit('connected', {'sessionId': session_id})
            logger.info(f"✅ [WebSocket] 已发送connected事件给客户端: {session_id}")
            logger.info(f"✅ [WebSocket] 连接处理完成: {session_id}")
            
        except Exception as e:
            logger.error(f"❌ [WebSocket] 连接处理失败: {str(e)}", exc_info=True)
            # 重新抛出异常，让Socket.IO处理
            raise
    
    @socketio.on('disconnect', namespace='/ws/video')
    def handle_disconnect():
        session_id = request.sid
        logger.info(f"视频客户端断开: {session_id}")
        
        # 清理会话
        if session_id in active_sessions:
            handler = active_sessions[session_id]
            handler.stop_interview()
    
    @socketio.on('start_interview', namespace='/ws/video')
    def handle_start_interview(data):
        try:
            session_id = request.sid
            logger.info(f"🎯🎯🎯 [WebSocket] DEBUG: start_interview事件被触发! session={session_id}")
            logger.info(f"🎯🎯🎯 [WebSocket] DEBUG: 事件数据: {json.dumps(data, ensure_ascii=False, default=str)}")
            logger.info(f"[WebSocket] 收到start_interview请求: session={session_id}, data={data}")
            
            if session_id not in active_sessions:
                logger.error(f"[WebSocket] 会话未找到: {session_id}")
                emit('error', {'message': 'Session not found'})
                return
            
            handler = active_sessions[session_id]
            logger.info(f"[WebSocket] 找到会话处理器: {session_id}, 开始启动视频面试...")
            handler.start_interview(data)
            logger.info(f"[WebSocket] start_interview处理完成: {session_id}")
            
        except Exception as e:
            logger.error(f"[WebSocket] 处理start_interview失败: {str(e)}", exc_info=True)
            emit('error', {'message': str(e)})
    
    @socketio.on('audio', namespace='/ws/video')
    def handle_audio(data):
        try:
            session_id = request.sid
            if session_id not in active_sessions:
                emit('error', {'message': 'Session not found'})
                return
            
            handler = active_sessions[session_id]
            
            # data应该是二进制音频数据或base64字符串
            if isinstance(data, str):
                # base64解码
                audio_data = base64.b64decode(data)
            else:
                # 二进制数据
                audio_data = data
            
            handler.handle_audio(audio_data)
            
        except Exception as e:
            logger.error(f"处理音频数据失败: {str(e)}")
    
    @socketio.on('video_frame', namespace='/ws/video')
    def handle_video_frame(data):
        try:
            session_id = request.sid
            if session_id not in active_sessions:
                emit('error', {'message': 'Session not found'})
                return
            
            handler = active_sessions[session_id]
            
            # data应该是二进制图像数据或base64字符串
            if isinstance(data, str):
                # base64解码
                frame_data = base64.b64decode(data)
            else:
                # 二进制数据
                frame_data = data
            
            handler.handle_video_frame(frame_data)
            
        except Exception as e:
            logger.error(f"处理视频帧数据失败: {str(e)}")
    
    @socketio.on('image', namespace='/ws/video')
    def handle_image(data):
        try:
            session_id = request.sid
            logger.info(f"[WebSocket] 收到图像数据: session={session_id}, data_type={type(data).__name__}")
            
            if session_id not in active_sessions:
                emit('error', {'message': 'Session not found'})
                return
            
            handler = active_sessions[session_id]
            
            # data应该是base64编码的图像字符串
            if isinstance(data, str):
                logger.info(f"[WebSocket] 图像数据大小: {len(data)} chars")
                handler.handle_image(data)
            else:
                # 如果是二进制数据，转换为base64
                logger.info(f"[WebSocket] 图像二进制数据大小: {len(data)} bytes")
                image_base64 = base64.b64encode(data).decode('utf-8')
                handler.handle_image(image_base64)
            
        except Exception as e:
            logger.error(f"处理图像数据失败: {str(e)}")
    
    @socketio.on('stop_interview', namespace='/ws/video')
    def handle_stop_interview(data):
        try:
            session_id = request.sid
            if session_id not in active_sessions:
                emit('error', {'message': 'Session not found'})
                return
            
            handler = active_sessions[session_id]
            handler.stop_interview()
            
        except Exception as e:
            logger.error(f"处理stop_interview失败: {str(e)}")
    
    logger.info("视频WebSocket路由已注册: /ws/video")