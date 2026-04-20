#!/usr/bin/env python3
"""简单测试修复后的配置"""
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

class SimpleCallback(OmniRealtimeCallback):
    """简单回调"""
    def __init__(self):
        super().__init__()
        self.event_list = []
        
    def on_open(self):
        print("📡 WebSocket连接已打开")
        self.event_list.append(('open', time.time()))
        
    def on_event(self, response):
        event_type = response.get('type')
        self.event_list.append((event_type, time.time(), response))
        print(f"📨 事件: {event_type}")
        
        if event_type == 'response.created':
            print("🔊 AI开始生成响应")
            
        elif event_type == 'response.audio_transcript.delta':
            text = response.get('delta', '')
            print(f"💬 {text}", end='', flush=True)
            
        elif event_type == 'response.done':
            print("\n✅ AI响应完成")
            
        elif event_type == 'error':
            error_msg = response.get('message', '未知错误')
            print(f"❌ 错误: {error_msg}")
            print(f"   完整响应: {response}")
            
    def on_close(self, close_status_code, close_msg):
        print(f"🔌 连接关闭: code={close_status_code}, msg={close_msg}")

def test_simple():
    """简单测试"""
    print("\n=== 简单测试修复后的配置 ===")
    
    dashscope.api_key = api_key
    callback = SimpleCallback()
    
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
        
        # 配置会话 - 尝试不同的配置
        instructions = "请说'你好，我是面试官'。"
        
        # 测试1：启用VAD，使用音频格式参数
        print("\n🔬 测试1：启用VAD + 音频格式参数")
        conversation.update_session(
            output_modalities=[MultiModality.AUDIO, MultiModality.TEXT],
            voice='Ethan',
            instructions=instructions,
            enable_turn_detection=True,
            input_audio_format=AudioFormat.PCM_16000HZ_MONO_16BIT,
            output_audio_format=AudioFormat.PCM_16000HZ_MONO_16BIT,
            smooth_output=True
        )
        
        print("✅ 配置完成")
        time.sleep(2)
        
        # 发送音频
        print("📤 发送音频帧（800字节）...")
        audio_data = b'\x00' * 800
        audio_b64 = base64.b64encode(audio_data).decode('utf-8')
        conversation.append_audio(audio_b64)
        
        # 等待响应
        print("⏳ 等待响应（5秒）...")
        time.sleep(5)
        
        # 检查是否有响应
        has_response = any(event[0] == 'response.created' for event in callback.event_list)
        print(f"AI是否开始响应: {'✅ 是' if has_response else '❌ 否'}")
        
        if not has_response:
            print("\n📊 事件列表:")
            for i, event in enumerate(callback.event_list):
                if len(event) == 3:
                    event_type, timestamp, response = event
                    elapsed = timestamp - callback.event_list[0][1] if i > 0 else 0
                    print(f"  {i+1:2d}. {event_type:30s} (+{elapsed:.2f}s)")
                else:
                    print(f"  {i+1:2d}. {event}")
        
        # 测试2：禁用VAD
        print("\n\n🔬 测试2：禁用VAD + 简单指令")
        
        # 创建新会话
        conversation.close()
        time.sleep(1)
        
        callback2 = SimpleCallback()
        conversation2 = OmniRealtimeConversation(
            model='qwen3.5-omni-plus-realtime',
            callback=callback2,
            url='wss://dashscope.aliyuncs.com/api-ws/v1/realtime'
        )
        
        conversation2.connect()
        time.sleep(1)
        
        conversation2.update_session(
            output_modalities=[MultiModality.AUDIO, MultiModality.TEXT],
            voice='Ethan',
            instructions="请立即开始说话。",
            enable_turn_detection=False,
            smooth_output=True
        )
        
        print("✅ 配置完成")
        time.sleep(2)
        
        # 发送音频
        print("📤 发送音频帧...")
        audio_data = b'\x00' * 800
        audio_b64 = base64.b64encode(audio_data).decode('utf-8')
        conversation2.append_audio(audio_b64)
        
        # 等待响应
        print("⏳ 等待响应（5秒）...")
        time.sleep(5)
        
        # 检查是否有响应
        has_response2 = any(event[0] == 'response.created' for event in callback2.event_list)
        print(f"AI是否开始响应: {'✅ 是' if has_response2 else '❌ 否'}")
        
        conversation2.close()
        
        return has_response or has_response2
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_without_audio_format():
    """测试不使用音频格式参数（参考文件模式）"""
    print("\n=== 测试参考文件模式（无音频格式参数） ===")
    
    dashscope.api_key = api_key
    callback = SimpleCallback()
    
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
            instructions="你是一个视觉AI助手。请说'你好'。",
            enable_turn_detection=True  # VAD模式
        )
        
        print("✅ 配置完成（参考文件模式）")
        time.sleep(2)
        
        # 持续发送音频
        print("📤 持续发送音频（3秒）...")
        start_time = time.time()
        count = 0
        
        while time.time() - start_time < 3:
            audio_data = b'\x00' * 800
            audio_b64 = base64.b64encode(audio_data).decode('utf-8')
            conversation.append_audio(audio_b64)
            count += 1
            time.sleep(0.1)  # 10 FPS
        
        print(f"✅ 发送完成，共{count}帧")
        
        # 等待响应
        print("⏳ 等待响应（5秒）...")
        time.sleep(5)
        
        # 检查是否有响应
        has_response = any(event[0] == 'response.created' for event in callback.event_list)
        print(f"AI是否开始响应: {'✅ 是' if has_response else '❌ 否'}")
        
        conversation.close()
        return has_response
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

def main():
    """主函数"""
    print("=== 简单测试修复 ===")
    
    print("\n1. 测试简单配置")
    result1 = test_simple()
    
    time.sleep(2)
    
    print("\n2. 测试参考文件模式（无音频格式）")
    result2 = test_without_audio_format()
    
    print(f"\n=== 测试结果 ===")
    print(f"简单配置测试: {'✅ 成功' if result1 else '❌ 失败'}")
    print(f"参考文件模式: {'✅ 成功' if result2 else '❌ 失败'}")
    
    if not result1 and not result2:
        print("\n⚠️ 所有测试都失败，可能是API密钥或服务问题")
        print(f"API密钥: {api_key[:10]}...")
        print("建议检查：")
        print("1. API密钥是否有效")
        print("2. 网络连接是否正常")
        print("3. DashScope服务是否正常")

if __name__ == "__main__":
    main()