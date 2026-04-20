#!/usr/bin/env python3
"""测试顺序修复：先音频后视频"""
import os
import sys
import time
import base64
import numpy as np
from PIL import Image, ImageDraw
import io

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    import dashscope
    from dashscope.audio.qwen_omni import OmniRealtimeConversation, OmniRealtimeCallback, MultiModality, AudioFormat
    
    print("✅ 导入依赖成功")
except ImportError as e:
    print(f"❌ 导入依赖失败: {e}")
    sys.exit(1)

# API密钥
api_key = os.environ.get('VIDEO_CHAT_API_KEY', 'REMOVED_API_KEY')

def create_test_image():
    """创建测试图像"""
    image = Image.new('RGB', (640, 480), color='white')
    draw = ImageDraw.Draw(image)
    draw.rectangle([50, 50, 150, 150], fill='red', outline='black')
    
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format='JPEG', quality=85)
    return img_byte_arr.getvalue()

def generate_sine_wave(freq=440, duration=0.025):
    """生成正弦波"""
    sample_rate = 16000
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    wave = np.sin(2 * np.pi * freq * t)
    wave_int16 = (wave * 32767).astype(np.int16)
    return wave_int16.tobytes()

class OrderCallback(OmniRealtimeCallback):
    """顺序测试回调"""
    def __init__(self):
        super().__init__()
        self.events = []
        self.ai_text = ""
        
    def on_open(self):
        self.events.append(('open', time.time()))
        print("📡 WebSocket连接已打开")
        
    def on_event(self, response):
        event_type = response.get('type')
        self.events.append((event_type, time.time()))
        
        if event_type == 'session.created':
            print(f"✅ 会话创建成功: {response['session']['id']}")
            
        elif event_type == 'response.created':
            print("🔊 AI开始生成响应")
            
        elif event_type == 'response.audio_transcript.delta':
            text_delta = response.get('delta', '')
            self.ai_text += text_delta
            print(f"💬 {text_delta}", end='', flush=True)
            
        elif event_type == 'response.audio_transcript.done':
            print(f"\n✅ AI完整文本")
            
        elif event_type == 'response.done':
            print("\n✅ AI响应完成")
            
        elif event_type == 'error':
            error_msg = response.get('message', '未知错误')
            print(f"\n❌ 错误: {error_msg}")

def test_audio_first():
    """测试先发送音频"""
    print("\n=== 测试先发送音频（后发送视频） ===")
    
    dashscope.api_key = api_key
    callback = OrderCallback()
    
    try:
        conversation = OmniRealtimeConversation(
            model='qwen3.5-omni-plus-realtime',
            callback=callback,
            url='wss://dashscope.aliyuncs.com/api-ws/v1/realtime'
        )
        
        conversation.connect()
        print("✅ 连接成功")
        time.sleep(1)
        
        # 配置会话
        conversation.update_session(
            output_modalities=[MultiModality.AUDIO, MultiModality.TEXT],
            voice='Ethan',
            instructions="你是一位面试官。请立即开始你的自我介绍。",
            enable_turn_detection=False,
            input_audio_format=AudioFormat.PCM_16000HZ_MONO_16BIT,
            output_audio_format=AudioFormat.PCM_16000HZ_MONO_16BIT,
            smooth_output=True
        )
        
        print("✅ 会话配置完成")
        time.sleep(2)
        
        # 关键：先发送音频帧
        print("1. 先发送音频帧...")
        audio_data = generate_sine_wave(freq=440, duration=0.025)
        audio_b64 = base64.b64encode(audio_data).decode('utf-8')
        conversation.append_audio(audio_b64)
        print(f"   🎤 音频: {len(audio_data)}字节")
        
        time.sleep(0.1)  # 短暂等待
        
        # 然后发送视频帧
        print("2. 再发送视频帧...")
        image_data = create_test_image()
        image_b64 = base64.b64encode(image_data).decode('utf-8')
        conversation.append_video(image_b64)
        print(f"   📹 视频: {len(image_data)}字节")
        
        # 持续发送（保持正确顺序）
        print("3. 持续发送数据（5秒）...")
        start_time = time.time()
        count = 0
        
        while time.time() - start_time < 5:
            time.sleep(0.2)
            
            # 先音频
            audio_data = generate_sine_wave(freq=440, duration=0.025)
            audio_b64 = base64.b64encode(audio_data).decode('utf-8')
            conversation.append_audio(audio_b64)
            
            # 然后视频（每500ms发送一次）
            if count % 2 == 0:
                image_data = create_test_image()
                image_b64 = base64.b64encode(image_data).decode('utf-8')
                conversation.append_video(image_b64)
            
            count += 1
            if count % 5 == 0:
                print(".", end='', flush=True)
        
        print(f"\n✅ 发送完成，共{count}次发送")
        
        # 等待AI回复
        print("⏳ 等待AI回复（10秒）...")
        wait_start = time.time()
        ai_started = False
        
        while time.time() - wait_start < 10:
            if any(event[0] == 'response.created' for event in callback.events):
                ai_started = True
                print("\n✅ AI已开始回复")
                break
            time.sleep(0.5)
        
        if not ai_started:
            print("\n❌ AI没有回复")
        
        # 打印事件
        print(f"\n事件列表:")
        for i, (event_type, timestamp) in enumerate(callback.events):
            elapsed = timestamp - callback.events[0][1] if i > 0 else 0
            print(f"  {i+1:2d}. {event_type:30s} (+{elapsed:.2f}s)")
        
        conversation.close()
        return ai_started
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

def test_video_first():
    """测试先发送视频（应该会失败）"""
    print("\n=== 测试先发送视频（应该会失败） ===")
    
    dashscope.api_key = api_key
    callback = OrderCallback()
    
    try:
        conversation = OmniRealtimeConversation(
            model='qwen3.5-omni-plus-realtime',
            callback=callback,
            url='wss://dashscope.aliyuncs.com/api-ws/v1/realtime'
        )
        
        conversation.connect()
        time.sleep(1)
        
        conversation.update_session(
            output_modalities=[MultiModality.AUDIO, MultiModality.TEXT],
            voice='Ethan',
            instructions="你是一位面试官。请立即开始你的自我介绍。",
            enable_turn_detection=False,
            input_audio_format=AudioFormat.PCM_16000HZ_MONO_16BIT,
            output_audio_format=AudioFormat.PCM_16000HZ_MONO_16BIT
        )
        
        time.sleep(2)
        
        # 先发送视频（错误顺序）
        print("1. 先发送视频帧（错误顺序）...")
        image_data = create_test_image()
        image_b64 = base64.b64encode(image_data).decode('utf-8')
        conversation.append_video(image_b64)
        
        time.sleep(0.1)
        
        # 然后发送音频
        print("2. 再发送音频帧...")
        audio_data = generate_sine_wave(freq=440, duration=0.025)
        audio_b64 = base64.b64encode(audio_data).decode('utf-8')
        conversation.append_audio(audio_b64)
        
        print("3. 等待5秒...")
        time.sleep(5)
        
        # 检查错误
        has_error = any(event[0] == 'error' for event in callback.events)
        
        print(f"\n结果: {'有错误' if has_error else '无错误'}")
        
        conversation.close()
        return not has_error  # 如果没有错误，返回True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

def main():
    """运行顺序测试"""
    print("=== 测试API顺序要求 ===")
    
    print("\n1. 测试先发送视频（应该会失败）")
    result1 = test_video_first()
    
    time.sleep(3)
    
    print("\n2. 测试先发送音频（应该会成功）")
    result2 = test_audio_first()
    
    print(f"\n=== 测试结果 ===")
    print(f"先视频后音频: {'✅ 通过' if result1 else '❌ 失败'}")
    print(f"先音频后视频: {'✅ 通过' if result2 else '❌ 失败'}")
    
    if result2:
        print("\n✅ 发现关键问题：必须先发送音频帧")
        print("修复方案:")
        print("1. 修改前端，确保先发送音频数据")
        print("2. 修改video_chat_service.py，在发送视频前先发送音频")
        print("3. 修改configure_interviewer，先发送初始音频帧")

if __name__ == "__main__":
    main()