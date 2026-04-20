#!/usr/bin/env python3
"""测试发送视频帧"""
import os
import time
import base64
import numpy as np
import dashscope
from dashscope.audio.qwen_omni import OmniRealtimeConversation, OmniRealtimeCallback, MultiModality

API_KEY = "REMOVED_API_KEY"

class VideoTestCallback(OmniRealtimeCallback):
    def __init__(self):
        super().__init__()
        self.events = []
        self.start_time = time.time()
        
    def on_event(self, response):
        event_type = response.get('type')
        elapsed = time.time() - self.start_time
        self.events.append((event_type, elapsed))
        
        if event_type == 'session.created':
            print(f"[{elapsed:.2f}s] 📄 会话已创建")
        elif event_type == 'session.updated':
            print(f"[{elapsed:.2f}s] ✅ 会话配置已更新")
        elif event_type == 'response.created':
            print(f"[{elapsed:.2f}s] 🔊 AI开始响应!")
        elif event_type == 'response.audio_transcript.delta':
            text = response.get('delta', '')
            print(f"[{elapsed:.2f}s] 💬 {text}", end='', flush=True)
        elif event_type == 'response.done':
            print(f"\n[{elapsed:.2f}s] ✅ 响应完成")
        elif event_type == 'error':
            error_msg = response.get('message', '未知错误')
            print(f"[{elapsed:.2f}s] ❌ 错误: {error_msg}")
            
    def on_close(self, close_status_code, close_msg):
        print(f"[{time.time()-self.start_time:.2f}s] 🔌 连接关闭")

def create_test_image(width=320, height=240):
    """创建测试图像（简单的渐变）"""
    # 创建渐变图像
    img = np.zeros((height, width, 3), dtype=np.uint8)
    
    # 添加一些变化，避免全黑
    for y in range(height):
        for x in range(width):
            img[y, x] = [x % 256, y % 256, (x + y) % 256]
    
    # 转换为JPEG
    from PIL import Image
    import io
    
    pil_img = Image.fromarray(img)
    img_byte_arr = io.BytesIO()
    pil_img.save(img_byte_arr, format='JPEG', quality=85)
    return img_byte_arr.getvalue()

def test_with_video():
    """测试发送视频帧"""
    print("=== 测试发送音频+视频帧 ===")
    
    dashscope.api_key = API_KEY
    callback = VideoTestCallback()
    
    conversation = OmniRealtimeConversation(
        model='qwen3.5-omni-plus-realtime',
        callback=callback,
        url='wss://dashscope.aliyuncs.com/api-ws/v1/realtime'
    )
    
    print("1. 连接...")
    conversation.connect()
    time.sleep(3)
    
    print("2. 配置会话...")
    conversation.update_session(
        output_modalities=[MultiModality.AUDIO, MultiModality.TEXT],
        voice='Ethan',
        instructions="你是一个视觉AI助手，可以看到摄像头画面。请根据你看到的图像内容说话。",
        enable_turn_detection=True
    )
    time.sleep(3)
    
    print("3. 发送初始音频帧（触发）...")
    audio_data = b'\x00' * 800
    audio_b64 = base64.b64encode(audio_data).decode('utf-8')
    conversation.append_audio(audio_b64)
    print("✅ 初始音频已发送")
    time.sleep(0.5)
    
    print("4. 发送视频帧...")
    try:
        video_frame = create_test_image()
        video_b64 = base64.b64encode(video_frame).decode('utf-8')
        conversation.append_video(video_b64)
        print(f"✅ 视频帧已发送 ({len(video_frame)} bytes)")
    except Exception as e:
        print(f"❌ 发送视频帧失败: {e}")
        return False
    
    print("5. 持续发送音频数据（10秒）...")
    start_time = time.time()
    audio_count = 0
    
    while time.time() - start_time < 10:
        audio_data = b'\x00' * 800
        audio_b64 = base64.b64encode(audio_data).decode('utf-8')
        
        try:
            conversation.append_audio(audio_b64)
            audio_count += 1
        except Exception as e:
            print(f"\n❌ 发送音频失败: {e}")
            break
        
        # 每秒发送一个视频帧
        if audio_count % 40 == 0:  # 40帧 = 1秒
            try:
                # 创建稍微不同的图像
                import numpy as np
                video_frame = create_test_image()
                video_b64 = base64.b64encode(video_frame).decode('utf-8')
                conversation.append_video(video_b64)
                print(f"📹 发送视频帧 {audio_count//40}")
            except Exception as e:
                print(f"\n❌ 发送视频帧失败: {e}")
        
        time.sleep(0.025)
    
    print(f"\n✅ 发送完成，共{audio_count}帧音频")
    
    print("6. 等待响应（10秒）...")
    time.sleep(10)
    
    print("7. 检查结果...")
    has_response = any('response.created' in e[0] for e in callback.events)
    
    if has_response:
        print("✅ AI已响应")
    else:
        print("❌ AI没有响应")
        print(f"收到的事件: {[e[0] for e in callback.events]}")
    
    print("8. 关闭连接...")
    conversation.close()
    
    return has_response

def test_simple_trigger():
    """简单触发测试：只发送一次音频+视频"""
    print("\n=== 简单触发测试 ===")
    
    dashscope.api_key = API_KEY
    callback = VideoTestCallback()
    
    conversation = OmniRealtimeConversation(
        model='qwen3.5-omni-plus-realtime',
        callback=callback,
        url='wss://dashscope.aliyuncs.com/api-ws/v1/realtime'
    )
    
    print("1. 连接...")
    conversation.connect()
    time.sleep(3)
    
    print("2. 配置会话（简单指令）...")
    conversation.update_session(
        output_modalities=[MultiModality.AUDIO, MultiModality.TEXT],
        voice='Ethan',
        instructions="请说'测试成功'。",
        enable_turn_detection=True
    )
    time.sleep(3)
    
    print("3. 发送音频...")
    for i in range(5):  # 发送5帧音频
        audio_data = b'\x00' * 800
        audio_b64 = base64.b64encode(audio_data).decode('utf-8')
        conversation.append_audio(audio_b64)
        time.sleep(0.1)
    
    print("4. 发送视频...")
    try:
        video_frame = create_test_image()
        video_b64 = base64.b64encode(video_frame).decode('utf-8')
        conversation.append_video(video_b64)
        print("✅ 视频已发送")
    except Exception as e:
        print(f"❌ 视频发送失败: {e}")
    
    print("5. 再发送一些音频...")
    for i in range(10):
        audio_data = b'\x00' * 800
        audio_b64 = base64.b64encode(audio_data).decode('utf-8')
        conversation.append_audio(audio_b64)
        time.sleep(0.1)
    
    print("6. 等待响应（15秒）...")
    time.sleep(15)
    
    print("7. 检查...")
    has_response = any('response.created' in e[0] for e in callback.events)
    
    conversation.close()
    return has_response

def main():
    print("开始测试视频帧发送...")
    
    print("\n测试1: 持续发送音频+视频")
    result1 = test_with_video()
    
    time.sleep(5)
    
    print("\n测试2: 简单触发测试")
    result2 = test_simple_trigger()
    
    print(f"\n=== 最终结果 ===")
    print(f"测试1 (持续发送): {'✅ AI响应' if result1 else '❌ 无响应'}")
    print(f"测试2 (简单触发): {'✅ AI响应' if result2 else '❌ 无响应'}")
    
    if not result1 and not result2:
        print("\n⚠️ 所有测试失败，可能的原因:")
        print("1. 账户没有实时API权限")
        print("2. 模型需要特定的触发条件（如特定音频模式）")
        print("3. 指令需要更明确的触发词")
        print("4. 需要真实的音频输入（而非静音）")

if __name__ == "__main__":
    main()