import dashscope
import logging
import sys

# 设置日志
logging.basicConfig(level=logging.DEBUG)

# 设置API密钥
API_KEY = "sk-206a776b2b1a4422bef8941e33e10cc5"
dashscope.api_key = API_KEY

print(f"API Key (前10位): {API_KEY[:10]}...")
print(f"DashScope version: {dashscope.__version__ if hasattr(dashscope, '__version__') else 'unknown'}")

# 尝试导入OmniRealtimeConversation
try:
    from dashscope.audio.qwen_omni import OmniRealtimeConversation, OmniRealtimeCallback, MultiModality, AudioFormat
    print("✅ 成功导入DashScope模块")
    
    # 创建一个简单的回调类
    class TestCallback(OmniRealtimeCallback):
        def on_open(self):
            print("✅ WebSocket连接已建立")
        
        def on_event(self, event):
            print(f"收到事件: {event}")
        
        def on_close(self, close_status_code, close_msg):
            print(f"连接关闭: code={close_status_code}, msg={close_msg}")
        
        def on_error(self, error):
            print(f"错误: {error}")
    
    # 创建会话
    callback = TestCallback()
    
    # 尝试创建会话
    print("尝试创建OmniRealtimeConversation...")
    try:
        conversation = OmniRealtimeConversation(
            model="qwen3.5-omni-plus-realtime",
            callback=callback,
            url="wss://dashscope.aliyuncs.com/api-ws/v1/realtime"
        )
        print(f"✅ 会话创建成功: {conversation}")
        print(f"会话类型: {type(conversation)}")
        
        # 检查属性
        print(f"conversation.ws属性: {hasattr(conversation, 'ws')}")
        if hasattr(conversation, 'ws'):
            print(f"conversation.ws值: {conversation.ws}")
        
        # 尝试调用update_session
        print("尝试调用update_session...")
        try:
            conversation.update_session(
                output_modalities=[MultiModality.AUDIO, MultiModality.TEXT],
                voice="Ethan",
                instructions="Hello",
                enable_turn_detection=True,
                input_audio_format=AudioFormat.PCM_16000HZ_MONO_16BIT,
                output_audio_format=AudioFormat.PCM_16000HZ_MONO_16BIT,
                smooth_output=True,
                enable_input_audio_transcription=True,
                enable_output_audio_transcription=True
            )
            print("✅ update_session调用成功")
        except Exception as e:
            print(f"❌ update_session失败: {type(e).__name__}: {e}")
        
    except Exception as e:
        print(f"❌ 创建会话失败: {type(e).__name__}: {e}")
        
except ImportError as e:
    print(f"❌ 导入失败: {e}")
except Exception as e:
    print(f"❌ 其他错误: {type(e).__name__}: {e}")