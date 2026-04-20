#!/usr/bin/env python3
"""测试API密钥有效性"""
import os
import dashscope
import json

API_KEY = "REMOVED_API_KEY"

def test_api_key_with_text():
    """使用文本API测试API密钥"""
    print("=== 测试API密钥有效性（文本API）===")
    
    dashscope.api_key = API_KEY
    
    try:
        # 尝试简单的文本生成
        from dashscope import Generation
        
        print("测试文本生成API...")
        response = Generation.call(
            model='qwen-plus',
            prompt='你好，请简单回复"API测试成功"',
            max_tokens=50
        )
        
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            print(f"✅ API密钥有效")
            print(f"响应: {response.output.text}")
            return True
        else:
            print(f"❌ API请求失败: {response.code} - {response.message}")
            print(f"详情: {response}")
            return False
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

def test_models_list():
    """测试列出可用模型"""
    print("\n=== 测试列出可用模型 ===")
    
    dashscope.api_key = API_KEY
    
    try:
        from dashscope import Model
        
        print("获取模型列表...")
        response = Model.list()
        
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            print(f"✅ 获取到模型列表")
            models = response.output
            print(f"共找到 {len(models)} 个模型")
            
            # 检查是否有实时模型
            realtime_models = [m for m in models if 'realtime' in m.get('model_id', '').lower()]
            print(f"实时模型: {len(realtime_models)} 个")
            
            for model in realtime_models[:5]:  # 显示前5个
                model_id = model.get('model_id', '未知')
                print(f"  - {model_id}")
                
            # 检查我们需要的模型是否存在
            target_model = 'qwen3.5-omni-plus-realtime'
            model_exists = any(target_model == m.get('model_id') for m in models)
            print(f"\n目标模型 '{target_model}' 是否存在: {'✅ 是' if model_exists else '❌ 否'}")
            
            return True
        else:
            print(f"❌ 获取模型列表失败: {response.code} - {response.message}")
            return False
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

def test_billing():
    """测试账户余额"""
    print("\n=== 测试账户余额 ===")
    
    dashscope.api_key = API_KEY
    
    try:
        from dashscope import Billing
        
        print("获取账户余额...")
        response = Billing.get()
        
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.output
            print(f"✅ 余额查询成功")
            print(f"可用额度: {data.get('available_amount', '未知')}")
            print(f"总消耗: {data.get('total_usage', '未知')}")
            return True
        else:
            print(f"❌ 余额查询失败: {response.code} - {response.message}")
            return False
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

def test_real_time_direct():
    """直接测试实时API（不使用我们的包装）"""
    print("\n=== 直接测试实时API ===")
    
    dashscope.api_key = API_KEY
    
    try:
        from dashscope.audio.qwen_omni import OmniRealtimeConversation, OmniRealtimeCallback, MultiModality
        import time
        import base64
        
        class DirectCallback(OmniRealtimeCallback):
            def __init__(self):
                super().__init__()
                self.events = []
                self.start_time = time.time()
                
            def on_event(self, response):
                event_type = response.get('type')
                elapsed = time.time() - self.start_time
                self.events.append((event_type, elapsed))
                print(f"[{elapsed:.2f}s] 事件: {event_type}")
                
                if event_type == 'session.created':
                    session_id = response.get('session', {}).get('id', '未知')
                    print(f"  -> 会话ID: {session_id}")
                elif event_type == 'error':
                    error_msg = response.get('message', '未知错误')
                    print(f"  -> 错误: {error_msg}")
        
        callback = DirectCallback()
        conversation = OmniRealtimeConversation(
            model='qwen3.5-omni-plus-realtime',
            callback=callback,
            url='wss://dashscope.aliyuncs.com/api-ws/v1/realtime'
        )
        
        print("1. 连接...")
        conversation.connect()
        time.sleep(3)
        
        print("2. 配置会话...")
        conversation.update_session(
            output_modalities=[MultiModality.TEXT],  # 只测试文本
            voice='Ethan',
            instructions="请回复'测试成功'。",
            enable_turn_detection=True
        )
        time.sleep(3)
        
        print("3. 发送音频数据...")
        for i in range(10):
            audio_data = b'\x00' * 800
            audio_b64 = base64.b64encode(audio_data).decode('utf-8')
            conversation.append_audio(audio_b64)
            time.sleep(0.1)
        
        print("4. 等待5秒...")
        time.sleep(5)
        
        print("5. 检查事件...")
        event_types = [e[0] for e in callback.events]
        print(f"收到的事件类型: {event_types}")
        
        has_response = any('response' in str(e).lower() for e in event_types)
        print(f"是否有响应事件: {'✅ 是' if has_response else '❌ 否'}")
        
        conversation.close()
        return has_response
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    print("开始测试API密钥有效性...")
    print(f"API密钥: {API_KEY[:10]}...{API_KEY[-10:]}")
    
    # 测试1: 文本API
    text_api_ok = test_api_key_with_text()
    
    # 测试2: 模型列表
    models_ok = test_models_list()
    
    # 测试3: 账户余额
    billing_ok = test_billing()
    
    # 测试4: 直接实时API
    realtime_ok = test_real_time_direct()
    
    print(f"\n=== 综合测试结果 ===")
    print(f"文本API: {'✅ 正常' if text_api_ok else '❌ 失败'}")
    print(f"模型列表: {'✅ 正常' if models_ok else '❌ 失败'}")
    print(f"账户余额: {'✅ 正常' if billing_ok else '❌ 失败'}")
    print(f"实时API: {'✅ 正常' if realtime_ok else '❌ 失败'}")
    
    if not text_api_ok:
        print("\n❌ API密钥可能无效或过期")
    elif text_api_ok and not realtime_ok:
        print("\n⚠️ API密钥有效，但实时API不可用")
        print("可能的原因:")
        print("1. 账户没有实时API权限")
        print("2. 实时模型服务暂时不可用")
        print("3. 网络连接到实时API有问题")
    elif all([text_api_ok, models_ok, billing_ok, realtime_ok]):
        print("\n✅ 所有测试通过，API密钥完全有效")

if __name__ == "__main__":
    main()