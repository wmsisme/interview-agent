#!/usr/bin/env python3
"""
测试如何触发AI面试官开始说话
"""
import os
import sys
import json
import time
import threading
import logging

# 添加项目路径
sys.path.append('.')

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 检查DashScope API密钥
api_key = os.getenv('VIDEO_CHAT_API_KEY') or os.getenv('DASHSCOPE_API_KEY')
if not api_key:
    print("错误: 请设置VIDEO_CHAT_API_KEY或DASHSCOPE_API_KEY环境变量")
    sys.exit(1)

try:
    import dashscope
    from dashscope.audio.qwen_omni import OmniRealtimeConversation, OmniRealtimeCallback, MultiModality, AudioFormat
    from app.services.video_chat_service import VideoChatCallback
    
    print("✅ 导入依赖成功")
except ImportError as e:
    print(f"❌ 导入依赖失败: {e}")
    sys.exit(1)

class TestTriggerCallback(VideoChatCallback):
    def __init__(self):
        self.session_id = 'test_trigger'
        self.websocket_handler = None
        self.connected_event = threading.Event()
        self.on_audio_callback = lambda x: print(f"🎵 收到音频数据: {len(x)} 字节")
        self.on_text_callback = lambda x: print(f"📝 收到文本: {x}")
        self.on_done_callback = lambda: print("✅ 响应完成")
        self.on_error_callback = lambda e: print(f"❌ 错误: {e}")
        self.on_interview_event_callback = lambda t, d: print(f"🔔 事件: {t}, 数据: {d}")
        
        # 记录所有事件
        self.all_events = []
        
    def on_open(self):
        print("✅ WebSocket连接已建立")
        self.connected_event.set()
        
    def on_event(self, event: dict):
        """记录所有事件"""
        event_type = event.get('type', 'unknown')
        print(f"📨 收到事件: {event_type}")
        self.all_events.append(event)
        
        # 调用父类处理
        super().on_event(event)
        
    def on_close(self, close_status_code: int, close_msg: str):
        print(f"🔌 连接关闭: code={close_status_code}, msg={close_msg}")
        
    def on_error(self, error):
        print(f"❌ WebSocket错误: {error}")

def test_ai_start():
    """测试AI如何开始说话"""
    print("\n=== 测试AI触发机制 ===")
    
    # 设置DashScope API密钥
    print(f"设置API密钥: {api_key[:10]}...")
    dashscope.api_key = api_key
    
    # 创建回调
    callback = TestTriggerCallback()
    
    try:
        # 创建会话
        print("创建OmniRealtimeConversation...")
        # 使用默认配置
        model = 'qwen3.5-omni-plus-realtime'
        url = 'wss://dashscope.aliyuncs.com/api-ws/v1/realtime'
        
        conversation = OmniRealtimeConversation(
            model=model,
            callback=callback,
            url=url
        )
        
        # 调试：查看conversation的方法
        print(f"\nOmniRealtimeConversation方法列表:")
        methods = [m for m in dir(conversation) if not m.startswith('_')]
        for method in methods:
            print(f"  - {method}")
        
        # 连接WebSocket
        print("连接WebSocket...")
        conversation.connect()
        
        # 等待连接建立
        if callback.connected_event.wait(timeout=10):
            print("✅ WebSocket连接成功")
        else:
            print("❌ 连接超时")
            return
            
        # 配置会话
        print("\n配置会话参数...")
        instructions = """你是一位专业的技术面试官，名字是"千小问"。
你需要通过提问来评估候选人的技术能力和综合素质。

重要指令：当会话建立后，请立即开始说话，不需要等待任何用户输入。

面试流程：
1. 【立即开始】会话建立后，立即进行简短的自我介绍（20-30秒），说明你是面试官和本次面试的目的。
2. 【询问准备】自我介绍后，立即询问候选人是否准备好了。
3. 【开始提问】如果候选人表示准备好了或保持沉默，立即开始第一个技术问题。
4. 【面试过程】根据岗位要求提出有针对性的技术问题，问题应由浅入深。
5. 【结束面试】面试结束时，对候选人的表现给予简短鼓励，并告知后续流程。

对话要求：
- 始终保持口语化的中文，使用亲切自然的语气
- 每个问题要简洁明了，不要长篇大论
- 认真倾听候选人的回答，根据回答质量决定是否追问
- 控制对话节奏，确保面试流畅进行

现在请立即开始你的自我介绍！"""
        
        conversation.update_session(
            output_modalities=[MultiModality.AUDIO, MultiModality.TEXT],
            voice='zhiyuan',
            instructions=instructions,
            enable_turn_detection=False,  # 关闭回合检测，让AI主动说话
            input_audio_format=AudioFormat.PCM_16000HZ_MONO_16BIT,
            output_audio_format=AudioFormat.PCM_16000HZ_MONO_16BIT,
            smooth_output=True,
            enable_input_audio_transcription=True,
            enable_output_audio_transcription=True
        )
        
        print("✅ 会话配置完成")
        
        # 立即发送一个空音频帧来触发AI响应
        print("发送初始静音帧触发AI...")
        empty_audio = b'\x00' * 320  # 20ms的静音帧（16kHz, 16-bit, mono）
        # 将音频数据编码为base64
        import base64
        audio_base64 = base64.b64encode(empty_audio).decode('utf-8')
        conversation.append_audio(audio_base64)
        conversation.commit()  # 提交音频数据
        
        print("等待AI回复...（等待15秒）")
        time.sleep(15)
            
        # 输出所有收到的事件
        print(f"\n=== 收到的事件总结 ===")
        print(f"总共收到 {len(callback.all_events)} 个事件")
        for i, event in enumerate(callback.all_events):
            event_type = event.get('type', 'unknown')
            print(f"{i+1}. {event_type}")
            if event_type in ['response.text.delta', 'response.audio_transcript.delta']:
                print(f"   内容: {event.get('delta', '')[:50]}...")
                
        # 关闭连接
        print("\n关闭连接...")
        conversation.close()
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_ai_start()