import logging
from flask import Blueprint, request, Response
from werkzeug.utils import secure_filename
import os
import tempfile
from ..utils.response import success, error
from ..services.voice_service import VoiceService

logger = logging.getLogger(__name__)

# 创建主蓝图，保持向后兼容性
# 原来的app工厂注册voice.bp，url_prefix='/api/tts'
# 现在改为url_prefix='/api'，以支持ASR和TTS
bp = Blueprint('voice', __name__, url_prefix='/api')

voice_service = VoiceService()

# ASR路由 - 语音识别
@bp.route('/asr', methods=['POST'])
def speech_to_text():
    """
    语音识别API
    参考语音功能测试项目的/api/asr端点
    接收音频文件（WebM格式），返回识别文本
    """
    try:
        # 检查是否有音频文件
        if 'audio' not in request.files:
            return error('音频文件未提供', 400)
        
        audio_file = request.files['audio']
        if audio_file.filename == '':
            return error('音频文件名为空', 400)
        
        # 读取音频数据
        audio_data = audio_file.read()
        if not audio_data:
            return error('音频文件为空', 400)
        
        logger.info(f"接收到ASR请求，音频大小: {len(audio_data)} bytes, 文件名: {audio_file.filename}")
        
        # 语音识别
        # 假设音频是WebM格式，自动检测格式
        recognized_text = voice_service.speech_to_text(audio_data, audio_format='auto')
        
        # 返回识别结果
        return success({
            'text': recognized_text,
            'message': '语音识别成功'
        })
        
    except Exception as e:
        logger.error(f"语音识别API错误: {str(e)}")
        return error(f'语音识别失败: {str(e)}')

@bp.route('/asr', methods=['GET'])
def asr_info():
    """
    ASR API信息
    """
    return success({
        'method': 'POST',
        'endpoint': '/api/asr',
        'contentType': 'multipart/form-data',
        'body': {
            'audio': '音频文件 (WebM格式)'
        }
    })

# TTS路由 - 文本转语音 (POST方法)
@bp.route('/tts', methods=['POST'])
def text_to_speech_post():
    """
    文本转语音API
    参考语音功能测试项目的/api/tts端点
    接收JSON格式文本，返回音频数据
    """
    try:
        # 解析请求体
        data = request.get_json()
        if not data or 'text' not in data:
            return error('文本参数未提供', 400)
        
        text = data['text'].strip()
        if not text:
            return error('文本内容为空', 400)
        
        logger.info(f"接收到POST TTS请求，文本长度: {len(text)} 字符")
        
        # 文本转语音
        audio_data = voice_service.text_to_speech(text)
        
        # 返回音频数据
        response = Response(audio_data, mimetype='audio/mpeg')
        response.headers['Content-Disposition'] = 'inline; filename="speech.mp3"'
        response.headers['Content-Length'] = len(audio_data)
        
        return response
        
    except Exception as e:
        logger.error(f"文本转语音API错误: {str(e)}")
        return error(f'文本转语音失败: {str(e)}')

# TTS路由 - 文本转语音 (GET方法，兼容旧版本)
@bp.route('/tts', methods=['GET'])
def text_to_speech_get():
    """
    TTS API信息 和 兼容旧版本GET请求
    """
    # 检查是否有文本参数（兼容旧版本）
    text = request.args.get('text')
    if text:
        try:
            logger.info(f"接收到GET TTS请求，文本: {text}")
            audio_data = voice_service.text_to_speech(text)
            
            response = Response(audio_data, mimetype='audio/mpeg')
            response.headers['Content-Disposition'] = 'inline; filename="speech.mp3"'
            response.headers['Content-Length'] = len(audio_data)
            
            return response
        except Exception as e:
            logger.error(f"GET TTS API错误: {str(e)}")
            return error(f'文本转语音失败: {str(e)}')
    
    # 返回API信息
    return success({
        'method': 'POST',
        'endpoint': '/api/tts',
        'contentType': 'application/json',
        'body': {
            'text': '要转换为语音的文本'
        }
    })

# 语音功能状态检查
@bp.route('/voice/status', methods=['GET'])
def voice_status():
    """
    语音功能状态检查
    """
    try:
        # 检查语音服务是否可用
        # 简单的测试：尝试创建一个语音服务实例
        test_service = VoiceService()
        
        return success({
            'status': 'healthy',
            'message': '语音服务正常运行',
            'services': {
                'asr': '可用',
                'tts': '可用'
            },
            'config': {
                'app_id': test_service.app_id[:8] + '...' if test_service.app_id else '未配置',
                'asr_url': '已配置' if test_service.asr_url else '未配置',
                'tts_ws_url': '已配置' if test_service.tts_ws_url else '未配置'
            }
        })
    except Exception as e:
        logger.error(f"语音服务状态检查失败: {str(e)}")
        return error(f'语音服务状态异常: {str(e)}')