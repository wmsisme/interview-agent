import logging
import json
import base64
import threading
import time
from flask import request
from flask_socketio import SocketIO, emit, join_room, leave_room, close_room
from ..services.voice_service import VoiceService

logger = logging.getLogger(__name__)

# 存储活动会话
active_sessions = {}

class StreamRecognitionSession:
    def __init__(self, session_id, interview_id, question_id, socketio):
        self.session_id = session_id
        self.interview_id = interview_id
        self.question_id = question_id
        self.socketio = socketio
        self.voice_service = VoiceService()
        self.recognizer = None
        self.recognized_text = ""
        self.is_active = True
        self.audio_buffer = bytearray()
        
    def start(self):
        try:
            # 创建流式识别器
            self.recognizer = self.voice_service.create_streaming_recognizer()
            
            # 定义回调函数
            def on_partial_text(text):
                if not self.is_active:
                    return
                
                self.recognized_text += text
                self._send_partial_result(text)
                
            def on_final_text(text):
                if not self.is_active:
                    return
                
                self.recognized_text = text
                self._send_final_result(text)
                
            def on_error(error_msg):
                logger.error(f"流式识别错误: {error_msg}")
                self._send_error(error_msg)
            
            # 启动识别器
            self.recognizer.start(
                partial_callback=on_partial_text,
                final_callback=on_final_text,
                error_callback=on_error
            )
            
            logger.info(f"流式识别会话已启动: {self.session_id}")
            
        except Exception as e:
            logger.error(f"启动流式识别会话失败: {str(e)}")
            self._send_error(str(e))
            raise
    
    def add_audio_data(self, audio_data):
        if not self.is_active or not self.recognizer:
            return
        
        try:
            # 将WebM音频数据转换为PCM 16kHz单声道格式
            # 假设前端发送的是WebM格式（audio/webm;codecs=opus）
            try:
                pcm_data = self.voice_service._convert_audio_to_pcm(audio_data, 'webm')
                logger.debug(f"音频转换成功: {len(audio_data)} bytes -> {len(pcm_data)} bytes")
            except Exception as conv_error:
                logger.warning(f"音频转换失败，尝试直接发送原始数据: {str(conv_error)}")
                # 如果转换失败，尝试直接发送原始数据
                pcm_data = audio_data
            
            # 发送音频数据到识别器
            self.recognizer.send_audio(pcm_data)
        except Exception as e:
            logger.error(f"发送音频数据失败: {str(e)}")
            self._send_error(str(e))
    
    def _send_partial_result(self, text):
        if not self.is_active:
            return
        
        # 发送部分识别结果
        self.socketio.emit('partial', {
            'text': text,
            'sessionId': self.session_id
        }, room=self.session_id)
    
    def _send_final_result(self, text):
        if not self.is_active:
            return
        
        # 发送最终识别结果
        self.socketio.emit('stopped', {
            'text': text,
            'sessionId': self.session_id
        }, room=self.session_id)
    
    def _send_error(self, error_msg):
        self.socketio.emit('error', {
            'message': error_msg,
            'sessionId': self.session_id
        }, room=self.session_id)
    
    def finalize(self):
        self.is_active = False
        if self.recognizer:
            self.recognizer.stop()
            self.recognizer = None
        
        # 清理会话
        if self.session_id in active_sessions:
            del active_sessions[self.session_id]
    
    def stop(self):
        self.finalize()

def init_websocket(socketio: SocketIO):
    @socketio.on('connect', namespace='/ws/stt')
    def handle_connect():
        logger.info(f"客户端连接: {request.sid}")
    
    @socketio.on('disconnect', namespace='/ws/stt')
    def handle_disconnect():
        logger.info(f"客户端断开: {request.sid}")
        # 清理该客户端的会话
        if request.sid in active_sessions:
            session = active_sessions[request.sid]
            session.finalize()
    
    @socketio.on('start', namespace='/ws/stt')
    def handle_start(data):
        try:
            interview_id = data.get('interviewId')
            question_id = data.get('questionId')
            
            if not interview_id or not question_id:
                emit('error', {'message': 'interviewId and questionId are required'})
                return
            
            session_id = request.sid
            logger.info(f"开始流式识别会话: {session_id}, interviewId: {interview_id}, questionId: {question_id}")
            
            # 创建新的会话
            session = StreamRecognitionSession(session_id, interview_id, question_id, socketio)
            active_sessions[session_id] = session
            
            # 启动识别会话
            session.start()
            
            emit('started', {'sessionId': session_id})
            
        except Exception as e:
            logger.error(f"处理start消息失败: {str(e)}")
            emit('error', {'message': str(e)})
    
    @socketio.on('audio', namespace='/ws/stt')
    def handle_audio(data):
        try:
            session_id = request.sid
            if session_id not in active_sessions:
                emit('error', {'message': 'Session not found'})
                return
            
            session = active_sessions[session_id]
            
            # data应该是二进制音频数据
            if isinstance(data, str):
                # 可能是base64编码
                audio_data = base64.b64decode(data)
            else:
                # 假设是二进制数据
                audio_data = data
            
            session.add_audio_data(audio_data)
            
        except Exception as e:
            logger.error(f"处理音频数据失败: {str(e)}")
    
    @socketio.on('stop', namespace='/ws/stt')
    def handle_stop():
        try:
            session_id = request.sid
            if session_id not in active_sessions:
                emit('error', {'message': 'Session not found'})
                return
            
            session = active_sessions[session_id]
            session.finalize()
            
        except Exception as e:
            logger.error(f"处理stop消息失败: {str(e)}")
            emit('error', {'message': str(e)})