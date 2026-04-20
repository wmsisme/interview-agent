#!/usr/bin/env python3
"""测试发送真实音频数据（非静音）"""
import os
import time
import base64
import numpy as np
import dashscope
from dashscope.audio.qwen_omni import OmniRealtimeConversation, OmniRealtimeCallback, MultiModality

API_KEY = "sk-206a776b2b1a4422bef8941e33e10cc5"

def generate_sine_wave(freq=440, duration=0.025, sample_rate=16000):
    """生成正弦波音频数据（模拟语音）"""
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    wave = np.sin(2 * np.pi * freq * t)
    # 转换为16位PCM
    wave_int16 = (wave * 32767 * 0.3).astype(np.int16)  # 30%音量
    return wave_int16.tobytes()

def generate_chirp(start_freq=200, end_freq=800, duration=0.025, sample_rate=16000):
    """生成啁啾信号（变化的频率）"""
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    # 线性变化的频率
    freq = start_freq + (end_freq - start_freq) * t / duration
    wave = np.sin(2 * np.pi * freq * t)
    wave_int16 = (wave * 32767 * 0.2).astype(np.int16)  # 20%音量
    return wave_int16.tobytes()

def generate_noise(duration=0.025, sample_rate=16000):
    """生成白噪声（模拟背景音）"""
    t = int(sample_rate * duration)
    noise = np.random.normal(0, 0.1, t)  # 小幅度噪声
    wave_int16 = (noise * 32767).astype(np.int16)
    return wave_int16.tobytes()

class AudioTestCallback(OmniRealtimeCallback):
    def __init__(self):
        super().__init__()
        self.events = []
        self.start_time = time.time()
        
    def on_event(self, response):
        event_type = response.get('type')
        elapsed = time.time() - self.start_time
        self.events.append((event_type, elapsed))
        
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

def test_with_sine_wave():
    """测试发送正弦波音频"""
    print("=== 测试发送正弦波音频 ===")
    
    dashscope.api_key = API_KEY
    callback = AudioTestCallback()
    
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
        instructions="请说'你好，测试成功'。",
        enable_turn_detection=True
    )
    time.sleep(3)
    
    print("3. 发送正弦波音频（440Hz，1秒）...")
    start_time = time.time()
    audio_count = 0
    
    while time.time() - start_time < 1.0:
        audio_data = generate_sine_wave(freq=440, duration=0.025)
        audio_b64 = base64.b64encode(audio_data).decode('utf-8')
        conversation.append_audio(audio_b64)
        audio_count += 1
        time.sleep(0.025)
    
    print(f"✅ 发送完成，共{audio_count}帧正弦波音频")
    
    print("4. 等待响应（10秒）...")
    time.sleep(10)
    
    print("5. 检查结果...")
    has_response = any('response.created' in e[0] for e in callback.events)
    
    conversation.close()
    return has_response

def test_with_chirp():
    """测试发送啁啾信号（变化的频率）"""
    print("\n=== 测试发送啁啾信号 ===")
    
    dashscope.api_key = API_KEY
    callback = AudioTestCallback()
    
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
        instructions="请说'测试成功'。",
        enable_turn_detection=True
    )
    time.sleep(3)
    
    print("3. 发送啁啾信号（200-800Hz，2秒）...")
    start_time = time.time()
    audio_count = 0
    
    while time.time() - start_time < 2.0:
        audio_data = generate_chirp(start_freq=200, end_freq=800, duration=0.025)
        audio_b64 = base64.b64encode(audio_data).decode('utf-8')
        conversation.append_audio(audio_b64)
        audio_count += 1
        time.sleep(0.025)
    
    print(f"✅ 发送完成，共{audio_count}帧啁啾信号")
    
    print("4. 等待响应（10秒）...")
    time.sleep(10)
    
    print("5. 检查结果...")
    has_response = any('response.created' in e[0] for e in callback.events)
    
    conversation.close()
    return has_response

def test_mixed_signals():
    """测试混合信号（正弦波+噪声）"""
    print("\n=== 测试混合信号 ===")
    
    dashscope.api_key = API_KEY
    callback = AudioTestCallback()
    
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
        instructions="你好，请立即开始说话。",
        enable_turn_detection=True
    )
    time.sleep(3)
    
    print("3. 发送混合音频信号（3秒）...")
    start_time = time.time()
    audio_count = 0
    
    while time.time() - start_time < 3.0:
        # 交替发送正弦波和噪声
        if audio_count % 2 == 0:
            audio_data = generate_sine_wave(freq=300 + (audio_count % 5) * 100, duration=0.025)
        else:
            audio_data = generate_noise(duration=0.025)
        
        audio_b64 = base64.b64encode(audio_data).decode('utf-8')
        conversation.append_audio(audio_b64)
        audio_count += 1
        time.sleep(0.025)
    
    print(f"✅ 发送完成，共{audio_count}帧混合信号")
    
    print("4. 等待响应（10秒）...")
    time.sleep(10)
    
    print("5. 检查结果...")
    has_response = any('response.created' in e[0] for e in callback.events)
    
    conversation.close()
    return has_response

def test_silence_vs_real():
    """对比测试：静音 vs 真实音频"""
    print("\n=== 对比测试：静音 vs 真实音频 ===")
    
    dashscope.api_key = API_KEY
    
    # 测试1: 静音
    print("\n测试1: 发送静音")
    callback1 = AudioTestCallback()
    conv1 = OmniRealtimeConversation(
        model='qwen3.5-omni-plus-realtime',
        callback=callback1,
        url='wss://dashscope.aliyuncs.com/api-ws/v1/realtime'
    )
    
    conv1.connect()
    time.sleep(2)
    conv1.update_session(
        output_modalities=[MultiModality.AUDIO, MultiModality.TEXT],
        voice='Ethan',
        instructions="请说'测试'。",
        enable_turn_detection=True
    )
    time.sleep(2)
    
    # 发送静音
    for i in range(40):  # 1秒
        audio_data = b'\x00' * 800
        audio_b64 = base64.b64encode(audio_data).decode('utf-8')
        conv1.append_audio(audio_b64)
        time.sleep(0.025)
    
    time.sleep(5)
    conv1.close()
    
    has_silence_response = any('response.created' in e[0] for e in callback1.events)
    print(f"静音测试: {'✅ AI响应' if has_silence_response else '❌ 无响应'}")
    
    time.sleep(3)
    
    # 测试2: 真实音频
    print("\n测试2: 发送真实音频（正弦波）")
    callback2 = AudioTestCallback()
    conv2 = OmniRealtimeConversation(
        model='qwen3.5-omni-plus-realtime',
        callback=callback2,
        url='wss://dashscope.aliyuncs.com/api-ws/v1/realtime'
    )
    
    conv2.connect()
    time.sleep(2)
    conv2.update_session(
        output_modalities=[MultiModality.AUDIO, MultiModality.TEXT],
        voice='Ethan',
        instructions="请说'测试'。",
        enable_turn_detection=True
    )
    time.sleep(2)
    
    # 发送正弦波
    for i in range(40):  # 1秒
        audio_data = generate_sine_wave(freq=440, duration=0.025)
        audio_b64 = base64.b64encode(audio_data).decode('utf-8')
        conv2.append_audio(audio_b64)
        time.sleep(0.025)
    
    time.sleep(5)
    conv2.close()
    
    has_real_response = any('response.created' in e[0] for e in callback2.events)
    print(f"真实音频测试: {'✅ AI响应' if has_real_response else '❌ 无响应'}")
    
    return has_silence_response, has_real_response

def main():
    print("开始测试真实音频数据...")
    print(f"API密钥: {API_KEY[:10]}...{API_KEY[-10:]}")
    
    print("\n测试1: 正弦波音频")
    result1 = test_with_sine_wave()
    
    time.sleep(5)
    
    print("\n测试2: 啁啾信号")
    result2 = test_with_chirp()
    
    time.sleep(5)
    
    print("\n测试3: 混合信号")
    result3 = test_mixed_signals()
    
    time.sleep(5)
    
    print("\n测试4: 静音 vs 真实音频对比")
    silence_result, real_result = test_silence_vs_real()
    
    print(f"\n=== 最终结果 ===")
    print(f"正弦波测试: {'✅ AI响应' if result1 else '❌ 无响应'}")
    print(f"啁啾信号测试: {'✅ AI响应' if result2 else '❌ 无响应'}")
    print(f"混合信号测试: {'✅ AI响应' if result3 else '❌ 无响应'}")
    print(f"静音 vs 真实音频对比:")
    print(f"  静音: {'✅ AI响应' if silence_result else '❌ 无响应'}")
    print(f"  真实音频: {'✅ AI响应' if real_result else '❌ 无响应'}")
    
    if not any([result1, result2, result3, real_result]):
        print("\n⚠️ 所有音频测试都失败，但参考文件可以工作")
        print("可能的问题:")
        print("1. 指令设置问题（太复杂或冲突）")
        print("2. 需要发送视频帧才能触发响应")
        print("3. 音频数据格式不正确")
        print("4. 需要更长的音频输入")
    
    if real_result and not silence_result:
        print("\n✅ 发现关键问题：AI需要真实音频信号才能响应！")
        print("解决方案：发送非静音音频数据")

if __name__ == "__main__":
    main()