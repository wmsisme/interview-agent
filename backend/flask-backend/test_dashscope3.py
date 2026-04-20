import dashscope
from dashscope.audio.qwen_omni import OmniRealtimeConversation, OmniRealtimeCallback, MultiModality, AudioFormat
import time
import threading

# 设置API密钥
dashscope.api_key = "sk-206a776b2b1a4422bef8941e33e10cc5"

class TestCallback(OmniRealtimeCallback):
    def __init__(self):
        super().__init__()
        self.connected = threading.Event()
    
    def on_open(self):
        print("✅ WebSocket连接已建立")
        self.connected.set()
    
    def on_event(self, event):
        print(f"收到事件: {event}")
    
    def on_close(self, close_status_code, close_msg):
        print(f"连接关闭: code={close_status_code}, msg={close_msg}")
    
    def on_error(self, error):
        print(f"错误: {error}")

print("=== 测试连接流程 ===")
callback = TestCallback()
conversation = OmniRealtimeConversation(
    model="qwen3.5-omni-plus-realtime",
    callback=callback,
    url="wss://dashscope.aliyuncs.com/api-ws/v1/realtime"
)

print(f"1. 会话创建成功: {conversation}")
print(f"2. ws状态: {conversation.ws}")

print("3. 调用connect()...")
try:
    conversation.connect()
    print("✅ connect()调用成功")
    
    # 等待连接建立（最多5秒）
    print("等待连接建立...")
    if callback.connected.wait(timeout=5):
        print("✅ 连接已建立")
        print(f"ws状态: {conversation.ws}")
        
        # 现在尝试update_session
        print("4. 调用update_session...")
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
            
            # 等待一下再关闭
            time.sleep(2)
            
        except Exception as e:
            print(f"❌ update_session失败: {type(e).__name__}: {e}")
    else:
        print("❌ 连接未在5秒内建立")
        
except Exception as e:
    print(f"❌ connect()失败: {type(e).__name__}: {e}")

print("5. 关闭连接...")
try:
    conversation.close()
    print("✅ 连接已关闭")
except Exception as e:
    print(f"❌ 关闭失败: {e}")