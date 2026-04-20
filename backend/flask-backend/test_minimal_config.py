#!/usr/bin/env python3
"""最小化配置测试：尝试不同的配置组合"""
import os
import sys
import time
import base64

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

class TestCallback(OmniRealtimeCallback):
    """测试回调"""
    def __init__(self):
        super().__init__()
        self.events = []
        self.response_text = ""
        
    def on_open(self):
        self.events.append(('open', time.time()))
        print("📡 WebSocket连接已打开")
        
    def on_event(self, response):
        event_type = response.get('type')
        self.events.append((event_type, time.time()))
        
        if event_type == 'session.created':
            print(f"✅ 会话创建成功: {response['session']['id']}")
            
        elif event_type == 'response.audio_transcript.delta':
            text_delta = response.get('delta', '')
            self.response_text += text_delta
            print(f"💬 {text_delta}", end='', flush=True)
            
        elif event_type == 'response.done':
            print("\n✅ AI响应完成")
            
        elif event_type == 'error':
            error_msg = response.get('message', '未知错误')
            print(f"❌ 错误: {error_msg}")
            
    def on_close(self, close_status_code, close_msg):
        print(f"🔌 连接关闭: code={close_status_code}, msg={close_msg}")

def test_config(config_name: str, **kwargs):
    """测试特定配置"""
    print(f"\n=== 测试配置: {config_name} ===")
    
    dashscope.api_key = api_key
    callback = TestCallback()
    
    try:
        # 创建会话
        conversation = OmniRealtimeConversation(
            model='qwen3.5-omni-plus-realtime',
            callback=callback,
            url='wss://dashscope.aliyuncs.com/api-ws/v1/realtime'
        )
        
        # 连接
        conversation.connect()
        time.sleep(1)  # 等待连接
        
        # 配置会话
        instructions = "你是一位面试官。当会话建立后，请立即开始说话。现在请立即开始你的自我介绍！"
        conversation.update_session(
            output_modalities=[MultiModality.AUDIO, MultiModality.TEXT],
            instructions=instructions,
            **kwargs
        )
        
        print("✅ 会话配置完成，等待3秒...")
        time.sleep(3)
        
        # 发送初始音频
        empty_audio = b'\x00' * 320
        audio_base64 = base64.b64encode(empty_audio).decode('utf-8')
        conversation.append_audio(audio_base64)
        print("✅ 发送初始音频")
        
        # 等待响应
        print("等待AI回复（10秒）...")
        start_time = time.time()
        has_response = False
        
        while time.time() - start_time < 10:
            if any(event[0] == 'response.done' for event in callback.events):
                has_response = True
                break
            time.sleep(0.5)
        
        if has_response:
            print(f"✅ AI已回复: {config_name}")
        else:
            print(f"❌ AI没有回复: {config_name}")
        
        print(f"事件数量: {len(callback.events)}")
        for event_type, _ in callback.events:
            print(f"  - {event_type}")
        
        conversation.close()
        return has_response
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

def main():
    """测试不同的配置组合"""
    print("=== 测试不同的配置组合 ===")
    
    configs = [
        {
            'name': '最小配置',
            'voice': 'Ethan',
            'enable_turn_detection': True,
            'smooth_output': True
        },
        {
            'name': '参考文件配置',
            'voice': 'Ethan',
            'enable_turn_detection': True,
            'smooth_output': True,
            'enable_input_audio_transcription': True,
            'enable_output_audio_transcription': True
        },
        {
            'name': '带音频格式',
            'voice': 'Ethan',
            'enable_turn_detection': True,
            'input_audio_format': AudioFormat.PCM_16000HZ_MONO_16BIT,
            'output_audio_format': AudioFormat.PCM_16000HZ_MONO_16BIT,
            'smooth_output': True
        },
        {
            'name': '使用zhitian_emo',
            'voice': 'zhitian_emo',
            'enable_turn_detection': True,
            'smooth_output': True
        },
        {
            'name': '启用语音检测',
            'voice': 'Ethan',
            'enable_turn_detection': True,
            'smooth_output': True
        },
        {
            'name': '禁用语音检测',
            'voice': 'Ethan',
            'enable_turn_detection': False,
            'smooth_output': True
        }
    ]
    
    results = []
    for config in configs:
        name = config.pop('name')
        result = test_config(name, **config)
        results.append((name, result))
        time.sleep(2)  # 间隔时间
    
    print("\n=== 测试结果汇总 ===")
    for name, result in results:
        status = "✅ 成功" if result else "❌ 失败"
        print(f"{name}: {status}")

if __name__ == "__main__":
    main()