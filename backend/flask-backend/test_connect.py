#!/usr/bin/env python3
"""测试Socket.IO连接到视频命名空间"""
import socketio
import time
import sys

sio = socketio.Client(logger=True, engineio_logger=True)

@sio.event
def connect():
    print("✅ 连接成功到Socket.IO服务器")

@sio.event
def connect_error(data):
    print(f"❌ 连接错误: {data}")

@sio.event
def disconnect():
    print("🔌 连接断开")

@sio.event
def connected(data):
    print(f"✅ 连接到命名空间，数据: {data}")

def test_connect_to_video():
    """测试连接到视频命名空间"""
    print("=== 测试Socket.IO连接到/ws/video命名空间 ===")
    print("尝试连接到: ws://localhost:8083")
    
    try:
        # 连接到服务器，然后使用命名空间
        sio.connect('ws://localhost:8083', transports=['websocket'])
        print("✅ 连接到根命名空间成功")
        
        # 等待连接建立
        time.sleep(2)
        
        if sio.connected:
            print(f"✅ 连接状态: connected={sio.connected}")
            print(f"✅ Session ID: {sio.sid}")
            
            # 现在尝试连接到视频命名空间
            print("\n尝试连接到/ws/video命名空间...")
            # 创建一个新的socketio客户端，专门连接到命名空间
            sio_video = socketio.Client()
            
            @sio_video.event
            def connect():
                print("✅ 成功连接到/ws/video命名空间")
                
            @sio_video.event  
            def connected(data):
                print(f"✅ 收到connected事件: {data}")
                
            # 连接到命名空间
            sio_video.connect('ws://localhost:8083', namespaces=['/ws/video'], transports=['websocket'])
            time.sleep(3)
            
            if sio_video.connected:
                print(f"✅ 视频命名空间连接状态: connected={sio_video.connected}")
                print(f"✅ 命名空间: {list(sio_video.namespaces.keys())}")
                
                # 发送测试消息
                print("\n发送测试消息到视频命名空间...")
                sio_video.emit('test', {'message': 'ping'}, namespace='/ws/video')
                time.sleep(2)
                
                sio_video.disconnect()
            else:
                print("❌ 视频命名空间连接失败")
                
        else:
            print("❌ 根连接未建立")
            
        # 断开连接
        sio.disconnect()
        time.sleep(1)
        
    except Exception as e:
        print(f"❌ 连接失败: {e}")
        import traceback
        traceback.print_exc()

def test_without_namespace():
    """测试连接到根命名空间"""
    print("\n=== 测试连接到根命名空间 ===")
    
    sio2 = socketio.Client()
    
    @sio2.event
    def connect():
        print("✅ 连接到根命名空间")
        
    try:
        sio2.connect('http://localhost:8083', transports=['websocket'])
        time.sleep(3)
        
        if sio2.connected:
            print(f"✅ 根连接状态: connected={sio2.connected}")
        else:
            print("❌ 根连接失败")
            
        sio2.disconnect()
        
    except Exception as e:
        print(f"❌ 根连接失败: {e}")

def test_ping():
    """测试简单的ping请求"""
    print("\n=== 测试简单HTTP连接 ===")
    import requests
    try:
        response = requests.get('http://localhost:8083', timeout=5)
        print(f"✅ HTTP服务器响应: {response.status_code}")
        if response.status_code == 200:
            print("✅ 后端服务器正在运行")
    except Exception as e:
        print(f"❌ HTTP请求失败: {e}")

def main():
    print("Socket.IO连接测试开始...")
    
    # 先测试HTTP连接
    test_ping()
    
    # 测试根命名空间
    test_without_namespace()
    
    # 测试视频命名空间
    test_connect_to_video()
    
    print("\n=== 测试完成 ===")

if __name__ == "__main__":
    main()