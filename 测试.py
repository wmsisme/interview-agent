import os
from dashscope import Generation
import dashscope
#  api_key=os.getenv("DASHSCOPE_API_KEY"),这是环境变量中的API Key
dashscope.base_http_api_url = 'https://dashscope.aliyuncs.com/api/v1'

messages = [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "你好，我是张三。"},
]
response = Generation.call(
    # 若没有配置环境变量，请用百炼API Key将下行替换为：api_key = "sk-xxx",
    api_key="REMOVED_API_KEY",
    model="deepseek-v4-flash",
    messages=messages,
    result_format="message",
    # 开启深度思考
    enable_thinking=True,
)

if response.status_code == 200:
    # 打印思考过程
    print("=" * 20 + "思考过程" + "=" * 20)
    print(response.output.choices[0].message.reasoning_content)
    
    # 打印回复
    print("=" * 20 + "完整回复" + "=" * 20)
    print(response.output.choices[0].message.content)
else:
    print(f"HTTP返回码：{response.status_code}")
    print(f"错误码：{response.code}")
    print(f"错误信息：{response.message}")