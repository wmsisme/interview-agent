#!/usr/bin/env python3
"""测试参考文件的精确配置"""
import os
import sys
import time
import base64

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    import dashscope
    from dashscope.audio.qwen_omni import OmniRealtimeConversation, OmniRealtimeCallback, MultiModality
    
    print("✅ 导入依赖成功")
except ImportError as e:
    print(f"❌ 导入依赖失败: {e}")
    sys.exit(1)

# API密钥
api_key = os.environ.get('VIDEO_CHAT_API_KEY', 'REMOVED_API_KEY')

class DetailedCallback(OmniRealtimeCallback):
    """详细回调，打印所有信息"""
    def __init__(self):
        super().__init__()
        self.events = []
        
    def on_open(self):
        self.events.append(('open', time.time(), {}))
        print("📡 WebSocket连接已打开")
        
    def on_event(self, response):
        event_type = response.get('type')
        self.events.append((event_type, time.time(), response.copy()))
        
        print(f"\n📨 事件: {event_type}")
        
        # 打印重要字段
        if 'session' in response:
            print(f"   会话ID: {response.get('session', {}).get('id', 'N/A')}")
        
        if 'message' in response:
            print(f"   消息: {response['message']}")
            
        if 'transcript' in response:
            print(f"   转写: {response['transcript']}")
            
        if 'delta' in response:
            data_len = len(response['delta'])
            print(f"   数据长度: {data_len}")
        
        # 打印错误详细信息
        if event_type == 'error':
            print(f"   ❌ 完整错误响应:")
            for key, value in response.items():
                print(f"     {key}: {value}")
                
    def on_close(self, close_status_code, close_msg):
        print(f"\n🔌 连接关闭: code={close_status_code}, msg={close_msg}")
        
    def on_error(self, error):
        print(f"\n❌ 连接错误: {error}")

def test_exact_reference():
    """测试参考文件的精确配置"""
    print("\n=== 测试参考文件精确配置 ===")
    
    dashscope.api_key = api_key
    callback = DetailedCallback()
    
    try:
        # 创建会话 - 与参考文件相同
        conversation = OmniRealtimeConversation(
            model='qwen3.5-omni-plus-realtime',
            callback=callback,
            url='wss://dashscope.aliyuncs.com/api-ws/v1/realtime'
        )
        
        # 连接
        conversation.connect()
        print("✅ 连接成功")
        time.sleep(1)
        
        # 配置会话 - 与参考文件完全相同
        conversation.update_session(
            output_modalities=[MultiModality.AUDIO, MultiModality.TEXT],
            voice='Ethan',  # 参考文件使用Ethan
            instructions="你是一个视觉AI助手，可以实时看到摄像头画面。请根据你看到的视频内容回答用户的问题。",
            enable_turn_detection=True  # 使用VAD模式
            # 注意：参考文件没有设置音频格式参数
        )
        
        print("✅ 会话配置完成（参考文件配置）")
        
        # 等待会话稳定
        print("等待3秒...")
        time.sleep(3)
        
        # 发送音频数据 - 参考文件持续发送音频
        print("发送音频数据...")
        empty_audio = b'\x00' * 320
        audio_base64 = base64.b64encode(empty_audio).decode('utf-8')
        conversation.append_audio(audio_base64)
        
        # 发送一些音频数据
        print("持续发送音频（5秒）...")
        start_time = time.time()
        count = 0
        while time.time() - start_time < 5:
            time.sleep(0.2)
            conversation.append_audio(audio_base64)
            count += 1
            if count % 5 == 0:
                print(".", end='', flush=True)
        
        print(f"\n✅ 发送完成，共{count}个音频帧")
        
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
            print("✅ AI已回复")
        else:
            print("❌ AI没有回复")
        
        # 打印事件总结
        print(f"\n=== 事件总结 ===")
        print(f"总事件数: {len(callback.events)}")
        for i, (event_type, timestamp, response) in enumerate(callback.events):
            elapsed = timestamp - callback.events[0][1] if i > 0 else 0
            print(f"{i+1:2d}. {event_type:40s} (+{elapsed:.2f}s)")
            
            # 如果是错误事件，打印更多信息
            if event_type == 'error':
                print(f"    错误详情: {response}")
        
        conversation.close()
        return has_response
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_with_audio_format():
    """测试添加音频格式参数"""
    print("\n=== 测试添加音频格式参数 ===")
    
    dashscope.api_key = api_key
    callback = DetailedCallback()
    
    try:
        from dashscope.audio.qwen_omni import AudioFormat
        
        conversation = OmniRealtimeConversation(
            model='qwen3.5-omni-plus-realtime',
            callback=callback,
            url='wss://dashscope.aliyuncs.com/api-ws/v1/realtime'
        )
        
        conversation.connect()
        print("✅ 连接成功")
        time.sleep(1)
        
        # 配置会话 - 添加音频格式参数
        conversation.update_session(
            output_modalities=[MultiModality.AUDIO, MultiModality.TEXT],
            voice='Ethan',
            instructions="你是一个视觉AI助手，可以实时看到摄像头画面。请根据你看到的视频内容回答用户的问题。",
            enable_turn_detection=True,
            input_audio_format=AudioFormat.PCM_16000HZ_MONO_16BIT,
            output_audio_format=AudioFormat.PCM_16000HZ_MONO_16BIT,
            smooth_output=True,
            enable_input_audio_transcription=True,
            enable_output_audio_transcription=True
        )
        
        print("✅ 会话配置完成（带音频格式）")
        
        # 其余测试相同
        time.sleep(3)
        print("发送音频数据...")
        empty_audio = b'\x00' * 320
        audio_base64 = base64.b64encode(empty_audio).decode('utf-8')
        conversation.append_audio(audio_base64)
        
        print("持续发送音频（5秒）...")
        start_time = time.time()
        count = 0
        while time.time() - start_time < 5:
            time.sleep(0.2)
            conversation.append_audio(audio_base64)
            count += 1
        
        print(f"\n✅ 发送完成，共{count}个音频帧")
        
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
            print("✅ AI已回复")
        else:
            print("❌ AI没有回复")
        
        conversation.close()
        return has_response
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

def main():
    """运行测试"""
    print("=== 测试配置参数影响 ===")
    
    print("\n1. 测试参考文件精确配置（无音频格式参数）")
    result1 = test_exact_reference()
    
    time.sleep(3)
    
    print("\n2. 测试添加音频格式参数")
    result2 = test_with_audio_format()
    
    print(f"\n=== 测试结果 ===")
    print(f"参考文件配置: {'✅ 成功' if result1 else '❌ 失败'}")
    print(f"添加音频格式: {'✅ 成功' if result2 else '❌ 失败'}")

if __name__ == "__main__":
    main()