#!/usr/bin/env python3
"""完全复制参考文件的测试"""
import os
import sys
import time
import base64
import threading
import queue
import dashscope
from dashscope.audio.qwen_omni import OmniRealtimeConversation, OmniRealtimeCallback, MultiModality

# 配置
API_KEY = "sk-206a776b2b1a4422bef8941e33e10cc5"
MODEL = "qwen3.5-omni-plus-realtime"
VOICE = "Ethan"
URL = "wss://dashscope.aliyuncs.com/api-ws/v1/realtime"
AUDIO_CHUNK_SIZE = 800  # 25ms @ 16kHz

class TestCallback(OmniRealtimeCallback):
    def __init__(self):
        super().__init__()
        self.events = []
        self.has_response = False
        self.ai_text = ""
        self.start_time = time.time()
        
    def on_open(self):
        print(f"[{time.time()-self.start_time:.2f}s] ✅ WebSocket连接已打开")
        self.events.append(('open', time.time()))
        
    def on_event(self, response):
        event_type = response.get('type')
        current_time = time.time()
        elapsed = current_time - self.start_time
        self.events.append((event_type, elapsed))
        
        if event_type == 'session.created':
            session_id = response.get('session', {}).get('id', 'unknown')
            print(f"[{elapsed:.2f}s] 📄 会话已创建: {session_id}")
            
        elif event_type == 'session.updated':
            print(f"[{elapsed:.2f}s] ✅ 会话配置已更新")
            
        elif event_type == 'response.created':
            self.has_response = True
            print(f"[{elapsed:.2f}s] 🔊 AI开始生成响应")
            
        elif event_type == 'response.audio_transcript.delta':
            text = response.get('delta', '')
            self.ai_text += text
            print(f"[{elapsed:.2f}s] 💬 {text}", end='', flush=True)
            
        elif event_type == 'response.done':
            print(f"\n[{elapsed:.2f}s] ✅ AI响应完成")
            
        elif event_type == 'error':
            error_msg = response.get('message', '未知错误')
            print(f"\n[{elapsed:.2f}s] ❌ 错误: {error_msg}")
            
    def on_close(self, close_status_code, close_msg):
        print(f"[{time.time()-self.start_time:.2f}s] 🔌 连接关闭: code={close_status_code}, msg={close_msg}")

def test_exact_reference():
    """完全复制参考文件的测试"""
    print("=== 完全复制参考文件配置测试 ===")
    
    dashscope.api_key = API_KEY
    
    callback = TestCallback()
    conversation = OmniRealtimeConversation(
        model=MODEL,
        callback=callback,
        url=URL
    )
    
    print("1. 连接WebSocket...")
    conversation.connect()
    time.sleep(2)
    
    print("2. 配置会话（与参考文件完全一致）...")
    conversation.update_session(
        output_modalities=[MultiModality.AUDIO, MultiModality.TEXT],
        voice=VOICE,
        instructions="你是一个视觉AI助手，可以实时看到摄像头画面。请根据你看到的视频内容回答用户的问题。",
        enable_turn_detection=True  # 使用VAD模式
    )
    time.sleep(2)
    
    print("3. 持续发送音频数据（10秒）...")
    start_time = time.time()
    audio_count = 0
    
    while time.time() - start_time < 10:
        # 发送800字节的音频帧（25ms @ 16kHz）
        audio_data = b'\x00' * AUDIO_CHUNK_SIZE
        audio_b64 = base64.b64encode(audio_data).decode('utf-8')
        
        try:
            conversation.append_audio(audio_b64)
            audio_count += 1
        except Exception as e:
            print(f"\n❌ 发送音频失败: {e}")
            break
        
        # 控制发送频率：大约40帧/秒（25ms/帧）
        time.sleep(0.025)
        
        # 每50帧显示进度
        if audio_count % 50 == 0:
            elapsed = time.time() - start_time
            print(f"  已发送{audio_count}帧音频，耗时{elapsed:.1f}s")
    
    print(f"\n✅ 音频发送完成，共{audio_count}帧，约{audio_count*0.025:.1f}s的音频数据")
    
    print("4. 等待AI响应（5秒）...")
    response_wait_start = time.time()
    ai_started = False
    
    while time.time() - response_wait_start < 5:
        if callback.has_response:
            ai_started = True
            print(f"\n[{time.time()-callback.start_time:.2f}s] ✅ AI已开始响应")
            break
        time.sleep(0.1)
    
    if not ai_started:
        print(f"\n❌ AI没有响应")
        print(f"事件记录: {len(callback.events)}个事件")
        for event_type, event_time in callback.events:
            print(f"  - {event_type} @ {event_time:.2f}s")
    
    print("5. 检查收到的文本...")
    if callback.ai_text:
        print(f"📋 AI回复内容: {callback.ai_text}")
    
    print("\n6. 关闭连接...")
    conversation.close()
    time.sleep(1)
    
    print("\n=== 测试结果 ===")
    if callback.has_response:
        print("✅ AI已响应")
        return True
    else:
        print("❌ AI没有响应")
        return False

def test_with_video_frame():
    """测试发送音频+视频帧"""
    print("\n=== 测试音频+视频帧发送 ===")
    
    dashscope.api_key = API_KEY
    
    callback = TestCallback()
    conversation = OmniRealtimeConversation(
        model=MODEL,
        callback=callback,
        url=URL
    )
    
    print("1. 连接...")
    conversation.connect()
    time.sleep(2)
    
    print("2. 配置会话...")
    conversation.update_session(
        output_modalities=[MultiModality.AUDIO, MultiModality.TEXT],
        voice=VOICE,
        instructions="你是一个视觉AI助手，可以实时看到摄像头画面。请根据你看到的视频内容回答用户的问题。现在请立即开始说话！",
        enable_turn_detection=True
    )
    time.sleep(2)
    
    print("3. 发送初始音频帧（触发AI）...")
    audio_data = b'\x00' * AUDIO_CHUNK_SIZE
    audio_b64 = base64.b64encode(audio_data).decode('utf-8')
    conversation.append_audio(audio_b64)
    print("✅ 初始音频帧已发送")
    time.sleep(0.5)
    
    print("4. 发送测试视频帧...")
    # 创建一个简单的测试图像（黑色矩形）
    import numpy as np
    img = np.zeros((240, 320, 3), dtype=np.uint8)
    img_bytes = bytes(img)
    img_b64 = base64.b64encode(img_bytes).decode('utf-8')
    
    try:
        conversation.append_video(img_b64)
        print("✅ 视频帧已发送")
    except Exception as e:
        print(f"❌ 发送视频帧失败: {e}")
    
    print("5. 持续发送音频数据（5秒）...")
    start_time = time.time()
    audio_count = 0
    
    while time.time() - start_time < 5:
        audio_data = b'\x00' * AUDIO_CHUNK_SIZE
        audio_b64 = base64.b64encode(audio_data).decode('utf-8')
        
        try:
            conversation.append_audio(audio_b64)
            audio_count += 1
        except Exception as e:
            print(f"\n❌ 发送音频失败: {e}")
            break
        
        time.sleep(0.025)
    
    print(f"\n✅ 发送完成，共{audio_count}帧音频")
    
    print("6. 等待响应（8秒）...")
    time.sleep(8)
    
    print("7. 检查结果...")
    if callback.has_response:
        print(f"✅ AI已响应: {callback.ai_text[:100]}...")
    else:
        print("❌ AI没有响应")
        print(f"事件: {[e[0] for e in callback.events]}")
    
    conversation.close()
    return callback.has_response

def main():
    """主函数"""
    print("开始测试完全复制参考文件的配置...")
    
    # 测试1: 仅音频
    print("\n测试1: 仅发送音频数据")
    result1 = test_exact_reference()
    
    time.sleep(3)
    
    # 测试2: 音频+视频
    print("\n测试2: 发送音频+视频帧")
    result2 = test_with_video_frame()
    
    print(f"\n=== 最终结果 ===")
    print(f"测试1 (仅音频): {'✅ 成功' if result1 else '❌ 失败'}")
    print(f"测试2 (音频+视频): {'✅ 成功' if result2 else '❌ 失败'}")
    
    if not result1 and not result2:
        print("\n⚠️ 所有测试都失败，可能的问题:")
        print("1. API密钥无效或过期")
        print("2. 网络连接问题（无法连接到DashScope）")
        print("3. 模型服务不可用")
        print("4. 账户余额不足")
        print("\n建议:")
        print("1. 验证API密钥有效性")
        print("2. 运行参考文件确认API正常工作")
        print("3. 检查网络连接")

if __name__ == "__main__":
    main()