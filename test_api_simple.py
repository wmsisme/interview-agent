#!/usr/bin/env python3
"""简单的API测试，不依赖摄像头"""
import os
import time
import base64
import dashscope
from dashscope.audio.qwen_omni import OmniRealtimeConversation, OmniRealtimeCallback, MultiModality

API_KEY = "REMOVED_API_KEY"

class SimpleCallback(OmniRealtimeCallback):
    def __init__(self):
        super().__init__()
        self.events = []
        self.start_time = time.time()
        
    def on_open(self):
        print(f"[{time.time()-self.start_time:.2f}s] ✅ WebSocket连接已打开")
        self.events.append(('open', time.time()))
        
    def on_event(self, response):
        event_type = response.get('type')
        elapsed = time.time() - self.start_time
        print(f"[{elapsed:.2f}s] 📨 事件: {event_type}")
        
        if event_type == 'response.created':
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

def test_simple():
    print("=== 简单API测试 ===")
    
    dashscope.api_key = API_KEY
    
    callback = SimpleCallback()
    conversation = OmniRealtimeConversation(
        model='qwen3.5-omni-plus-realtime',
        callback=callback,
        url='wss://dashscope.aliyuncs.com/api-ws/v1/realtime'
    )
    
    print("1. 连接...")
    conversation.connect()
    time.sleep(2)
    
    print("2. 配置会话...")
    conversation.update_session(
        output_modalities=[MultiModality.AUDIO, MultiModality.TEXT],
        voice='Ethan',
        instructions="请说'你好，我是AI助手'。",
        enable_turn_detection=True
    )
    time.sleep(2)
    
    print("3. 发送音频数据触发AI...")
    for i in range(20):  # 发送20帧音频（约0.5秒）
        audio_data = b'\x00' * 800  # 25ms
        audio_b64 = base64.b64encode(audio_data).decode('utf-8')
        conversation.append_audio(audio_b64)
        time.sleep(0.025)
    
    print("4. 等待响应（8秒）...")
    time.sleep(8)
    
    print("5. 关闭连接...")
    conversation.close()
    
    print("\n=== 测试完成 ===")
    # 检查是否有response.created事件
    has_response = any('response.created' in str(e) for e in callback.events)
    return has_response

def test_without_vad():
    """测试不使用VAD模式"""
    print("\n=== 测试不使用VAD模式 ===")
    
    dashscope.api_key = API_KEY
    
    callback = SimpleCallback()
    conversation = OmniRealtimeConversation(
        model='qwen3.5-omni-plus-realtime',
        callback=callback,
        url='wss://dashscope.aliyuncs.com/api-ws/v1/realtime'
    )
    
    print("1. 连接...")
    conversation.connect()
    time.sleep(2)
    
    print("2. 配置会话（不使用VAD）...")
    conversation.update_session(
        output_modalities=[MultiModality.AUDIO, MultiModality.TEXT],
        voice='Ethan',
        instructions="请说'你好，测试成功'。",
        enable_turn_detection=False  # 禁用VAD
    )
    time.sleep(2)
    
    print("3. 发送更多音频数据...")
    for i in range(40):  # 发送40帧音频（约1秒）
        audio_data = b'\x00' * 800
        audio_b64 = base64.b64encode(audio_data).decode('utf-8')
        conversation.append_audio(audio_b64)
        time.sleep(0.025)
    
    print("4. 等待响应（8秒）...")
    time.sleep(8)
    
    print("5. 关闭...")
    conversation.close()
    
    has_response = any('response.created' in str(e) for e in callback.events)
    return has_response

def main():
    print("测试DashScope API响应...")
    
    print("\n测试1: 使用VAD模式")
    result1 = test_simple()
    
    time.sleep(3)
    
    print("\n测试2: 不使用VAD模式")
    result2 = test_without_vad()
    
    print(f"\n=== 最终结果 ===")
    print(f"测试1 (VAD模式): {'✅ AI有响应' if result1 else '❌ AI无响应'}")
    print(f"测试2 (无VAD模式): {'✅ AI有响应' if result2 else '❌ AI无响应'}")
    
    if not result1 and not result2:
        print("\n❌ 两个测试都失败，可能是以下问题:")
        print("1. API密钥无效/过期")
        print("2. 账户余额不足")
        print("3. 网络连接问题")
        print("4. DashScope服务问题")

if __name__ == "__main__":
    main()