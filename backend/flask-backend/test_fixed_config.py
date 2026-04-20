#!/usr/bin/env python3
"""测试修复后的配置"""
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

class TestCallback(OmniRealtimeCallback):
    """测试回调"""
    def __init__(self):
        super().__init__()
        self.events = []
        self.ai_text = ""
        self.ai_started = False
        
    def on_open(self):
        self.events.append(('open', time.time()))
        print("📡 WebSocket连接已打开")
        
    def on_event(self, response):
        event_type = response.get('type')
        current_time = time.time()
        self.events.append((event_type, current_time, response))
        
        if event_type == 'response.created':
            print("🔊 AI开始生成响应")
            self.ai_started = True
            
        elif event_type == 'response.audio_transcript.delta':
            text = response.get('delta', '')
            self.ai_text += text
            print(f"💬 {text}", end='', flush=True)
            
        elif event_type == 'response.audio_transcript.done':
            full_text = response.get('transcript', '')
            print(f"\n✅ AI完整文本: {full_text}")
            
        elif event_type == 'response.done':
            print("\n✅ AI响应完成")
            
        elif event_type == 'error':
            error_msg = response.get('message', '未知错误')
            print(f"\n❌ 错误: {error_msg}")
            print(f"   完整响应: {response}")

def test_fixed_config():
    """测试修复后的配置"""
    print("\n=== 测试修复后的配置 ===")
    
    dashscope.api_key = api_key
    callback = TestCallback()
    
    try:
        # 创建会话 - 使用与项目相同的配置
        conversation = OmniRealtimeConversation(
            model='qwen3.5-omni-plus-realtime',
            callback=callback,
            url='wss://dashscope.aliyuncs.com/api-ws/v1/realtime'
        )
        
        # 连接
        conversation.connect()
        print("✅ 连接成功")
        time.sleep(1)
        
        # 配置会话 - 使用项目修复后的配置
        instructions = """你是一位面试官。当会话建立后，请立即开始说话。现在请立即开始你的自我介绍！"""
        
        conversation.update_session(
            output_modalities=[MultiModality.AUDIO, MultiModality.TEXT],
            voice='Ethan',
            instructions=instructions,
            enable_turn_detection=True,  # 使用VAD模式
            input_audio_format=AudioFormat.PCM_16000HZ_MONO_16BIT,
            output_audio_format=AudioFormat.PCM_16000HZ_MONO_16BIT,
            smooth_output=True,
            enable_input_audio_transcription=True,
            enable_output_audio_transcription=True
        )
        
        print("✅ 会话配置完成")
        time.sleep(2)
        
        # 关键修复：先发送音频帧（800字节 = 25ms）
        print("📤 1. 先发送音频帧（800字节）...")
        audio_data = b'\x00' * 800  # 25ms静音
        audio_b64 = base64.b64encode(audio_data).decode('utf-8')
        conversation.append_audio(audio_b64)
        print(f"   ✅ 发送音频: {len(audio_data)}字节")
        
        time.sleep(0.1)  # 短暂等待
        
        # 然后发送视频帧
        print("📤 2. 再发送视频帧...")
        image = Image.new('RGB', (640, 480), color='white')
        draw = ImageDraw.Draw(image)
        draw.rectangle([50, 50, 150, 150], fill='red', outline='black')
        
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format='JPEG', quality=85)
        image_data = img_byte_arr.getvalue()
        image_b64 = base64.b64encode(image_data).decode('utf-8')
        conversation.append_video(image_b64)
        print(f"   ✅ 发送视频: {len(image_data)}字节")
        
        # 持续发送数据（模拟前端）
        print("📤 3. 持续发送数据（6秒）...")
        start_time = time.time()
        frame_count = 0
        
        while time.time() - start_time < 6:
            # 每100ms发送一次音频
            time.sleep(0.1)
            
            # 发送音频（800字节）
            audio_data = b'\x00' * 800
            audio_b64 = base64.b64encode(audio_data).decode('utf-8')
            conversation.append_audio(audio_b64)
            
            # 每500ms发送一次视频（2 FPS）
            if frame_count % 5 == 0:
                image = Image.new('RGB', (640, 480), color='white')
                draw = ImageDraw.Draw(image)
                draw.text((100, 200), f"Frame {frame_count}", fill='black')
                
                img_byte_arr = io.BytesIO()
                image.save(img_byte_arr, format='JPEG', quality=85)
                image_data = img_byte_arr.getvalue()
                image_b64 = base64.b64encode(image_data).decode('utf-8')
                conversation.append_video(image_b64)
            
            frame_count += 1
            if frame_count % 10 == 0:
                print(".", end='', flush=True)
        
        print(f"\n✅ 发送完成，共{frame_count}次发送")
        
        # 等待AI回复
        print("⏳ 等待AI回复（12秒）...")
        wait_start = time.time()
        
        while time.time() - wait_start < 12:
            if callback.ai_started:
                print("\n✅ AI已开始回复")
                break
            time.sleep(0.5)
        
        if not callback.ai_started:
            print("\n❌ AI没有回复")
            
            # 分析事件
            print(f"\n📊 事件分析:")
            event_types = {}
            for event_type, timestamp, response in callback.events:
                event_types[event_type] = event_types.get(event_type, 0) + 1
            
            for event_type, count in event_types.items():
                print(f"  {event_type}: {count}")
                
                if event_type == 'error':
                    # 打印错误详情
                    for _, _, resp in callback.events:
                        if resp.get('type') == 'error':
                            print(f"    错误详情: {resp.get('error', {})}")
        
        # 打印AI回复的内容
        if callback.ai_text:
            print(f"\n📝 AI回复内容: {callback.ai_text}")
        
        conversation.close()
        return callback.ai_started
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_project_video_chat_service():
    """测试项目中的VideoChatService"""
    print("\n=== 测试项目VideoChatService ===")
    
    try:
        # 导入项目模块
        from app.services.video_chat_service import VideoChatService, VideoChatCallback
        
        class TestVideoCallback(VideoChatCallback):
            def __init__(self):
                super().__init__()
                self.events = []
                
            def on_audio(self, audio_data: bytes):
                pass
                
            def on_text(self, text: str):
                print(f"📝 AI文本: {text}")
                
            def on_connected(self):
                print("✅ WebSocket连接已建立")
                
            def on_closed(self):
                print("🔌 连接已关闭")
                
            def on_error(self, error: str):
                print(f"❌ 错误: {error}")
        
        callback = TestVideoCallback()
        service = VideoChatService(
            session_id="test_session_123",
            position="软件工程师",
            job_description="负责后端开发",
            user_id="test_user"
        )
        
        print("🚀 创建VideoChatService...")
        
        # 创建会话
        conversation = service.create_conversation(callback)
        print("✅ 会话创建成功")
        
        # 配置面试官
        service.configure_interviewer()
        print("✅ 面试官配置成功")
        
        # 测试发送音频
        print("📤 测试发送音频...")
        audio_data = b'\x00' * 800  # 25ms静音
        service.send_audio(audio_data)
        print("✅ 音频发送成功")
        
        # 测试发送视频
        print("📤 测试发送视频...")
        image = Image.new('RGB', (640, 480), color='white')
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format='JPEG', quality=85)
        image_data = img_byte_arr.getvalue()
        image_b64 = base64.b64encode(image_data).decode('utf-8')
        service.send_image(image_b64)
        print("✅ 视频发送成功")
        
        # 等待一段时间
        print("⏳ 等待5秒...")
        time.sleep(5)
        
        print("✅ VideoChatService测试完成")
        return True
        
    except Exception as e:
        print(f"❌ VideoChatService测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    print("=== 测试修复后的配置 ===")
    
    print("\n1. 测试直接API调用")
    result1 = test_fixed_config()
    
    time.sleep(3)
    
    print("\n2. 测试项目VideoChatService")
    result2 = test_project_video_chat_service()
    
    print(f"\n=== 测试结果 ===")
    print(f"直接API调用: {'✅ 成功' if result1 else '❌ 失败'}")
    print(f"项目VideoChatService: {'✅ 成功' if result2 else '❌ 失败'}")
    
    if result1:
        print("\n🎉 修复成功！AI现在应该可以正常回复了。")
    else:
        print("\n⚠️ 修复可能不完全成功，需要进一步调试。")

if __name__ == "__main__":
    main()