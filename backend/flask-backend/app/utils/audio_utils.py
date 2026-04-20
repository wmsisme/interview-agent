import logging
import subprocess
import tempfile
import os
import io
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

class AudioConverter:
    """
    音频格式转换工具类
    用于将WebM/Opus等格式转换为PCM 16kHz单声道
    参考语音功能测试项目中的convertWebmToPcm函数
    """
    
    @staticmethod
    def webm_to_pcm(audio_data: bytes) -> Optional[bytes]:
        """
        将WebM音频数据转换为PCM 16kHz单声道格式
        
        Args:
            audio_data: WebM格式的音频数据
            
        Returns:
            PCM格式的音频数据，或None如果转换失败
        """
        try:
            # 创建临时文件存储输入音频
            with tempfile.NamedTemporaryFile(suffix='.webm', delete=False) as input_file:
                input_file.write(audio_data)
                input_path = input_file.name
            
            # 创建临时文件存储输出音频
            with tempfile.NamedTemporaryFile(suffix='.pcm', delete=False) as output_file:
                output_path = output_file.name
            
            try:
                # 使用ffmpeg进行转换
                # 参数说明：
                # -y: 覆盖输出文件
                # -i: 输入文件
                # -ar 16000: 采样率16kHz
                # -ac 1: 单声道
                # -f s16le: PCM signed 16-bit little-endian格式
                # -acodec pcm_s16le: PCM编码
                cmd = [
                    'ffmpeg',
                    '-y',  # 覆盖输出文件
                    '-i', input_path,  # 输入文件
                    '-ar', '16000',  # 采样率16kHz
                    '-ac', '1',  # 单声道
                    '-f', 's16le',  # PCM signed 16-bit little-endian格式
                    '-acodec', 'pcm_s16le',  # PCM编码
                    output_path
                ]
                
                logger.info(f"执行ffmpeg命令: {' '.join(cmd)}")
                
                # 执行转换
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=30  # 30秒超时
                )
                
                if result.returncode != 0:
                    logger.error(f"ffmpeg转换失败: {result.stderr}")
                    return None
                
                # 读取转换后的PCM数据
                with open(output_path, 'rb') as f:
                    pcm_data = f.read()
                
                logger.info(f"音频转换成功: WebM {len(audio_data)} bytes -> PCM {len(pcm_data)} bytes")
                return pcm_data
                
            finally:
                # 清理临时文件
                try:
                    os.unlink(input_path)
                except:
                    pass
                try:
                    os.unlink(output_path)
                except:
                    pass
                
        except subprocess.TimeoutExpired:
            logger.error("音频转换超时")
            return None
        except Exception as e:
            logger.error(f"音频转换异常: {str(e)}")
            return None
    
    @staticmethod
    def is_valid_pcm(pcm_data: bytes, sample_rate: int = 16000, channels: int = 1) -> bool:
        """
        检查PCM数据是否有效
        
        Args:
            pcm_data: PCM音频数据
            sample_rate: 期望的采样率
            channels: 期望的声道数
            
        Returns:
            是否有效
        """
        if not pcm_data:
            return False
        
        # 简单的检查：PCM数据长度应该是偶数（16-bit = 2字节每样本）
        if len(pcm_data) % 2 != 0:
            logger.warning(f"PCM数据长度不是偶数: {len(pcm_data)} bytes")
            return False
        
        # 检查数据大小是否合理（至少0.1秒的音频）
        min_bytes = sample_rate * channels * 2 * 0.1  # 0.1秒的音频
        if len(pcm_data) < min_bytes:
            logger.warning(f"PCM数据太小: {len(pcm_data)} bytes, 期望至少{min_bytes} bytes")
            return False
        
        return True
    
    @staticmethod
    def convert_audio(input_data: bytes, input_format: str = 'webm') -> Optional[bytes]:
        """
        通用音频转换方法
        
        Args:
            input_data: 输入音频数据
            input_format: 输入格式（'webm', 'wav', 'mp3'等）
            
        Returns:
            转换后的PCM数据
        """
        if input_format.lower() == 'webm':
            return AudioConverter.webm_to_pcm(input_data)
        else:
            # 暂时只支持WebM格式
            logger.error(f"不支持的音频格式: {input_format}")
            return None
    
    @staticmethod
    def get_audio_info(audio_data: bytes, format: str = 'webm') -> Optional[dict]:
        """
        获取音频文件信息
        
        Args:
            audio_data: 音频数据
            format: 音频格式
            
        Returns:
            音频信息字典，包含时长、采样率、声道数等
        """
        try:
            # 创建临时文件
            with tempfile.NamedTemporaryFile(suffix=f'.{format}', delete=False) as temp_file:
                temp_file.write(audio_data)
                temp_path = temp_file.name
            
            try:
                # 使用ffprobe获取音频信息
                cmd = [
                    'ffprobe',
                    '-v', 'quiet',
                    '-print_format', 'json',
                    '-show_format',
                    '-show_streams',
                    temp_path
                ]
                
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if result.returncode != 0:
                    return None
                
                import json
                info = json.loads(result.stdout)
                
                audio_info = {
                    'format': format,
                    'size_bytes': len(audio_data),
                }
                
                # 提取音频流信息
                for stream in info.get('streams', []):
                    if stream.get('codec_type') == 'audio':
                        audio_info.update({
                            'codec': stream.get('codec_name', 'unknown'),
                            'sample_rate': int(stream.get('sample_rate', 0)),
                            'channels': stream.get('channels', 0),
                            'duration': float(stream.get('duration', 0)),
                            'bit_rate': stream.get('bit_rate', 0)
                        })
                        break
                
                return audio_info
                
            finally:
                try:
                    os.unlink(temp_path)
                except:
                    pass
                    
        except Exception as e:
            logger.error(f"获取音频信息失败: {str(e)}")
            return None