#!/usr/bin/env python3
"""测试参考文件配置：使用enable_turn_detection=True"""
import os
import sys
import time
import json
import base64
import threading
import queue

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

class SimpleCallback(OmniRealtimeCallback):
    """简单回调，记录所有事件"""
    def __init__(self):
        super().__init__()
        self.events_received = []
        self.connected_event = threading.Event()
        self.response_received = threading.Event()
        self.last_audio = None
        self.last_text = None
        
    def on_open(self):
        print("📡 WebSocket连接已打开")
        self.connected_event.set()
        
    def on_event(self, response):
        event_type = response.get('type')
        self.events_received.append(event_type)
        
        print(f"📨 收到事件: {event_type}")
        
        if event_type == 'session.created':
            print(f"✅ 会话创建成功: {response['session']['id']}")
            
        elif event_type == 'conversation.item.input_audio_transcription.completed':
            user_text = response.get('transcript', '')
            print(f"🎤 用户语音转文字: {user_text}")
            
        elif event_type == 'response.created':
            print("🔊 AI开始生成响应")
            
        elif event_type == 'response.audio_transcript.delta':
            text_delta = response.get('delta', '')
            if self.last_text is None:
                self.last_text = text_delta
            else:
                self.last_text += text_delta
            print(f"💬 AI文本回复增量: {text_delta}")
            
        elif event_type == 'response.audio.delta':
            print(f"🔊 收到AI音频数据: {len(response['delta'])}字节")
            
        elif event_type == 'response.done':
            print("✅ AI响应完成")
            self.response_received.set()
            
        elif event_type == 'error':
            error_msg = response.get('message', '未知错误')
            print(f"❌ 错误: {error_msg}")
            
    def on_close(self, close_status_code, close_msg):
        print(f"🔌 连接关闭: code={close_status_code}, msg={close_msg}")

def test_reference_config():
    """测试参考文件配置"""
    print("\n=== 测试参考文件配置 (enable_turn_detection=True) ===")
    
    # 设置DashScope API密钥
    print(f"设置API密钥: {api_key[:10]}...")
    dashscope.api_key = api_key
    
    # 创建回调
    callback = SimpleCallback()
    
    try:
        # 创建会话 - 使用参考文件的配置
        print("创建OmniRealtimeConversation...")
        model = 'qwen3.5-omni-plus-realtime'
        url = 'wss://dashscope.aliyuncs.com/api-ws/v1/realtime'
        
        conversation = OmniRealtimeConversation(
            model=model,
            callback=callback,
            url=url
        )
        
        # 连接WebSocket
        print("连接WebSocket...")
        conversation.connect()
        
        # 等待连接建立
        if callback.connected_event.wait(timeout=10):
            print("✅ WebSocket连接成功")
        else:
            print("❌ WebSocket连接超时")
            return
        
        # 配置会话 - 使用参考文件的配置
        print("配置会话参数...")
        conversation.update_session(
            output_modalities=[MultiModality.AUDIO, MultiModality.TEXT],
            voice='zhitian_emo',  # 使用参考文件中的音色
            instructions="你是一位专业、友好、循循善诱的技术面试官，名字是'千小问'。当会话建立后，请立即开始说话，不需要等待任何用户输入。现在请立即开始你的自我介绍！",
            enable_turn_detection=True,  # 关键差异：使用VAD模式
            # 不设置音频格式参数（让API使用默认值）
            smooth_output=True,
            enable_input_audio_transcription=True,
            enable_output_audio_transcription=True
        )
        
        print("✅ 会话配置完成")
        
        # 等待3秒让会话建立
        print("等待3秒让会话稳定...")
        time.sleep(3)
        
        # 发送一个空音频帧（20ms静音）
        print("发送空音频帧...")
        empty_audio = b'\x00' * 320  # 20ms的静音帧（16kHz, 16-bit, mono）
        audio_base64 = base64.b64encode(empty_audio).decode('utf-8')
        conversation.append_audio(audio_base64)
        # 注意：参考文件没有调用commit()，我们也不调用
        
        print("等待AI回复...（等待15秒）")
        start_time = time.time()
        while time.time() - start_time < 15:
            if callback.response_received.is_set():
                print("✅ AI已回复")
                break
            time.sleep(0.5)
        
        if not callback.response_received.is_set():
            print("❌ AI没有回复")
        
        print(f"\n=== 收到的事件列表 ===")
        for i, event in enumerate(callback.events_received):
            print(f"{i+1}. {event}")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        print("\n关闭连接...")
        try:
            conversation.close()
        except:
            pass
        print("✅ 测试完成")

if __name__ == "__main__":
    test_reference_config()