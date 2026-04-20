import logging
import base64
import hashlib
import hmac
import json
import time
import requests
import websocket
import threading
from datetime import datetime
from urllib.parse import urlencode
from ..config.default import (
    IFLYTEK_APP_ID, IFLYTEK_API_KEY, IFLYTEK_API_SECRET,
    IFLYTEK_RES_ID, IFLYTEK_ASR_URL, IFLYTEK_TTS_URL, IFLYTEK_TTS_WS_URL
)
from ..utils.audio_utils import AudioConverter

logger = logging.getLogger(__name__)

class VoiceService:
    def __init__(self):
        self.app_id = IFLYTEK_APP_ID
        self.api_key = IFLYTEK_API_KEY
        self.api_secret = IFLYTEK_API_SECRET
        self.res_id = IFLYTEK_RES_ID
        self.asr_url = IFLYTEK_ASR_URL
        self.tts_url = IFLYTEK_TTS_URL
        self.tts_ws_url = IFLYTEK_TTS_WS_URL
    
    def speech_to_text(self, audio_data: bytes, audio_format: str = 'auto') -> str:
        """
        语音识别，将音频数据转换为文本
        
        Args:
            audio_data: 音频数据，可以是WebM格式或PCM格式
            audio_format: 音频格式，'webm'、'pcm'或'auto'（自动检测）
            
        Returns:
            识别出的文本
        """
        try:
            logger.info(f"开始语音识别，音频大小: {len(audio_data)} bytes, 格式: {audio_format}")
            
            # 音频格式转换（如果需要）
            pcm_data = self._convert_audio_to_pcm(audio_data, audio_format)
            if pcm_data is None:
                raise Exception("音频格式转换失败")
            
            # 构建WebSocket URL
            url = self._build_asr_url()
            
            # 建立WebSocket连接
            ws = websocket.WebSocket()
            ws.connect(url)
            
            # 发送音频数据
            self._send_audio_data(ws, pcm_data)
            
            # 接收识别结果
            recognized_text = self._receive_recognition_result(ws)
            
            ws.close()
            
            logger.info(f"语音识别完成，结果: {recognized_text}")
            return recognized_text
            
        except Exception as e:
            logger.error(f"语音识别失败: {str(e)}")
            raise

    def _convert_audio_to_pcm(self, audio_data: bytes, audio_format: str = 'auto') -> bytes:
        """
        将音频数据转换为PCM 16kHz单声道格式
        
        Args:
            audio_data: 原始音频数据
            audio_format: 音频格式 ('webm', 'pcm', 'auto')
            
        Returns:
            PCM格式的音频数据
        """
        try:
            # 如果是PCM格式，直接返回
            if audio_format == 'pcm':
                logger.info(f"音频已经是PCM格式，大小: {len(audio_data)} bytes")
                return audio_data
            
            # 自动检测格式
            if audio_format == 'auto':
                # 简单检测：检查是否是WebM格式（前4个字节为EBML头）
                if len(audio_data) >= 4 and audio_data[:4] == b'\x1a\x45\xdf\xa3':
                    logger.info("检测到WebM格式音频，自动转换为PCM")
                    audio_format = 'webm'
                else:
                    # 假设已经是PCM格式
                    logger.info("未检测到WebM格式，假设为PCM格式")
                    audio_format = 'pcm'
            
            # 格式转换
            if audio_format == 'webm':
                logger.info(f"转换WebM音频到PCM，原始大小: {len(audio_data)} bytes")
                pcm_data = AudioConverter.webm_to_pcm(audio_data)
                if pcm_data is None:
                    raise Exception("WebM到PCM转换失败")
                
                # 验证PCM数据
                if not AudioConverter.is_valid_pcm(pcm_data):
                    logger.warning("转换后的PCM数据可能无效")
                
                logger.info(f"音频转换成功，PCM大小: {len(pcm_data)} bytes")
                return pcm_data
            else:
                # 其他格式暂不支持
                raise ValueError(f"不支持的音频格式: {audio_format}")
                
        except Exception as e:
            logger.error(f"音频格式转换失败: {str(e)}")
            raise

    def create_streaming_recognizer(self):
        """
        创建流式语音识别器
        返回一个对象，包含以下方法：
        - start(): 开始识别
        - send_audio(audio_data): 发送音频数据
        - stop(): 结束识别
        """
        return self.StreamingRecognizer(self)

    class StreamingRecognizer:
        def __init__(self, voice_service):
            self.voice_service = voice_service
            self.ws = None
            self.is_active = False
            self.callbacks = {
                'partial': None,
                'final': None,
                'error': None
            }
        
        def start(self, partial_callback=None, final_callback=None, error_callback=None):
            try:
                self.callbacks['partial'] = partial_callback
                self.callbacks['final'] = final_callback
                self.callbacks['error'] = error_callback
                
                # 构建WebSocket URL
                url = self.voice_service._build_asr_url()
                
                # 建立WebSocket连接
                self.ws = websocket.WebSocket()
                self.ws.connect(url)
                self.is_active = True
                
                # 发送开始帧
                self._send_first_frame()
                
                logger.info("流式语音识别已启动")
                
            except Exception as e:
                logger.error(f"启动流式识别失败: {str(e)}")
                if error_callback:
                    error_callback(str(e))
                raise
        
        def _send_first_frame(self):
            # 发送空的第一帧 - 参考语音功能测试项目的参数
            request_data = {
                "common": {
                    "app_id": self.voice_service.app_id
                },
                "business": {
                    "language": "zh_cn",
                    "domain": "iat",          # 语音听写领域
                    "accent": "mandarin",
                    "sample_rate": "16000",   # 字符串类型，API要求
                    "vad_eos": 5000,          # 静音检测断点参数（毫秒）- 调整为5000
                    "dwa": "wpgs",            # 动态修正
                    "ptt": 1                  # 添加标点符号，默认开启
                },
                "data": {
                    "status": 0,
                    "format": "audio/L16;rate=16000",
                    "encoding": "raw",
                    "audio": ""
                }
            }
            self.ws.send(json.dumps(request_data))
        
        def send_audio(self, audio_data):
            if not self.is_active or not self.ws:
                raise Exception("流式识别未启动")
            
            try:
                # 发送音频数据帧 - 参考语音功能测试项目的参数
                request_data = {
                    "common": {
                        "app_id": self.voice_service.app_id
                    },
                    "business": {
                        "language": "zh_cn",
                        "domain": "iat",          # 语音听写领域
                        "accent": "mandarin",
                        "sample_rate": "16000",   # 字符串类型，API要求
                        "vad_eos": 5000,          # 静音检测断点参数（毫秒）- 调整为5000
                        "dwa": "wpgs",            # 动态修正
                        "ptt": 1                  # 添加标点符号，默认开启
                    },
                    "data": {
                        "status": 1,
                        "format": "audio/L16;rate=16000",
                        "encoding": "raw",
                        "audio": base64.b64encode(audio_data).decode('utf-8')
                    }
                }
                self.ws.send(json.dumps(request_data))
                
                # 尝试接收部分结果
                self._receive_partial_results()
                
            except Exception as e:
                logger.error(f"发送音频数据失败: {str(e)}")
                if self.callbacks['error']:
                    self.callbacks['error'](str(e))
                raise
        
        def _receive_partial_results(self):
            if not self.is_active or not self.ws:
                return
            
            try:
                # 非阻塞接收
                self.ws.settimeout(0.1)
                while True:
                    try:
                        result = self.ws.recv()
                        if not result:
                            break
                        
                        data = json.loads(result)
                        code = data.get("code")
                        if code != 0:
                            error_msg = data.get("message", "Unknown error")
                            logger.error(f"语音识别错误: {error_msg}")
                            if self.callbacks['error']:
                                self.callbacks['error'](error_msg)
                            break
                        
                        # 解析结果
                        if "data" in data:
                            result_data = data["data"]["result"]
                            if result_data:
                                text = ""
                                for word in result_data.get("ws", []):
                                    for cw in word.get("cw", []):
                                        text += cw.get("w", "")
                                
                                if text and self.callbacks['partial']:
                                    self.callbacks['partial'](text)
                        
                        # 检查是否结束
                        if data.get("data", {}).get("status") == 2:
                            if self.callbacks['final']:
                                self.callbacks['final'](text)
                            break
                            
                    except websocket.WebSocketTimeoutException:
                        break
                    except Exception as e:
                        logger.error(f"接收结果失败: {str(e)}")
                        break
                        
            except Exception as e:
                logger.error(f"接收部分结果失败: {str(e)}")
        
        def stop(self):
            if not self.is_active or not self.ws:
                return
            
            try:
                # 发送结束帧 - 参考语音功能测试项目的参数
                request_data = {
                    "common": {
                        "app_id": self.voice_service.app_id
                    },
                    "business": {
                        "language": "zh_cn",
                        "domain": "iat",          # 语音听写领域
                        "accent": "mandarin",
                        "sample_rate": "16000",   # 字符串类型，API要求
                        "vad_eos": 5000,          # 静音检测断点参数（毫秒）- 调整为5000
                        "dwa": "wpgs",            # 动态修正
                        "ptt": 1                  # 添加标点符号，默认开启
                    },
                    "data": {
                        "status": 2,
                        "format": "audio/L16;rate=16000",
                        "encoding": "raw",
                        "audio": ""
                    }
                }
                self.ws.send(json.dumps(request_data))
                
                # 接收最终结果
                self._receive_final_results()
                
            except Exception as e:
                logger.error(f"停止流式识别失败: {str(e)}")
            finally:
                self.is_active = False
                if self.ws:
                    self.ws.close()
                    self.ws = None
        
        def _receive_final_results(self):
            if not self.ws:
                return
            
            try:
                self.ws.settimeout(2.0)
                full_text = ""
                
                while True:
                    try:
                        result = self.ws.recv()
                        if not result:
                            break
                        
                        data = json.loads(result)
                        code = data.get("code")
                        if code != 0:
                            break
                        
                        if "data" in data:
                            result_data = data["data"]["result"]
                            if result_data:
                                for word in result_data.get("ws", []):
                                    for cw in word.get("cw", []):
                                        full_text += cw.get("w", "")
                        
                        if data.get("data", {}).get("status") == 2:
                            break
                            
                    except websocket.WebSocketTimeoutException:
                        break
                    except Exception as e:
                        logger.error(f"接收最终结果失败: {str(e)}")
                        break
                
                if full_text and self.callbacks['final']:
                    self.callbacks['final'](full_text)
                    
            except Exception as e:
                logger.error(f"接收最终结果失败: {str(e)}")

    def text_to_speech(self, text: str) -> bytes:
        """
        文本转语音，使用WebSocket接口
        参考语音功能测试项目的TTS实现
        """
        try:
            logger.info(f"开始文本转语音，文本: {text}")
            
            # 构建WebSocket URL
            url = self._build_tts_websocket_url()
            
            # 建立WebSocket连接
            ws = websocket.WebSocket()
            ws.connect(url)
            
            # 生成TTS请求帧
            request_data = self._generate_tts_request(text)
            
            # 发送请求
            ws.send(json.dumps(request_data))
            
            # 接收音频数据
            audio_data = bytearray()
            is_final = False
            error = None
            
            # 设置超时
            import time
            start_time = time.time()
            timeout = 15  # 15秒超时
            
            while not is_final and time.time() - start_time < timeout:
                try:
                    result = ws.recv()
                    if not result:
                        continue
                    
                    data = json.loads(result)
                    code = data.get("code")
                    if code != 0 and code is not None:
                        error = f"TTS API错误: {data.get('message', 'Unknown error')}"
                        break
                    
                    if data.get("data") and data["data"].get("audio"):
                        # 解码base64音频数据
                        chunk = base64.b64decode(data["data"]["audio"])
                        audio_data.extend(chunk)
                        
                        if data["data"].get("status") == 2:
                            is_final = True
                            break
                except websocket.WebSocketTimeoutException:
                    break
                except Exception as e:
                    logger.error(f"接收TTS响应失败: {str(e)}")
                    break
            
            ws.close()
            
            if error:
                raise Exception(error)
            
            if not audio_data:
                raise Exception("未收到音频数据")
            
            # 将音频数据转换为bytes
            audio_bytes = bytes(audio_data)
            logger.info(f"文本转语音完成，音频大小: {len(audio_bytes)} bytes")
            return audio_bytes
            
        except Exception as e:
            logger.error(f"文本转语音失败: {str(e)}")
            raise
    
    def _build_asr_url(self) -> str:
        # 生成RFC1123格式的时间戳
        date = datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')
        
        # 构建签名字符串
        signature_origin = f"host: iat-api.xfyun.cn\ndate: {date}\nGET /v2/iat HTTP/1.1"
        
        # 计算签名
        signature_sha = hmac.new(
            self.api_secret.encode('utf-8'),
            signature_origin.encode('utf-8'),
            digestmod=hashlib.sha256
        ).digest()
        
        signature = base64.b64encode(signature_sha).decode('utf-8')
        
        # 构建授权头
        authorization_origin = f'api_key="{self.api_key}", algorithm="hmac-sha256", headers="host date request-line", signature="{signature}"'
        authorization = base64.b64encode(authorization_origin.encode('utf-8')).decode('utf-8')
        
        # 构建查询参数
        params = {
            "authorization": authorization,
            "date": date,
            "host": "iat-api.xfyun.cn"
        }
        
        return f"{self.asr_url}?{urlencode(params)}"
    
    def _build_tts_websocket_url(self) -> str:
        """
        构建TTS WebSocket URL
        参考语音功能测试项目的generateAuthUrl函数
        """
        # 生成RFC1123格式的时间戳
        date = datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')
        
        # 构建签名字符串
        signature_origin = f"host: tts-api.xfyun.cn\ndate: {date}\nGET /v2/tts HTTP/1.1"
        
        # 计算签名
        signature_sha = hmac.new(
            self.api_secret.encode('utf-8'),
            signature_origin.encode('utf-8'),
            digestmod=hashlib.sha256
        ).digest()
        
        signature = base64.b64encode(signature_sha).decode('utf-8')
        
        # 构建授权头
        authorization_origin = f'api_key="{self.api_key}", algorithm="hmac-sha256", headers="host date request-line", signature="{signature}"'
        authorization = base64.b64encode(authorization_origin.encode('utf-8')).decode('utf-8')
        
        # 构建查询参数
        params = {
            "authorization": authorization,
            "date": date,
            "host": "tts-api.xfyun.cn"
        }
        
        return f"{self.tts_ws_url}?{urlencode(params)}"
    
    def _generate_tts_request(self, text: str) -> dict:
        """
        生成TTS请求帧
        参考语音功能测试项目的generateTtsRequest函数
        """
        return {
            "common": {
                "app_id": self.app_id
            },
            "business": {
                "aue": "lame",           # 音频编码格式，lame表示MP3
                "sfl": 1,                # 流式返回
                "auf": "audio/L16;rate=16000",
                "vcn": "xiaoyan",        # 发音人
                "speed": 50,             # 语速
                "volume": 50,            # 音量
                "pitch": 50,             # 音高
                "bgs": 0,                # 背景音
                "tte": "UTF8"            # 文本编码
            },
            "data": {
                "status": 2,             # 状态，2表示最后一帧
                "text": base64.b64encode(text.encode('utf-8')).decode('utf-8'),
                "encoding": "utf8"
            }
        }
    
    def _send_audio_data(self, ws, audio_data: bytes):
        # 构建请求帧 - 参考语音功能测试项目的参数
        request_data = {
            "common": {
                "app_id": self.app_id
            },
            "business": {
                "language": "zh_cn",
                "domain": "iat",          # 语音听写领域
                "accent": "mandarin",
                "sample_rate": "16000",   # 字符串类型，API要求
                "vad_eos": 5000,          # 静音检测断点参数（毫秒）- 调整为5000
                "dwa": "wpgs",            # 动态修正
                "ptt": 1                  # 添加标点符号，默认开启
            },
            "data": {
                "status": 0,
                "format": "audio/L16;rate=16000",
                "encoding": "raw",
                "audio": base64.b64encode(audio_data[:1024]).decode('utf-8')
            }
        }
        
        # 发送第一帧
        ws.send(json.dumps(request_data))
        
        # 发送剩余的音频数据（分片）
        chunk_size = 1280  # 每帧音频大小
        for i in range(1024, len(audio_data), chunk_size):
            chunk = audio_data[i:min(i + chunk_size, len(audio_data))]
            if chunk:
                request_data["data"]["status"] = 1
                request_data["data"]["audio"] = base64.b64encode(chunk).decode('utf-8')
                ws.send(json.dumps(request_data))
        
        # 发送结束帧
        request_data["data"]["status"] = 2
        request_data["data"]["audio"] = ""
        ws.send(json.dumps(request_data))
    
    def _receive_recognition_result(self, ws) -> str:
        full_text = ""
        
        while True:
            try:
                result = ws.recv()
                if not result:
                    break
                    
                data = json.loads(result)
                
                code = data.get("code")
                if code != 0:
                    error_msg = data.get("message", "Unknown error")
                    logger.error(f"语音识别错误: {error_msg}")
                    break
                
                # 解析结果
                if "data" in data:
                    result_data = data["data"]["result"]
                    if result_data:
                        for word in result_data.get("ws", []):
                            for cw in word.get("cw", []):
                                full_text += cw.get("w", "")
                
                # 检查是否结束
                if data.get("data", {}).get("status") == 2:
                    break
                    
            except websocket.WebSocketConnectionClosedException:
                break
            except Exception as e:
                logger.error(f"接收识别结果失败: {str(e)}")
                break
        
        return full_text
    
