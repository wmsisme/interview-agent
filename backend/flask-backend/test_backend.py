#!/usr/bin/env python3
"""测试后端服务"""
import time
import requests
import json

def test_backend():
    """测试后端服务是否运行"""
    url = "http://localhost:8083"
    
    print(f"测试后端服务: {url}")
    
    try:
        # 测试健康检查
        health_url = f"{url}/health"
        print(f"测试健康检查: {health_url}")
        
        response = requests.get(health_url, timeout=5)
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.text}")
        
        if response.status_code == 200:
            print("✅ 后端服务运行正常")
            return True
        else:
            print(f"❌ 健康检查失败: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到后端服务")
        print("请确保后端服务正在运行")
        return False
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

def test_video_chat_endpoint():
    """测试视频聊天端点"""
    url = "http://localhost:8083/api/video-chat/test"
    
    print(f"\n测试视频聊天端点: {url}")
    
    try:
        response = requests.get(url, timeout=10)
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"响应: {json.dumps(data, indent=2, ensure_ascii=False)}")
            print("✅ 视频聊天端点正常")
            return True
        else:
            print(f"❌ 视频聊天端点失败: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

def main():
    """主函数"""
    print("=== 测试后端服务 ===")
    
    # 等待后端启动
    print("等待后端启动...")
    time.sleep(3)
    
    # 测试后端服务
    if test_backend():
        print("\n✅ 后端服务测试通过")
        
        # 测试视频聊天端点
        if test_video_chat_endpoint():
            print("\n✅ 所有测试通过")
            print("\n现在可以测试前端连接了")
            print("前端URL: http://localhost:5173 (假设前端运行在5173端口)")
        else:
            print("\n⚠️ 视频聊天端点可能有问题")
    else:
        print("\n❌ 后端服务测试失败")
        print("请检查:")
        print("1. 后端服务是否正在运行")
        print("2. 端口8083是否被占用")
        print("3. 是否有防火墙阻止连接")

if __name__ == "__main__":
    main()