import dashscope
from dashscope.audio.qwen_omni import OmniRealtimeConversation, OmniRealtimeCallback

# 设置API密钥
dashscope.api_key = "REMOVED_API_KEY"

class TestCallback(OmniRealtimeCallback):
    def on_open(self):
        print("✅ WebSocket连接已建立")
    
    def on_event(self, event):
        print(f"收到事件: {event}")
    
    def on_close(self, close_status_code, close_msg):
        print(f"连接关闭: code={close_status_code}, msg={close_msg}")
    
    def on_error(self, error):
        print(f"错误: {error}")

callback = TestCallback()
conversation = OmniRealtimeConversation(
    model="qwen3.5-omni-plus-realtime",
    callback=callback,
    url="wss://dashscope.aliyuncs.com/api-ws/v1/realtime"
)

print("=== OmniRealtimeConversation 属性 ===")
print(f"类型: {type(conversation)}")
print(f"所有属性: {dir(conversation)}")

print("\n=== 检查特定属性 ===")
# 检查是否有connect或start方法
for attr in dir(conversation):
    if not attr.startswith('_'):
        obj = getattr(conversation, attr)
        if callable(obj):
            print(f"方法: {attr}")
        else:
            print(f"属性: {attr} = {obj}")

print("\n=== 检查ws属性 ===")
if hasattr(conversation, 'ws'):
    print(f"ws: {conversation.ws}")
    print(f"ws类型: {type(conversation.ws)}")
    
    # 检查ws是否有connect方法
    if conversation.ws:
        print(f"ws的所有属性: {dir(conversation.ws)[:20]}")
    else:
        print("ws是None，需要建立连接")

print("\n=== 尝试查找连接方法 ===")
# 查看是否有_run或_connect方法
for attr in dir(conversation):
    if 'connect' in attr.lower() or 'run' in attr.lower() or 'start' in attr.lower():
        print(f"找到相关方法: {attr}")