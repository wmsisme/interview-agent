#!/usr/bin/env python3
"""测试禁用VAD模式"""
import os
import time
import base64
import numpy as np
from PIL import Image, ImageDraw
import io
import dashscope
from dashscope.audio.qwen_omni import OmniRealtimeConversation, OmniRealtimeCallback, MultiModality

API_KEY = "sk-206a776b2b1a4422bef8941e33e10cc5"
MODEL = "qwen3.5-omni-plus-realtime"
VOICE = "Ethan"
URL = "wss://dashscope.aliyuncs.com/api-ws/v1/realtime"

def generate_audio_chunk():
    """生成音频数据"""
    duration = 0.025  # 25ms
    sample_rate = 16000
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    freq = 440  # 440Hz
    wave = np.sin(2 * np.pi * freq * t)
    wave_int16 = (wave * 32767 * 0.2).astype(np.int16)
    return wave_int16.tobytes()

class SimpleCallback(OmniRealtimeCallback):
    def __init__(self):
        super().__init__()
        self.events = []
        self.start_time = time.time()
        
    def on_event(self, response):
        event_type = response.get('type')
        elapsed = time.time() - self.start_time
        self.events.append((event_type, elapsed, response))
        
        if event_type == 'session.created':
            print(f"[{elapsed:.2f}s] ✅ 会话已创建")
        elif event_type == 'session.updated':
            print(f"[{elapsed:.2f}s] ✅ 会话已更新")
        elif event_type == 'response.created':
            print(f"[{elapsed:.2f}s] 🔊 AI开始生成响应!")
        elif event_type == 'response.done':
            print(f"[{elapsed:.2f}s] ✅ 响应完成")
        elif event_type == 'error':
            print(f"[{elapsed:.2f}s] ❌ 错误: {response.get('message', '未知')}")
        elif event_type == 'response.audio.delta':
            print(f"[{elapsed:.2f}s] 🎵 收到音频数据")
        elif event_type == 'response.audio_transcript.delta':
            text = response.get('delta', '')
            print(f"[{elapsed:.2f}s] 💬 {text}", end='', flush=True)
            
    def on_close(self, close_status_code, close_msg):
        print(f"[{time.time()-self.start_time:.2f}s] 🔌 连接关闭")

def test_no_vad_simple():
    """测试禁用VAD，简单指令"""
    print("=== 测试1: 禁用VAD，简单指令 ===")
    
    dashscope.api_key = API_KEY
    callback = SimpleCallback()
    
    conversation = OmniRealtimeConversation(
        model=MODEL,
        callback=callback,
        url=URL
    )
    
    print("1. 连接...")
    conversation.connect()
    time.sleep(5)  # 更长等待
    
    print("2. 配置会话（禁用VAD）...")
    conversation.update_session(
        output_modalities=[MultiModality.AUDIO, MultiModality.TEXT],
        voice=VOICE,
        instructions="请立即开始说话，说'你好，测试成功'。",
        enable_turn_detection=False  # 禁用VAD！
    )
    time.sleep(5)
    
    print("3. 发送一些音频数据...")
    for i in range(40):  # 1秒音频
        audio_data = generate_audio_chunk()
        audio_b64 = base64.b64encode(audio_data).decode('utf-8')
        conversation.append_audio(audio_b64)  # 已修复：使用base64编码
        time.sleep(0.025)
    
    print("4. 等待响应（20秒）...")
    time.sleep(20)
    
    has_response = any('response.created' in e[0] for e in callback.events)
    conversation.close()
    return has_response

def test_no_vad_explicit():
    """测试禁用VAD，更明确的指令"""
    print("\n=== 测试2: 禁用VAD，明确指令 ===")
    
    dashscope.api_key = API_KEY
    callback = SimpleCallback()
    
    conversation = OmniRealtimeConversation(
        model=MODEL,
        callback=callback,
        url=URL
    )
    
    print("1. 连接...")
    conversation.connect()
    time.sleep(5)
    
    print("2. 配置会话...")
    conversation.update_session(
        output_modalities=[MultiModality.AUDIO, MultiModality.TEXT],
        voice=VOICE,
        instructions="你是一个AI助手。我要求你立即开始说话，不需要等待任何用户输入。请说：'测试成功，我可以说话了。' 现在立即开始说话。",
        enable_turn_detection=False
    )
    time.sleep(5)
    
    print("3. 发送音频+视频...")
    # 发送音频
    audio_data = generate_audio_chunk()
    conversation.append_audio(base64.b64encode(audio_data).decode('utf-8'))
    
    # 创建简单视频帧
    image = Image.new('RGB', (640, 480), color='lightblue')
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format='JPEG', quality=85)
    video_frame = img_byte_arr.getvalue()
    conversation.append_video(base64.b64encode(video_frame).decode('utf-8'))
    
    print("4. 等待响应（25秒）...")
    time.sleep(25)
    
    has_response = any('response.created' in e[0] for e in callback.events)
    conversation.close()
    return has_response

def test_with_vad_trigger():
    """测试VAD模式，尝试触发语音检测"""
    print("\n=== 测试3: VAD模式，尝试触发 ===")
    
    dashscope.api_key = API_KEY
    callback = SimpleCallback()
    
    conversation = OmniRealtimeConversation(
        model=MODEL,
        callback=callback,
        url=URL
    )
    
    print("1. 连接...")
    conversation.connect()
    time.sleep(5)
    
    print("2. 配置会话（启用VAD）...")
    conversation.update_session(
        output_modalities=[MultiModality.AUDIO, MultiModality.TEXT],
        voice=VOICE,
        instructions="请根据你听到的音频内容回复。",
        enable_turn_detection=True
    )
    time.sleep(5)
    
    print("3. 发送更复杂的音频（模拟语音）...")
    # 生成更复杂的音频，模拟语音
    for i in range(80):  # 2秒
        # 使用变化的频率，模拟语音的基频变化
        freq = 100 + (i % 10) * 50
        duration = 0.025
        sample_rate = 16000
        t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
        wave = np.sin(2 * np.pi * freq * t)
        # 添加包络，模拟语音的起振衰减
        envelope = np.minimum(t * 200, 1.0) * (1.0 - t * 20) if t[-1] < 0.05 else 1.0
        wave = wave * envelope
        wave_int16 = (wave * 32767 * 0.3).astype(np.int16)
        
        audio_b64 = base64.b64encode(wave_int16.tobytes()).decode('utf-8')
        conversation.append_audio(audio_b64)
        time.sleep(0.025)
    
    print("4. 等待响应（20秒）...")
    time.sleep(20)
    
    has_response = any('response.created' in e[0] for e in callback.events)
    conversation.close()
    return has_response

def main():
    print("测试VAD模式对AI响应的影响...")
    
    print("\n测试1: 禁用VAD，简单指令")
    result1 = test_no_vad_simple()
    
    time.sleep(5)
    
    print("\n测试2: 禁用VAD，明确指令")
    result2 = test_no_vad_explicit()
    
    time.sleep(5)
    
    print("\n测试3: 启用VAD，复杂音频")
    result3 = test_with_vad_trigger()
    
    print(f"\n=== 最终结果 ===")
    print(f"禁用VAD（简单指令）: {'✅ AI响应' if result1 else '❌ 无响应'}")
    print(f"禁用VAD（明确指令）: {'✅ AI响应' if result2 else '❌ 无响应'}")
    print(f"启用VAD（复杂音频）: {'✅ AI响应' if result3 else '❌ 无响应'}")
    
    if not any([result1, result2, result3]):
        print("\n⚠️ 所有测试都失败")
        print("可能的原因:")
        print("1. API密钥问题（虽然有权限，但可能有其他限制）")
        print("2. 音频格式问题（虽然正确，但可能不被接受）")
        print("3. 连接问题（WebSocket连接可能不完整）")
        print("4. 模型服务问题（实时模型可能不可用）")
        
        print("\n建议:")
        print("1. 直接运行参考文件，对比输出")
        print("2. 检查API调用日志")
        print("3. 尝试其他实时模型")

if __name__ == "__main__":
    main()