#!/usr/bin/env python3
"""测试AI主动开始说话：模拟视频面试流程"""
import os
import sys
import time
import base64
import json
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

def create_test_image(width=640, height=480):
    """创建测试图像"""
    # 创建一个简单的测试图像
    image = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(image)
    
    # 画一些图形
    draw.rectangle([50, 50, 150, 150], fill='red', outline='black')
    draw.ellipse([200, 50, 300, 150], fill='blue', outline='black')
    draw.line([350, 50, 450, 150], fill='green', width=3)
    
    # 添加文本
    draw.text((100, 200), "Test Image", fill='black')
    draw.text((100, 230), f"Time: {time.time()}", fill='gray')
    
    # 转换为JPEG字节
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format='JPEG', quality=85)
    return img_byte_arr.getvalue()

class ActiveStartCallback(OmniRealtimeCallback):
    """主动开始回调"""
    def __init__(self):
        super().__init__()
        self.events = []
        self.ai_text = ""
        self.audio_received = False
        self.response_complete = False
        
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
            self.audio_received = True
            audio_len = len(response.get('delta', ''))
            print(f"🔊 收到AI音频数据: {audio_len}字节")
            
        elif event_type == 'response.done':
            print("\n✅ AI响应完成")
            self.response_complete = True
            
        elif event_type == 'error':
            error_msg = response.get('message', '未知错误')
            print(f"❌ 错误: {error_msg}")
            
    def on_close(self, close_status_code, close_msg):
        print(f"🔌 连接关闭: code={close_status_code}, msg={close_msg}")

def test_active_start(use_vad=False, send_video=True, send_audio=True, voice='Ethan'):
    """测试AI主动开始说话"""
    print(f"\n=== 测试主动开始 (VAD={use_vad}, 视频={send_video}, 音频={send_audio}, 音色={voice}) ===")
    
    dashscope.api_key = api_key
    callback = ActiveStartCallback()
    
    try:
        # 创建会话
        conversation = OmniRealtimeConversation(
            model='qwen3.5-omni-plus-realtime',
            callback=callback,
            url='wss://dashscope.aliyuncs.com/api-ws/v1/realtime'
        )
        
        # 连接
        conversation.connect()
        print("✅ 连接已建立")
        time.sleep(1)
        
        # 配置会话 - 使用明确的指令要求AI立即开始
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
            voice=voice,
            instructions=instructions,
            enable_turn_detection=use_vad,
            input_audio_format=AudioFormat.PCM_16000HZ_MONO_16BIT,
            output_audio_format=AudioFormat.PCM_16000HZ_MONO_16BIT,
            smooth_output=True,
            enable_input_audio_transcription=True,
            enable_output_audio_transcription=True
        )
        
        print("✅ 会话配置完成")
        time.sleep(2)  # 等待会话稳定
        
        # 发送初始数据
        test_sent = False
        
        if send_video:
            # 发送测试视频帧
            image_data = create_test_image()
            image_b64 = base64.b64encode(image_data).decode('utf-8')
            conversation.append_video(image_b64)
            print(f"📹 发送测试视频帧: {len(image_data)}字节")
            test_sent = True
        
        if send_audio:
            # 发送静音音频帧
            empty_audio = b'\x00' * 320  # 20ms静音
            audio_b64 = base64.b64encode(empty_audio).decode('utf-8')
            conversation.append_audio(audio_b64)
            print(f"🎤 发送静音音频帧: {len(empty_audio)}字节")
            test_sent = True
        
        if not test_sent:
            # 至少发送一个空的音频帧
            empty_audio = b'\x00' * 320
            audio_b64 = base64.b64encode(empty_audio).decode('utf-8')
            conversation.append_audio(audio_b64)
            print("🎤 发送默认静音帧")
        
        # 持续发送数据（模拟前端）
        print("🔄 持续发送数据（10秒）...")
        start_time = time.time()
        frame_count = 0
        
        while time.time() - start_time < 10:
            # 每500ms发送一次数据
            time.sleep(0.5)
            
            if send_video and frame_count % 2 == 0:  # 每1秒发送一次视频
                image_data = create_test_image()
                image_b64 = base64.b64encode(image_data).decode('utf-8')
                conversation.append_video(image_b64)
            
            # 发送静音音频帧
            empty_audio = b'\x00' * 320
            audio_b64 = base64.b64encode(empty_audio).decode('utf-8')
            conversation.append_audio(audio_b64)
            
            frame_count += 1
            if frame_count % 4 == 0:
                print(".", end='', flush=True)
        
        print(f"\n✅ 数据发送完成，共发送{frame_count}帧")
        
        # 等待AI回复
        print("⏳ 等待AI回复（15秒）...")
        wait_start = time.time()
        while time.time() - wait_start < 15:
            if callback.response_complete:
                print("✅ AI已回复")
                break
            time.sleep(0.5)
        
        if not callback.response_complete:
            print("❌ AI没有回复")
        
        # 打印结果
        print(f"\n=== 测试结果 ===")
        print(f"事件数量: {len(callback.events)}")
        print(f"AI文本: {len(callback.ai_text)}字符")
        print(f"收到AI音频: {callback.audio_received}")
        print(f"AI响应完成: {callback.response_complete}")
        
        if callback.ai_text:
            print(f"AI回复内容: {callback.ai_text}")
        
        print(f"\n=== 事件列表 ===")
        for i, (event_type, timestamp) in enumerate(callback.events[:20]):  # 只显示前20个事件
            elapsed = timestamp - callback.events[0][1] if i > 0 else 0
            print(f"{i+1:2d}. {event_type:40s} (+{elapsed:.2f}s)")
        
        return callback.response_complete
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        try:
            conversation.close()
        except:
            pass

def main():
    """运行多个测试"""
    print("=== 测试AI主动开始说话 ===")
    
    tests = [
        {"name": "禁用VAD+视频+音频", "use_vad": False, "send_video": True, "send_audio": True, "voice": "Ethan"},
        {"name": "启用VAD+视频+音频", "use_vad": True, "send_video": True, "send_audio": True, "voice": "Ethan"},
        {"name": "禁用VAD+仅音频", "use_vad": False, "send_video": False, "send_audio": True, "voice": "Ethan"},
        {"name": "禁用VAD+仅视频", "use_vad": False, "send_video": True, "send_audio": False, "voice": "Ethan"},
        {"name": "使用zhitian_emo", "use_vad": False, "send_video": True, "send_audio": True, "voice": "zhitian_emo"},
        {"name": "最小配置", "use_vad": False, "send_video": False, "send_audio": True, "voice": "Ethan", "no_audio_format": True},
    ]
    
    results = []
    for test in tests:
        print(f"\n{'='*60}")
        name = test.pop('name')
        
        if test.get('no_audio_format'):
            # 特殊测试：不使用音频格式参数
            test.pop('no_audio_format')
            results.append((name, test_simple_config(voice=test['voice'])))
        else:
            results.append((name, test_active_start(**test)))
        
        time.sleep(3)  # 间隔时间
    
    print(f"\n{'='*60}")
    print("=== 测试结果汇总 ===")
    for name, result in results:
        status = "✅ 成功" if result else "❌ 失败"
        print(f"{name:30s}: {status}")

def test_simple_config(voice='Ethan'):
    """测试最简单的配置（不使用音频格式参数）"""
    print(f"\n=== 测试简单配置（音色={voice}） ===")
    
    dashscope.api_key = api_key
    callback = ActiveStartCallback()
    
    try:
        conversation = OmniRealtimeConversation(
            model='qwen3.5-omni-plus-realtime',
            callback=callback,
            url='wss://dashscope.aliyuncs.com/api-ws/v1/realtime'
        )
        
        conversation.connect()
        time.sleep(1)
        
        # 简单指令
        instructions = "你是一位面试官。请立即开始你的自我介绍。现在请开始说话！"
        
        conversation.update_session(
            output_modalities=[MultiModality.AUDIO, MultiModality.TEXT],
            voice=voice,
            instructions=instructions,
            enable_turn_detection=False,
            smooth_output=True
        )
        
        print("✅ 简单配置完成")
        time.sleep(2)
        
        # 发送音频
        empty_audio = b'\x00' * 320
        audio_b64 = base64.b64encode(empty_audio).decode('utf-8')
        conversation.append_audio(audio_b64)
        print("✅ 发送音频帧")
        
        # 等待回复
        print("等待回复（10秒）...")
        start_time = time.time()
        while time.time() - start_time < 10:
            if callback.response_complete:
                print("✅ AI已回复")
                break
            time.sleep(0.5)
        
        if not callback.response_complete:
            print("❌ AI没有回复")
        
        conversation.close()
        return callback.response_complete
        
    except Exception as e:
        print(f"❌ 简单配置测试失败: {e}")
        return False

if __name__ == "__main__":
    main()