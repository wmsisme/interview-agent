#!/usr/bin/env python3
"""最终配置测试：使用正确参数"""
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
api_key = os.environ.get('VIDEO_CHAT_API_KEY', 'sk-206a776b2b1a4422bef8941e33e10cc5')

def create_test_image(width=640, height=480):
    """创建测试图像"""
    image = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(image)
    draw.rectangle([50, 50, 150, 150], fill='red', outline='black')
    draw.text((100, 200), "Test Image", fill='black')
    
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format='JPEG', quality=85)
    return img_byte_arr.getvalue()

def generate_sine_wave(freq=440, duration=0.025, sample_rate=16000):
    """生成正弦波音频（替代静音）"""
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    wave = np.sin(2 * np.pi * freq * t)
    # 转换为16位PCM
    wave_int16 = (wave * 32767).astype(np.int16)
    return wave_int16.tobytes()

class FinalCallback(OmniRealtimeCallback):
    """最终回调"""
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
            full_text = response.get('transcript', '')
            print(f"\n✅ AI完整文本: {full_text}")
            
        elif event_type == 'response.audio.delta':
            print("🔊", end='', flush=True)
            
        elif event_type == 'response.done':
            print("\n✅ AI响应完成")
            
        elif event_type == 'error':
            error_msg = response.get('message', '未知错误')
            print(f"\n❌ 错误: {error_msg}")
            print(f"   完整响应: {response}")

def test_final_config():
    """测试最终配置"""
    print("\n=== 测试最终配置 ===")
    
    dashscope.api_key = api_key
    callback = FinalCallback()
    
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
        
        # 配置会话 - 使用项目配置，但禁用VAD
        instructions = """你是一位面试官。当会话建立后，请立即开始说话。现在请立即开始你的自我介绍！"""
        
        conversation.update_session(
            output_modalities=[MultiModality.AUDIO, MultiModality.TEXT],
            voice='Ethan',
            instructions=instructions,
            enable_turn_detection=False,  # 禁用VAD，希望AI主动开始
            input_audio_format=AudioFormat.PCM_16000HZ_MONO_16BIT,
            output_audio_format=AudioFormat.PCM_16000HZ_MONO_16BIT,
            smooth_output=True,
            enable_input_audio_transcription=True,
            enable_output_audio_transcription=True
        )
        
        print("✅ 会话配置完成")
        time.sleep(2)
        
        # 发送初始数据
        print("📤 发送初始数据...")
        
        # 1. 发送视频帧
        image_data = create_test_image()
        image_b64 = base64.b64encode(image_data).decode('utf-8')
        conversation.append_video(image_b64)
        print(f"📹 视频帧: {len(image_data)}字节")
        
        # 2. 发送音频帧（使用正确大小：800字节 = 25ms @ 16kHz）
        # 生成正弦波（非静音）
        audio_data = generate_sine_wave(freq=440, duration=0.025, sample_rate=16000)  # 25ms
        # 验证大小：16kHz * 2 bytes * 0.025s = 800字节
        print(f"🎤 音频帧: {len(audio_data)}字节 (期望: 800)")
        audio_b64 = base64.b64encode(audio_data).decode('utf-8')
        conversation.append_audio(audio_b64)
        
        # 持续发送数据（模拟前端）
        print("🔄 持续发送数据（8秒）...")
        start_time = time.time()
        frame_count = 0
        
        while time.time() - start_time < 8:
            time.sleep(0.1)  # 100ms间隔
            
            # 每400ms发送视频帧（2.5 FPS）
            if frame_count % 4 == 0:
                image_data = create_test_image()
                image_b64 = base64.b64encode(image_data).decode('utf-8')
                conversation.append_video(image_b64)
            
            # 持续发送音频（每100ms发送4个25ms帧）
            audio_data = generate_sine_wave(freq=440, duration=0.025, sample_rate=16000)
            audio_b64 = base64.b64encode(audio_data).decode('utf-8')
            conversation.append_audio(audio_b64)
            
            frame_count += 1
            if frame_count % 20 == 0:
                print(".", end='', flush=True)
        
        print(f"\n✅ 发送完成，共{frame_count}帧")
        
        # 等待AI回复
        print("⏳ 等待AI回复（12秒）...")
        wait_start = time.time()
        ai_started = False
        
        while time.time() - wait_start < 12:
            if any(event[0] == 'response.created' for event in callback.events):
                ai_started = True
                print("\n✅ AI已开始回复")
                break
            time.sleep(0.5)
        
        if not ai_started:
            print("\n❌ AI没有回复")
            
            # 检查是否有错误
            errors = [e for e in callback.events if e[0] == 'error']
            if errors:
                print(f"发现{len(errors)}个错误事件")
        
        # 打印事件总结
        print(f"\n=== 事件总结 ===")
        print(f"总事件数: {len(callback.events)}")
        
        event_types = {}
        for event_type, _ in callback.events:
            event_types[event_type] = event_types.get(event_type, 0) + 1
        
        for event_type, count in event_types.items():
            print(f"  {event_type}: {count}")
        
        if callback.ai_text:
            print(f"\nAI回复内容: {callback.ai_text}")
        
        conversation.close()
        return ai_started
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_reference_mode():
    """测试参考文件模式（响应式）"""
    print("\n=== 测试参考文件模式（响应式） ===")
    
    dashscope.api_key = api_key
    callback = FinalCallback()
    
    try:
        conversation = OmniRealtimeConversation(
            model='qwen3.5-omni-plus-realtime',
            callback=callback,
            url='wss://dashscope.aliyuncs.com/api-ws/v1/realtime'
        )
        
        conversation.connect()
        print("✅ 连接成功")
        time.sleep(1)
        
        # 参考文件配置
        conversation.update_session(
            output_modalities=[MultiModality.AUDIO, MultiModality.TEXT],
            voice='Ethan',
            instructions="你是一个视觉AI助手，可以实时看到摄像头画面。请根据你看到的视频内容回答用户的问题。",
            enable_turn_detection=True  # 使用VAD模式
        )
        
        print("✅ 参考文件配置完成")
        
        # 发送一些数据
        print("📤 发送视频和音频...")
        for i in range(10):
            time.sleep(0.5)
            
            # 发送视频帧
            image_data = create_test_image()
            image_b64 = base64.b64encode(image_data).decode('utf-8')
            conversation.append_video(image_b64)
            
            # 发送音频（静音）
            audio_data = b'\x00' * 800  # 25ms静音
            audio_b64 = base64.b64encode(audio_data).decode('utf-8')
            conversation.append_audio(audio_b64)
            
            print(f"帧 {i+1}", end=' ', flush=True)
        
        print("\n✅ 数据发送完成")
        
        # 等待回复
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
        
        conversation.close()
        return ai_started
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

def main():
    """运行测试"""
    print("=== 最终测试 ===")
    
    print("\n1. 测试主动开始模式（禁用VAD）")
    result1 = test_final_config()
    
    time.sleep(3)
    
    print("\n2. 测试响应式模式（启用VAD，参考文件模式）")
    result2 = test_reference_mode()
    
    print(f"\n=== 最终结果 ===")
    print(f"主动开始模式: {'✅ 成功' if result1 else '❌ 失败'}")
    print(f"响应式模式: {'✅ 成功' if result2 else '❌ 失败'}")
    
    if not result1 and not result2:
        print("\n⚠️ 两个测试都失败，可能是API密钥或服务问题")
        print(f"API密钥: {api_key[:10]}...")
        print("建议：")
        print("1. 检查API密钥是否有效")
        print("2. 检查网络连接")
        print("3. 尝试使用不同的模型或区域")

if __name__ == "__main__":
    main()