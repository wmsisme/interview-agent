#!/usr/bin/env python3
"""分析参考文件的音频发送机制"""
import os
import sys
import time
import base64
import numpy as np

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

class AnalyzeCallback(OmniRealtimeCallback):
    """分析回调"""
    def __init__(self):
        super().__init__()
        self.audio_count = 0
        self.video_count = 0
        self.sequence = []
        self.start_time = time.time()
        
    def on_open(self):
        print("📡 WebSocket连接已打开")
        self.start_time = time.time()
        
    def on_event(self, response):
        event_type = response.get('type')
        current_time = time.time() - self.start_time
        
        if event_type == 'response.created':
            print(f"\n🕒 {current_time:.2f}s: AI开始生成响应")
            
        elif event_type == 'response.audio_transcript.delta':
            text = response.get('delta', '')
            print(f"💬 {text}", end='', flush=True)
            
        elif event_type == 'response.audio_transcript.done':
            print(f"\n✅ AI完整转写完成")
            
        elif event_type == 'response.done':
            print(f"\n✅ AI响应完成")
            
        elif event_type == 'error':
            error_msg = response.get('message', '未知错误')
            print(f"\n❌ 错误: {error_msg}")

def analyze_audio_sending():
    """分析音频发送机制"""
    print("\n=== 分析音频发送机制 ===")
    
    dashscope.api_key = api_key
    callback = AnalyzeCallback()
    
    try:
        # 创建会话
        conversation = OmniRealtimeConversation(
            model='qwen3.5-omni-plus-realtime',
            callback=callback,
            url='wss://dashscope.aliyuncs.com/api-ws/v1/realtime'
        )
        
        # 连接
        conversation.connect()
        print("✅ 连接成功")
        time.sleep(1)
        
        # 使用与参考文件相同的配置
        conversation.update_session(
            output_modalities=[MultiModality.AUDIO, MultiModality.TEXT],
            voice='Ethan',
            instructions="你是一个测试助手。请立即开始说话，从1数到3。",
            enable_turn_detection=True  # VAD模式
            # 注意：没有设置音频格式参数
        )
        
        print("✅ 会话配置完成")
        time.sleep(2)
        
        # 测试不同的音频帧大小
        frame_sizes = [320, 400, 800, 1600]  # 20ms, 25ms, 50ms, 100ms
        sample_rate = 16000
        
        for i, frame_bytes in enumerate(frame_sizes):
            print(f"\n🔬 测试帧大小: {frame_bytes}字节 ({frame_bytes/2/sample_rate*1000:.1f}ms)")
            
            # 生成正弦波
            duration = frame_bytes / 2 / sample_rate  # 16位，2字节/样本
            t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
            wave = np.sin(2 * np.pi * 440 * t)
            wave_int16 = (wave * 32767).astype(np.int16)
            audio_data = wave_int16.tobytes()
            
            print(f"  理论时长: {duration*1000:.1f}ms")
            print(f"  实际字节: {len(audio_data)}")
            
            # 发送音频
            audio_b64 = base64.b64encode(audio_data).decode('utf-8')
            conversation.append_audio(audio_b64)
            print(f"  ✅ 发送音频")
            
            time.sleep(1)
            
            # 发送视频帧（在音频之后）
            test_image = b'test' * 100  # 简单测试图像
            image_b64 = base64.b64encode(test_image).decode('utf-8')
            conversation.append_video(image_b64)
            print(f"  ✅ 发送视频（音频后）")
            
            # 等待响应
            print(f"  等待响应3秒...")
            time.sleep(3)
            
            # 检查是否收到响应
            # 在callback中检查
        
        print("\n=== 发送连续音频 ===")
        # 测试连续发送（模拟参考文件）
        print("连续发送音频（5秒）...")
        start_time = time.time()
        sent_frames = 0
        
        while time.time() - start_time < 5:
            # 使用800字节（25ms）帧
            audio_data = b'\x00' * 800
            audio_b64 = base64.b64encode(audio_data).decode('utf-8')
            conversation.append_audio(audio_b64)
            
            sent_frames += 1
            
            # 每200ms发送一次视频
            if sent_frames % 8 == 0:  # 8*25ms = 200ms
                test_image = b'test' * 100
                image_b64 = base64.b64encode(test_image).decode('utf-8')
                conversation.append_video(image_b64)
            
            time.sleep(0.025)  # 25ms
        
        print(f"✅ 发送完成，共{sent_frames}音频帧")
        
        # 额外等待
        print("等待AI响应（5秒）...")
        time.sleep(5)
        
        conversation.close()
        
    except Exception as e:
        print(f"❌ 分析失败: {e}")
        import traceback
        traceback.print_exc()

def test_commit_required():
    """测试是否需要调用commit()"""
    print("\n=== 测试commit()方法 ===")
    
    dashscope.api_key = api_key
    callback = AnalyzeCallback()
    
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
            instructions="请说'测试'。",
            enable_turn_detection=False
        )
        
        time.sleep(2)
        
        # 测试1：只append_audio，不commit
        print("测试1: 只append_audio，不commit")
        audio_data = b'\x00' * 800
        audio_b64 = base64.b64encode(audio_data).decode('utf-8')
        conversation.append_audio(audio_b64)
        print("✅ append_audio完成")
        
        time.sleep(3)
        
        # 测试2：append_audio后立即commit
        print("\n测试2: append_audio后立即commit")
        conversation.append_audio(audio_b64)
        conversation.commit()
        print("✅ append_audio + commit完成")
        
        time.sleep(3)
        
        # 测试3：append_video后commit
        print("\n测试3: append_video后commit")
        test_image = b'test' * 100
        image_b64 = base64.b64encode(test_image).decode('utf-8')
        conversation.append_video(image_b64)
        conversation.commit()
        print("✅ append_video + commit完成")
        
        time.sleep(3)
        
        conversation.close()
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")

def main():
    """主函数"""
    print("=== 分析参考文件机制 ===")
    
    # 分析音频发送
    analyze_audio_sending()
    
    time.sleep(2)
    
    # 测试commit方法
    test_commit_required()
    
    print("\n=== 总结 ===")
    print("参考文件的关键特征:")
    print("1. 使用VAD模式 (enable_turn_detection=True)")
    print("2. 先发送音频，后发送视频")
    print("3. 音频帧大小可能是800字节（25ms）")
    print("4. 持续发送音频数据，而不是一次性发送")
    print("5. 参考文件没有设置音频格式参数")

if __name__ == "__main__":
    main()