#!/usr/bin/env python3
"""测试修复后的VideoChatService"""
import os
import sys
import time
import base64
import threading

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from app.services.video_chat_service import VideoChatService, VideoChatCallback
    print("✅ 导入依赖成功")
except ImportError as e:
    print(f"❌ 导入依赖失败: {e}")
    sys.exit(1)

class TestCallback(VideoChatCallback):
    """测试回调"""
    def __init__(self, session_id: str):
        super().__init__(session_id)
        self.audio_received = False
        self.text_received = False
        self.connected = False
        self.error = None
        self.ai_text = ""
        
    def on_audio(self, audio_data: bytes):
        self.audio_received = True
        print(f"🔊 收到AI音频: {len(audio_data)}字节")
        
    def on_text(self, text: str):
        self.text_received = True
        self.ai_text += text
        print(f"📝 AI文本: {text}")
        
    def on_connected(self):
        self.connected = True
        print("✅ WebSocket连接已建立")
        
    def on_closed(self):
        print("🔌 连接已关闭")
        
    def on_error(self, error: str):
        self.error = error
        print(f"❌ 错误: {error}")

def test_fixed_service():
    """测试修复后的服务"""
    print("\n=== 测试修复后的VideoChatService ===")
    
    session_id = "test_fixed_" + str(int(time.time()))
    callback = TestCallback(session_id)
    
    try:
        # 创建服务
        service = VideoChatService(
            session_id=session_id,
            position="软件工程师",
            job_description="负责后端开发，需要熟悉Python、Java等技术",
            user_id="test_user_123"
        )
        
        print(f"🚀 创建VideoChatService: {session_id}")
        
        # 创建会话
        conversation = service.create_conversation(callback)
        print("✅ 会话创建成功")
        
        # 等待连接建立
        print("等待连接建立...")
        start_time = time.time()
        while not callback.connected and time.time() - start_time < 10:
            time.sleep(0.5)
        
        if not callback.connected:
            print("❌ 连接超时")
            return False
        
        # 配置面试官
        print("配置面试官...")
        service.configure_interviewer()
        print("✅ 面试官配置完成")
        
        # 等待一小段时间让配置生效
        time.sleep(2)
        
        # 测试发送音频帧
        print("📤 测试发送音频帧...")
        audio_data = b'\x00' * 800  # 25ms静音
        service.send_audio(audio_data)
        print("✅ 音频帧发送成功")
        
        # 测试发送视频帧
        print("📤 测试发送视频帧...")
        # 创建简单的测试图像
        test_image = b'test_image_data' * 50  # 简单测试数据
        image_b64 = base64.b64encode(test_image).decode('utf-8')
        service.send_image(image_b64)
        print("✅ 视频帧发送成功")
        
        # 持续发送数据（模拟前端）
        print("🔄 持续发送数据（8秒）...")
        start_time = time.time()
        count = 0
        
        while time.time() - start_time < 8:
            # 发送音频帧
            audio_data = b'\x00' * 800
            service.send_audio(audio_data)
            
            # 每500ms发送一次视频
            if count % 5 == 0:
                test_image = b'test_image_' + str(count).encode() + b'_' * 50
                image_b64 = base64.b64encode(test_image).decode('utf-8')
                service.send_image(image_b64)
            
            count += 1
            time.sleep(0.1)  # 100ms间隔
            
            if count % 10 == 0:
                print(".", end='', flush=True)
        
        print(f"\n✅ 发送完成，共{count}次发送")
        
        # 等待AI响应
        print("⏳ 等待AI响应（15秒）...")
        response_start = time.time()
        ai_responded = False
        
        while time.time() - response_start < 15:
            if callback.text_received or callback.audio_received:
                ai_responded = True
                print("\n✅ AI已响应")
                break
            time.sleep(0.5)
        
        if not ai_responded:
            print("\n❌ AI没有响应")
            
            if callback.error:
                print(f"错误信息: {callback.error}")
            
            # 检查连接状态
            print(f"连接状态: {'已连接' if callback.connected else '未连接'}")
            print(f"收到音频: {'是' if callback.audio_received else '否'}")
            print(f"收到文本: {'是' if callback.text_received else '否'}")
        
        # 打印AI回复的文本
        if callback.ai_text:
            print(f"\n📋 AI回复内容: {callback.ai_text}")
        
        # 清理
        service.stop()
        print("✅ 服务已停止")
        
        return ai_responded
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_direct_api():
    """直接测试API（不通过服务层）"""
    print("\n=== 直接测试DashScope API ===")
    
    try:
        import dashscope
        from dashscope.audio.qwen_omni import OmniRealtimeConversation, OmniRealtimeCallback, MultiModality
        
        api_key = os.environ.get('VIDEO_CHAT_API_KEY', 'REMOVED_API_KEY')
        dashscope.api_key = api_key
        
        class DirectCallback(OmniRealtimeCallback):
            def __init__(self):
                super().__init__()
                self.events = []
                
            def on_open(self):
                print("📡 WebSocket连接已打开")
                self.events.append(('open', time.time()))
                
            def on_event(self, response):
                event_type = response.get('type')
                self.events.append((event_type, time.time()))
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
                    print(f"\n❌ 错误: {error_msg}")
                    
            def on_close(self, close_status_code, close_msg):
                print(f"🔌 连接关闭: code={close_status_code}, msg={close_msg}")
        
        callback = DirectCallback()
        conversation = OmniRealtimeConversation(
            model='qwen3.5-omni-plus-realtime',
            callback=callback,
            url='wss://dashscope.aliyuncs.com/api-ws/v1/realtime'
        )
        
        conversation.connect()
        print("✅ 连接成功")
        time.sleep(2)
        
        # 配置会话 - 使用与项目相同的配置
        conversation.update_session(
            output_modalities=[MultiModality.AUDIO, MultiModality.TEXT],
            voice='Ethan',
            instructions="你是一位面试官。请立即开始你的自我介绍。现在请说话！",
            enable_turn_detection=True
        )
        
        print("✅ 会话配置完成")
        time.sleep(2)
        
        # 持续发送音频
        print("📤 持续发送音频（5秒）...")
        start_time = time.time()
        count = 0
        
        while time.time() - start_time < 5:
            audio_data = b'\x00' * 800
            audio_b64 = base64.b64encode(audio_data).decode('utf-8')
            conversation.append_audio(audio_b64)
            count += 1
            time.sleep(0.1)
        
        print(f"\n✅ 发送完成，共{count}帧")
        
        # 等待响应
        print("⏳ 等待响应（10秒）...")
        time.sleep(10)
        
        # 检查是否有响应
        has_response = any(event[0] == 'response.created' for event in callback.events)
        print(f"AI是否开始响应: {'✅ 是' if has_response else '❌ 否'}")
        
        conversation.close()
        return has_response
        
    except Exception as e:
        print(f"❌ 直接API测试失败: {e}")
        return False

def main():
    """主函数"""
    print("=== 测试修复后的视频聊天服务 ===")
    
    print("\n1. 测试VideoChatService")
    result1 = test_fixed_service()
    
    time.sleep(3)
    
    print("\n2. 测试直接API调用")
    result2 = test_direct_api()
    
    print(f"\n=== 测试结果 ===")
    print(f"VideoChatService: {'✅ 成功' if result1 else '❌ 失败'}")
    print(f"直接API调用: {'✅ 成功' if result2 else '❌ 失败'}")
    
    if not result1 and not result2:
        print("\n⚠️ 所有测试都失败，可能的问题:")
        print("1. API密钥无效")
        print("2. 网络连接问题")
        print("3. DashScope服务不可用")
        print("4. 模型配置错误")

if __name__ == "__main__":
    main()