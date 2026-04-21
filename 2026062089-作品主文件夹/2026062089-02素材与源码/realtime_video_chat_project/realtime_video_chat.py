# 实时视频对话测试 - 摄像头视频+音频对话
import os
import cv2
import base64
import time
import threading
import queue
import numpy as np
import pyaudio
from PIL import Image
import io
import json
import sys
from dashscope.audio.qwen_omni import OmniRealtimeConversation, OmniRealtimeCallback, MultiModality
import dashscope

from config import API_KEY, MODEL, URL, VOICE, SAMPLE_RATE, AUDIO_CHUNK_SIZE, MAX_IMAGE_SIZE, IMAGE_FORMAT, IMAGE_QUALITY

class RealtimeVideoChatCallback(OmniRealtimeCallback):
    """实时视频聊天回调类"""
    def __init__(self):
        super().__init__()
        # 音频处理相关
        self.pya = None
        self.mic_stream = None
        self.out_stream = None
        self.response_done_event = threading.Event()
        self.last_response_text = ""
        
        # 音频队列和线程
        self.audio_queue = queue.Queue()  # 音频数据队列（从回调到播放线程）
        self.mic_audio_queue = queue.Queue()  # 麦克风音频队列（发送到服务器）
        self.playback_thread = None
        self.stop_playback = threading.Event()
        
        # 状态控制
        self.is_playing = False  # 是否正在播放AI回复
        self.mic_enabled = True  # 麦克风是否启用
        self.playback_volume = 0.5  # 播放音量 (0.0-1.0)
        
        # 回声抑制
        self.echo_suppression_enabled = True
        self.last_playback_time = 0
        self.echo_suppression_duration = 0.5  # 回声抑制持续时间（秒）
        
        # 视频相关
        self.video_frames_queue = queue.Queue()  # 视频帧队列
        self.video_thread = None
        self.stop_video = threading.Event()
        
    def on_open(self):
        print("✅ 连接成功")
        # 初始化音频输出
        try:
            self.pya = pyaudio.PyAudio()
            
            # 音频输出流（播放AI回复）
            self.out_stream = self.pya.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=24000,
                output=True,
                frames_per_buffer=2048
            )
            
            # 麦克风输入流
            self.mic_stream = self.pya.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=SAMPLE_RATE,
                input=True,
                frames_per_buffer=AUDIO_CHUNK_SIZE
            )
            
            print("✅ 音频设备初始化完成")
            
            # 启动音频播放线程
            self.stop_playback.clear()
            self.playback_thread = threading.Thread(target=self._playback_worker, daemon=True)
            self.playback_thread.start()
            print("✅ 音频播放线程已启动")
            
            # 启动麦克风采集线程
            self.mic_thread = threading.Thread(target=self._mic_capture_worker, daemon=True)
            self.mic_thread.start()
            print("✅ 麦克风采集线程已启动")
            
        except Exception as e:
            print(f"❌ 音频设备初始化失败: {e}")
    
    def _playback_worker(self):
        """音频播放工作线程"""
        while not self.stop_playback.is_set():
            try:
                # 从队列获取音频数据，超时时间100ms
                audio_data = self.audio_queue.get(timeout=0.1)
                if audio_data is None:  # 终止信号
                    break
                    
                # 应用音量控制
                if self.playback_volume < 1.0:
                    audio_array = np.frombuffer(audio_data, dtype=np.int16)
                    audio_array = (audio_array * self.playback_volume).astype(np.int16)
                    audio_data = audio_array.tobytes()
                
                # 播放音频数据
                if self.out_stream:
                    try:
                        self.out_stream.write(audio_data)
                        # 记录播放时间，用于回声抑制
                        self.last_playback_time = time.time()
                    except Exception as e:
                        print(f"❌ 音频播放失败: {e}")
                        
                self.audio_queue.task_done()
                
            except queue.Empty:
                # 队列为空，继续等待
                continue
            except Exception as e:
                print(f"❌ 播放线程错误: {e}")
                break
    
    def _mic_capture_worker(self):
        """麦克风采集工作线程"""
        while not self.stop_playback.is_set():
            try:
                if not self.mic_stream or not self.mic_enabled:
                    time.sleep(0.01)
                    continue
                
                # 读取麦克风数据
                audio_data = self.mic_stream.read(AUDIO_CHUNK_SIZE, exception_on_overflow=False)
                
                # 回声抑制：如果最近播放了音频，降低麦克风增益
                if self.echo_suppression_enabled and self.is_playing:
                    current_time = time.time()
                    time_since_playback = current_time - self.last_playback_time
                    
                    if time_since_playback < self.echo_suppression_duration:
                        # 降低增益来抑制回声
                        reduction_factor = max(0.3, 1.0 - (time_since_playback / self.echo_suppression_duration))
                        audio_array = np.frombuffer(audio_data, dtype=np.int16)
                        audio_array = (audio_array * reduction_factor).astype(np.int16)
                        audio_data = audio_array.tobytes()
                
                # 将音频数据放入队列，供主线程发送到服务器
                self.mic_audio_queue.put(audio_data)
                
            except Exception as e:
                print(f"❌ 麦克风采集失败: {e}")
                break
    
    def on_event(self, response):
        event_type = response.get('type')
        
        if event_type == 'conversation.item.input_audio_transcription.completed':
            user_text = response.get('transcript', '')
            print(f"\n[用户] {user_text}")
            
        elif event_type == 'response.created':
            # 服务端开始生成响应时，启用回声抑制
            if not self.is_playing:
                self.is_playing = True
                print("🔊 AI开始回复（启用回声抑制）")
            
        elif event_type == 'response.audio_transcript.delta':
            text_delta = response.get('delta', '')
            self.last_response_text += text_delta
            # 不显示文本（根据用户要求）
            # print(text_delta, end='', flush=True)
            
        elif event_type == 'response.audio_transcript.done':
            full_text = response.get('transcript', '')
            print(f"\n[助手] {full_text}")
            
        elif event_type == 'response.audio.delta':
            # 接收AI的音频回复
            if self.out_stream:
                try:
                    audio_data = base64.b64decode(response['delta'])
                    # 将音频数据放入队列，由播放线程处理
                    self.audio_queue.put(audio_data)
                except Exception as e:
                    print(f"❌ 音频数据处理失败: {e}")
                    
        elif event_type == 'response.done':
            print(f"\n✅ 响应完成")
            # 恢复麦克风完全启用
            self.is_playing = False
            self.response_done_event.set()
            
        elif event_type == 'session.created':
            print(f"✅ 会话创建成功，ID: {response['session']['id']}")
            
        elif event_type == 'error':
            error_msg = response.get('message', '未知错误')
            print(f"❌ 错误: {error_msg}")
            
    def on_close(self, close_status_code, close_msg):
        print(f"连接关闭 (code={close_status_code}, msg={close_msg})")
        self.cleanup()
        
    def cleanup(self):
        # 停止所有线程
        if hasattr(self, 'stop_playback'):
            self.stop_playback.set()
        
        # 发送终止信号到队列
        if hasattr(self, 'audio_queue'):
            try:
                self.audio_queue.put(None)
            except:
                pass
        
        # 等待线程结束
        if hasattr(self, 'playback_thread') and self.playback_thread:
            self.playback_thread.join(timeout=1.0)
        
        if hasattr(self, 'mic_thread') and self.mic_thread:
            self.mic_thread.join(timeout=1.0)
        
        # 清理音频流
        if self.out_stream:
            self.out_stream.close()
            self.out_stream = None
        
        if self.mic_stream:
            self.mic_stream.close()
            self.mic_stream = None
        
        if self.pya:
            self.pya.terminate()
            self.pya = None
        
        print("✅ 资源已清理")

def prepare_video_frame(frame, max_size=MAX_IMAGE_SIZE, quality=IMAGE_QUALITY):
    """准备视频帧数据（从video_test.py复制）"""
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
        pil_image.save(img_byte_arr, format=IMAGE_FORMAT, quality=quality, optimize=True)
        img_data = img_byte_arr.getvalue()
        
        # 检查大小
        if len(img_data) > max_size:
            # 进一步压缩
            quality = max(50, quality - 20)
            img_byte_arr = io.BytesIO()
            pil_image.save(img_byte_arr, format=IMAGE_FORMAT, quality=quality, optimize=True)
            img_data = img_byte_arr.getvalue()
            
            if len(img_data) > max_size:
                print(f"⚠️  警告: 视频帧大小 {len(img_data)}B 超过限制 {max_size}B")
                return None
        
        return img_data
        
    except Exception as e:
        print(f"❌ 视频帧处理失败: {e}")
        return None

def test_realtime_video_chat():
    """测试实时视频聊天"""
    print("=" * 60)
    print("实时视频聊天测试 - 摄像头视频+音频对话")
    print("=" * 60)
    
    # 设置API Key
    dashscope.api_key = API_KEY
    
    # 创建回调函数
    callback = RealtimeVideoChatCallback()
    
    # 创建会话
    conversation = OmniRealtimeConversation(
        model=MODEL,
        callback=callback,
        url=URL
    )
    
    try:
        # 连接
        conversation.connect()
        print("✅ 连接成功")
        
        # 配置会话：启用音频输出，使用VAD模式
        conversation.update_session(
            output_modalities=[MultiModality.AUDIO, MultiModality.TEXT],
            voice=VOICE,
            instructions="你是一个视觉AI助手，可以实时看到摄像头画面。请根据你看到的视频内容回答用户的问题。",
            enable_turn_detection=True  # 使用VAD模式
        )
        
        print("\n📋 配置信息:")
        print(f"  - 模型: {MODEL}")
        print(f"  - 音色: {VOICE}")
        print(f"  - 回声抑制: {'启用' if callback.echo_suppression_enabled else '禁用'}")
        print(f"  - 播放音量: {callback.playback_volume * 100:.0f}%")
        
        # 测试摄像头
        print("\n📷 初始化摄像头...")
        cap = cv2.VideoCapture(0)
        
        if not cap.isOpened():
            print("❌ 无法打开摄像头")
            cap = None
        else:
            # 获取摄像头信息
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            print(f"✅ 摄像头已打开: {width}x{height} @ {fps:.1f}FPS")
            
            # 创建摄像头预览窗口
            cv2.namedWindow('Camera Preview', cv2.WINDOW_NORMAL)
            cv2.resizeWindow('Camera Preview', 640, 480)
        
        print("\n🎤 音频配置完成")
        print("💡 回声抑制机制:")
        print("  - AI回复时自动降低麦克风增益")
        print("  - 播放完成后逐渐恢复麦克风灵敏度")
        print("  - 避免完全禁用麦克风")
        
        print("\n🚀 开始实时视频对话")
        print("=" * 40)
        print("操作指南:")
        print("1. 对着麦克风说话，描述你看到的画面")
        print("2. AI会分析视频内容并语音回复")
        print("3. 按 'q' 键退出")
        print("=" * 40)
        
        # 主循环
        frame_count = 0
        last_frame_time = time.time()
        frame_interval = 1.0  # 每秒发送1帧
        
        try:
            while True:
                current_time = time.time()
                
                # 处理摄像头视频
                if cap and cap.isOpened():
                    ret, frame = cap.read()
                    if ret:
                        # 显示预览
                        preview = cv2.resize(frame, (640, 480))
                        cv2.putText(preview, "Real-time Video Chat", (10, 30), 
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                        cv2.putText(preview, "Press 'q' to quit", (10, 60), 
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                        cv2.putText(preview, f"Frame: {frame_count}", (10, 90), 
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                        
                        cv2.imshow('Camera Preview', preview)
                        
                        # 按固定间隔发送视频帧
                        if current_time - last_frame_time >= frame_interval:
                            frame_data = prepare_video_frame(frame)
                            if frame_data:
                                try:
                                    # 发送视频帧
                                    frame_b64 = base64.b64encode(frame_data).decode()
                                    conversation.append_video(frame_b64)
                                    print(f"📹 发送视频帧 {frame_count} ({len(frame_data)}B)")
                                except Exception as e:
                                    print(f"❌ 发送视频帧失败: {e}")
                            
                            last_frame_time = current_time
                            frame_count += 1
                
                # 发送麦克风音频数据
                try:
                    while not callback.mic_audio_queue.empty():
                        audio_data = callback.mic_audio_queue.get_nowait()
                        conversation.append_audio(base64.b64encode(audio_data).decode())
                        callback.mic_audio_queue.task_done()
                except queue.Empty:
                    pass
                except Exception as e:
                    print(f"❌ 发送音频数据失败: {e}")
                
                # 检查退出键
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    print("\n🛑 用户请求退出")
                    break
                
                # 短暂休眠，避免CPU占用过高
                time.sleep(0.01)
                
        except KeyboardInterrupt:
            print("\n🛑 用户中断")
            
        finally:
            # 清理摄像头
            if cap and cap.isOpened():
                cap.release()
            cv2.destroyAllWindows()
        
        print("\n✅ 实时视频对话测试完成")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        # 清理资源
        conversation.close()
        print("✅ 资源已清理")

if __name__ == "__main__":
    test_realtime_video_chat()