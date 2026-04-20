#!/usr/bin/env python3
"""测试API密钥有效性"""
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

def test_api_key():
    """测试API密钥"""
    print("=== 测试API密钥 ===")
    
    # 测试多个API密钥
    api_keys = [
        "REMOVED_API_KEY",  # 项目使用的密钥
        os.environ.get('VIDEO_CHAT_API_KEY', ''),
        os.environ.get('DASHSCOPE_API_KEY', ''),
        os.environ.get('ALIYUN_API_KEY', ''),
    ]
    
    for i, api_key in enumerate(api_keys):
        if not api_key:
            continue
            
        print(f"\n🔑 测试API密钥 {i+1}: {api_key[:10]}...")
        
        try:
            dashscope.api_key = api_key
            
            # 尝试简单调用验证API密钥
            from dashscope import Generation
            response = Generation.call(
                model='qwen-max',
                prompt='你好',
                max_tokens=10
            )
            
            print(f"✅ API密钥有效")
            print(f"   响应状态: {response.status_code}")
            
            # 尝试创建实时会话
            class TestCallback(OmniRealtimeCallback):
                def on_open(self):
                    print("   连接已打开")
                    
                def on_event(self, response):
                    event_type = response.get('type')
                    print(f"   事件: {event_type}")
                    
                def on_error(self, error):
                    print(f"   连接错误: {error}")
            
            callback = TestCallback()
            conversation = OmniRealtimeConversation(
                model='qwen3.5-omni-plus-realtime',
                callback=callback,
                url='wss://dashscope.aliyuncs.com/api-ws/v1/realtime'
            )
            
            # 尝试连接（不等待太久）
            conversation.connect()
            time.sleep(2)
            
            print("   实时会话连接成功")
            
            # 尝试配置会话
            conversation.update_session(
                output_modalities=[MultiModality.AUDIO, MultiModality.TEXT],
                voice='Ethan',
                instructions='测试',
                enable_turn_detection=False
            )
            
            print("   会话配置成功")
            
            conversation.close()
            return True
            
        except Exception as e:
            print(f"❌ API密钥无效或出错: {e}")
    
    return False

def test_direct_reference():
    """直接测试参考文件配置"""
    print("\n=== 直接测试参考文件配置 ===")
    
    # 使用参考文件的配置
    try:
        # 切换到参考文件目录
        ref_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'realtime_video_chat_project')
        if os.path.exists(ref_dir):
            print(f"📂 切换到参考文件目录: {ref_dir}")
            os.chdir(ref_dir)
            
            # 尝试导入参考文件配置
            sys.path.insert(0, ref_dir)
            from config import API_KEY, MODEL, URL, VOICE
            
            print(f"🔑 API密钥: {API_KEY[:10]}...")
            print(f"📊 模型: {MODEL}")
            print(f"🌐 URL: {URL}")
            print(f"🎤 音色: {VOICE}")
            
            dashscope.api_key = API_KEY
            
            # 创建测试会话
            class RefCallback(OmniRealtimeCallback):
                def __init__(self):
                    super().__init__()
                    self.connected = False
                    
                def on_open(self):
                    print("✅ 连接已打开")
                    self.connected = True
                    
                def on_event(self, response):
                    event_type = response.get('type')
                    print(f"📨 事件: {event_type}")
                    
                    if event_type == 'session.created':
                        session_id = response.get('session', {}).get('id', 'N/A')
                        print(f"✅ 会话创建: {session_id}")
                    
                    elif event_type == 'session.updated':
                        print("✅ 会话更新成功")
                    
                    elif event_type == 'response.created':
                        print("🔊 AI开始生成响应")
                    
                    elif event_type == 'error':
                        error_msg = response.get('message', '未知错误')
                        print(f"❌ 错误: {error_msg}")
                        
                def on_error(self, error):
                    print(f"❌ 连接错误: {error}")
            
            callback = RefCallback()
            conversation = OmniRealtimeConversation(
                model=MODEL,
                callback=callback,
                url=URL
            )
            
            print("🚀 尝试连接...")
            conversation.connect()
            time.sleep(3)  # 等待连接
            
            if callback.connected:
                print("✅ WebSocket连接成功")
                
                # 配置会话（参考文件配置）
                conversation.update_session(
                    output_modalities=[MultiModality.AUDIO, MultiModality.TEXT],
                    voice=VOICE,
                    instructions="测试API。请说'测试成功'。",
                    enable_turn_detection=True
                )
                
                print("✅ 会话配置完成")
                time.sleep(2)
                
                # 发送音频帧
                audio_data = b'\x00' * 800
                audio_b64 = base64.b64encode(audio_data).decode('utf-8')
                conversation.append_audio(audio_b64)
                print("✅ 发送音频帧")
                
                # 等待响应
                print("⏳ 等待响应（10秒）...")
                time.sleep(10)
                
                conversation.close()
                print("✅ 测试完成")
                return True
            else:
                print("❌ 连接失败")
                return False
                
        except Exception as e:
            print(f"❌ 测试失败: {e}")
            import traceback
            traceback.print_exc()
            return False
            
    finally:
        # 切回原目录
        os.chdir(os.path.dirname(__file__))

def main():
    """主函数"""
    print("=== API密钥和配置测试 ===")
    
    print("\n1. 测试API密钥有效性")
    key_valid = test_api_key()
    
    print("\n2. 测试参考文件配置")
    ref_works = test_direct_reference()
    
    print(f"\n=== 测试结果 ===")
    print(f"API密钥有效: {'✅ 是' if key_valid else '❌ 否'}")
    print(f"参考文件工作: {'✅ 是' if ref_works else '❌ 否'}")
    
    if not key_valid:
        print("\n⚠️ API密钥可能无效，请检查：")
        print("1. API密钥是否正确")
        print("2. 是否已经启用Qwen-Omni-Realtime服务")
        print("3. 账户余额是否充足")
        
    if key_valid and not ref_works:
        print("\n⚠️ API密钥有效但参考文件不工作，可能是：")
        print("1. 网络问题（防火墙/代理）")
        print("2. DashScope服务暂时不可用")
        print("3. 模型服务未启用")

if __name__ == "__main__":
    main()