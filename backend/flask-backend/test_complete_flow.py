#!/usr/bin/env python3
"""完整流程测试：模拟前端视频面试流程"""
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
api_key = os.environ.get('VIDEO_CHAT_API_KEY', 'REMOVED_API_KEY')

class CompleteCallback(OmniRealtimeCallback):
    """完整回调，模拟前端流程"""
    def __init__(self):
        super().__init__()
        self.events_received = []
        self.connected_event = threading.Event()
        self.response_received = threading.Event()
        self.ai_text = ""
        self.audio_received = False
        self.text_received = False
        
    def on_open(self):
        print("📡 WebSocket连接已打开")
        self.connected_event.set()
        
    def on_event(self, response):
        event_type = response.get('type')
        self.events_received.append((event_type, time.time()))
        
        print(f"📨 {event_type}")
        
        if event_type == 'session.created':
            print(f"✅ 会话创建成功: {response['session']['id']}")
            
        elif event_type == 'conversation.item.input_audio_transcription.completed':
            user_text = response.get('transcript', '')
            print(f"🎤 用户语音转文字: {user_text}")
            
        elif event_type == 'response.created':
            print("🔊 AI开始生成响应")
            
        elif event_type == 'response.audio_transcript.delta':
            text_delta = response.get('delta', '')
            self.ai_text += text_delta
            self.text_received = True
            print(f"💬 AI文本: {text_delta}", end='')
            
        elif event_type == 'response.audio_transcript.done':
            full_text = response.get('transcript', '')
            print(f"\n✅ AI完整文本: {full_text}")
            
        elif event_type == 'response.audio.delta':
            self.audio_received = True
            print(f"🔊 收到AI音频数据")
            
        elif event_type == 'response.done':
            print("✅ AI响应完成")
            self.response_received.set()
            
        elif event_type == 'error':
            error_msg = response.get('message', '未知错误')
            print(f"❌ 错误: {error_msg}")
            
    def on_close(self, close_status_code, close_msg):
        print(f"🔌 连接关闭: code={close_status_code}, msg={close_msg}")
        
    def on_error(self, error):
        print(f"❌ 连接错误: {error}")

def test_complete_flow():
    """测试完整流程"""
    print("\n=== 完整视频面试流程测试 ===")
    
    # 设置DashScope API密钥
    print(f"设置API密钥: {api_key[:10]}...")
    dashscope.api_key = api_key
    
    # 创建回调
    callback = CompleteCallback()
    
    try:
        # 1. 创建会话
        print("\n1. 创建OmniRealtimeConversation...")
        model = 'qwen3.5-omni-plus-realtime'
        url = 'wss://dashscope.aliyuncs.com/api-ws/v1/realtime'
        
        conversation = OmniRealtimeConversation(
            model=model,
            callback=callback,
            url=url
        )
        
        # 2. 连接WebSocket
        print("2. 连接WebSocket...")
        conversation.connect()
        
        # 等待连接建立
        if callback.connected_event.wait(timeout=10):
            print("✅ WebSocket连接成功")
        else:
            print("❌ WebSocket连接超时")
            return
        
        # 3. 配置会话（使用项目的实际配置）
        print("\n3. 配置会话参数...")
        instructions = """你是一位专业、友好、循循善诱的技术面试官，名字是"千小问"。
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
            voice='zhitian_emo',
            instructions=instructions,
            enable_turn_detection=True,  # 使用VAD模式
            input_audio_format=AudioFormat.PCM_16000HZ_MONO_16BIT,
            output_audio_format=AudioFormat.PCM_16000HZ_MONO_16BIT,
            smooth_output=True,
            enable_input_audio_transcription=True,
            enable_output_audio_transcription=True
        )
        
        print("✅ 会话配置完成")
        
        # 4. 等待会话建立
        print("\n4. 等待会话稳定（3秒）...")
        time.sleep(3)
        
        # 5. 发送初始音频帧（模拟前端发送静音帧）
        print("\n5. 发送初始音频帧...")
        empty_audio = b'\x00' * 320  # 20ms静音帧
        audio_base64 = base64.b64encode(empty_audio).decode('utf-8')
        conversation.append_audio(audio_base64)
        # 注意：根据参考文件，不需要调用commit()
        
        print("✅ 初始音频帧已发送")
        
        # 6. 持续发送静音帧（模拟前端持续发送）
        print("\n6. 持续发送静音帧（10秒）...")
        start_time = time.time()
        while time.time() - start_time < 10:
            # 每200ms发送一个静音帧
            time.sleep(0.2)
            audio_base64 = base64.b64encode(empty_audio).decode('utf-8')
            conversation.append_audio(audio_base64)
            print(".", end='', flush=True)
        
        print("\n✅ 静音帧发送完成")
        
        # 7. 等待AI回复
        print("\n7. 等待AI回复...（等待20秒）")
        start_time = time.time()
        while time.time() - start_time < 20:
            if callback.response_received.is_set():
                print("✅ AI已回复")
                break
            time.sleep(0.5)
        
        if not callback.response_received.is_set():
            print("❌ AI没有回复")
        
        # 8. 分析结果
        print(f"\n=== 测试结果 ===")
        print(f"总事件数量: {len(callback.events_received)}")
        print(f"收到AI文本: {callback.text_received}")
        print(f"收到AI音频: {callback.audio_received}")
        print(f"AI响应完成: {callback.response_received.is_set()}")
        
        if callback.ai_text:
            print(f"AI回复内容: {callback.ai_text}")
        
        print(f"\n=== 事件列表 ===")
        for i, (event_type, timestamp) in enumerate(callback.events_received):
            elapsed = timestamp - callback.events_received[0][1] if i > 0 else 0
            print(f"{i+1:2d}. {event_type:40s} (+{elapsed:.2f}s)")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        print("\n8. 关闭连接...")
        try:
            conversation.close()
        except:
            pass
        print("✅ 测试完成")

if __name__ == "__main__":
    test_complete_flow()