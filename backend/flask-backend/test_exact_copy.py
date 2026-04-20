#!/usr/bin/env python3
"""完全复制参考文件的测试（包括视频帧）"""
import os
import time
import base64
import numpy as np
from PIL import Image, ImageDraw
import io
import dashscope
from dashscope.audio.qwen_omni import OmniRealtimeConversation, OmniRealtimeCallback, MultiModality

# 完全复制参考文件配置
API_KEY = "REMOVED_API_KEY"
MODEL = "qwen3.5-omni-plus-realtime"
VOICE = "Ethan"
URL = "wss://dashscope.aliyuncs.com/api-ws/v1/realtime"
SAMPLE_RATE = 16000
AUDIO_CHUNK_SIZE = 800  # 25ms @ 16kHz
MAX_IMAGE_SIZE = 500 * 1024
IMAGE_FORMAT = "JPEG"
IMAGE_QUALITY = 85

def create_test_image(width=640, height=480):
    """创建测试图像（模拟摄像头画面）"""
    # 创建一个简单的图像，模拟摄像头画面
    image = Image.new('RGB', (width, height), color='lightblue')
    draw = ImageDraw.Draw(image)
    
    # 添加一些图形
    draw.ellipse([width//2-50, height//2-50, width//2+50, height//2+50], 
                 fill='red', outline='black', width=2)
    draw.text((width//2-30, height//2-10), "TEST", fill='white')
    
    # 保存为JPEG
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format=IMAGE_FORMAT, quality=IMAGE_QUALITY, optimize=True)
    return img_byte_arr.getvalue()

def generate_audio_chunk():
    """生成音频数据（模拟麦克风输入）"""
    # 生成简单的正弦波
    duration = 0.025  # 25ms
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration), endpoint=False)
    freq = 440  # 440Hz (A音)
    wave = np.sin(2 * np.pi * freq * t)
    # 转换为16位PCM，较低音量
    wave_int16 = (wave * 32767 * 0.2).astype(np.int16)
    return wave_int16.tobytes()

class ExactCopyCallback(OmniRealtimeCallback):
    """完全复制参考文件的回调"""
    def __init__(self):
        super().__init__()
        self.events = []
        self.ai_text = ""
        self.start_time = time.time()
        
    def on_event(self, response):
        event_type = response.get('type')
        elapsed = time.time() - self.start_time
        self.events.append((event_type, elapsed))
        
        if event_type == 'session.created':
            session_id = response.get('session', {}).get('id', 'unknown')
            print(f"[{elapsed:.2f}s] 📄 会话已创建: {session_id}")
            
        elif event_type == 'session.updated':
            print(f"[{elapsed:.2f}s] ✅ 会话配置已更新")
            
        elif event_type == 'response.created':
            print(f"[{elapsed:.2f}s] 🔊 AI开始生成响应")
            
        elif event_type == 'response.audio_transcript.delta':
            text = response.get('delta', '')
            self.ai_text += text
            print(f"[{elapsed:.2f}s] 💬 {text}", end='', flush=True)
            
        elif event_type == 'response.done':
            print(f"\n[{elapsed:.2f}s] ✅ AI响应完成")
            
        elif event_type == 'error':
            error_msg = response.get('message', '未知错误')
            print(f"[{elapsed:.2f}s] ❌ 错误: {error_msg}")
            
    def on_close(self, close_status_code, close_msg):
        print(f"[{time.time()-self.start_time:.2f}s] 🔌 连接关闭")

def test_exact_copy():
    """完全复制参考文件的测试"""
    print("=== 完全复制参考文件配置测试 ===")
    print(f"模型: {MODEL}")
    print(f"音色: {VOICE}")
    print(f"音频帧大小: {AUDIO_CHUNK_SIZE}字节 (25ms @ {SAMPLE_RATE}Hz)")
    
    dashscope.api_key = API_KEY
    
    callback = ExactCopyCallback()
    conversation = OmniRealtimeConversation(
        model=MODEL,
        callback=callback,
        url=URL
    )
    
    print("\n1. 连接WebSocket...")
    conversation.connect()
    time.sleep(3)
    
    print("2. 配置会话（与参考文件完全一致）...")
    conversation.update_session(
        output_modalities=[MultiModality.AUDIO, MultiModality.TEXT],
        voice=VOICE,
        instructions="你是一个视觉AI助手，可以实时看到摄像头画面。请根据你看到的视频内容回答用户的问题。",
        enable_turn_detection=True  # 使用VAD模式
    )
    time.sleep(3)
    
    print("3. 发送初始音频帧（触发AI）...")
    # 先发送音频帧
    audio_data = generate_audio_chunk()
    audio_b64 = base64.b64encode(audio_data).decode('utf-8')
    conversation.append_audio(audio_b64)
    print(f"   ✅ 已发送音频帧: {len(audio_data)}字节")
    time.sleep(0.5)
    
    print("4. 发送视频帧...")
    video_frame = create_test_image()
    video_b64 = base64.b64encode(video_frame).decode('utf-8')
    conversation.append_video(video_b64)
    print(f"   ✅ 已发送视频帧: {len(video_frame)}字节")
    time.sleep(0.5)
    
    print("5. 持续发送音频+视频数据（10秒）...")
    start_time = time.time()
    audio_count = 0
    video_count = 0
    
    while time.time() - start_time < 10:
        # 发送音频帧
        audio_data = generate_audio_chunk()
        audio_b64 = base64.b64encode(audio_data).decode('utf-8')
        conversation.append_audio(audio_b64)
        audio_count += 1
        
        # 每秒发送一次视频帧
        if audio_count % 40 == 0:  # 40帧 = 1秒
            video_frame = create_test_image()
            video_b64 = base64.b64encode(video_frame).decode('utf-8')
            conversation.append_video(video_b64)
            video_count += 1
            print(f"   📹 发送视频帧 {video_count}")
        
        time.sleep(0.025)
    
    print(f"\n✅ 发送完成:")
    print(f"  音频帧: {audio_count}帧")
    print(f"  视频帧: {video_count}帧")
    
    print("\n6. 等待AI响应（15秒）...")
    time.sleep(15)
    
    print("\n7. 检查结果...")
    event_types = [e[0] for e in callback.events]
    print(f"收到的事件类型: {event_types}")
    
    has_response = any('response.created' in e for e in event_types)
    print(f"是否有响应事件: {'✅ 是' if has_response else '❌ 否'}")
    
    if has_response and callback.ai_text:
        print(f"AI回复内容: {callback.ai_text[:200]}...")
    
    print("\n8. 关闭连接...")
    conversation.close()
    time.sleep(2)
    
    return has_response

def test_without_video():
    """测试不发送视频帧"""
    print("\n=== 测试不发送视频帧 ===")
    
    dashscope.api_key = API_KEY
    
    callback = ExactCopyCallback()
    conversation = OmniRealtimeConversation(
        model=MODEL,
        callback=callback,
        url=URL
    )
    
    print("1. 连接...")
    conversation.connect()
    time.sleep(3)
    
    print("2. 配置会话...")
    conversation.update_session(
        output_modalities=[MultiModality.AUDIO, MultiModality.TEXT],
        voice=VOICE,
        instructions="你是一个视觉AI助手，可以实时看到摄像头画面。请根据你看到的视频内容回答用户的问题。",
        enable_turn_detection=True
    )
    time.sleep(3)
    
    print("3. 只发送音频数据（10秒）...")
    start_time = time.time()
    audio_count = 0
    
    while time.time() - start_time < 10:
        audio_data = generate_audio_chunk()
        audio_b64 = base64.b64encode(audio_data).decode('utf-8')
        conversation.append_audio(audio_b64)
        audio_count += 1
        time.sleep(0.025)
    
    print(f"✅ 发送完成: {audio_count}帧音频")
    
    print("4. 等待响应（10秒）...")
    time.sleep(10)
    
    print("5. 检查...")
    has_response = any('response.created' in e[0] for e in callback.events)
    
    conversation.close()
    return has_response

def test_reference_simplified():
    """简化的参考文件测试（只测试关键部分）"""
    print("\n=== 简化的参考文件测试 ===")
    
    dashscope.api_key = API_KEY
    
    callback = ExactCopyCallback()
    conversation = OmniRealtimeConversation(
        model=MODEL,
        callback=callback,
        url=URL
    )
    
    print("1. 连接...")
    conversation.connect()
    time.sleep(5)  # 更长等待时间
    
    print("2. 配置会话...")
    conversation.update_session(
        output_modalities=[MultiModality.AUDIO, MultiModality.TEXT],
        voice=VOICE,
        instructions="你好，请立即开始说话。",
        enable_turn_detection=True
    )
    time.sleep(5)
    
    print("3. 持续发送数据（15秒）...")
    start_time = time.time()
    
    while time.time() - start_time < 15:
        # 发送音频
        audio_data = generate_audio_chunk()
        audio_b64 = base64.b64encode(audio_data).decode('utf-8')
        conversation.append_audio(audio_b64)
        
        # 偶尔发送视频
        if int((time.time() - start_time) * 10) % 10 == 0:  # 每秒一次
            video_frame = create_test_image()
            video_b64 = base64.b64encode(video_frame).decode('utf-8')
            conversation.append_video(video_b64)
        
        time.sleep(0.025)
    
    print("4. 等待响应（15秒）...")
    time.sleep(15)
    
    has_response = any('response.created' in e[0] for e in callback.events)
    conversation.close()
    return has_response

def main():
    print("开始完全复制参考文件的测试...")
    
    print("\n测试1: 完全复制参考文件（音频+视频）")
    result1 = test_exact_copy()
    
    time.sleep(5)
    
    print("\n测试2: 不发送视频帧（仅音频）")
    result2 = test_without_video()
    
    time.sleep(5)
    
    print("\n测试3: 简化的参考文件测试")
    result3 = test_reference_simplified()
    
    print(f"\n=== 最终结果 ===")
    print(f"测试1 (音频+视频): {'✅ AI响应' if result1 else '❌ 无响应'}")
    print(f"测试2 (仅音频): {'✅ AI响应' if result2 else '❌ 无响应'}")
    print(f"测试3 (简化测试): {'✅ AI响应' if result3 else '❌ 无响应'}")
    
    if not any([result1, result2, result3]):
        print("\n⚠️ 所有测试都失败，但参考文件可以工作")
        print("可能的差异:")
        print("1. 参考文件使用真实的麦克风音频（而不是模拟音频）")
        print("2. 参考文件使用真实的摄像头视频（而不是模拟图像）")
        print("3. 网络环境或时间差异")
        print("4. 需要更长的等待时间")
        
        print("\n建议:")
        print("1. 运行参考文件确认它可以正常工作")
        print("2. 检查参考文件使用的音频/视频数据格式")
        print("3. 添加更多调试信息")

if __name__ == "__main__":
    main()