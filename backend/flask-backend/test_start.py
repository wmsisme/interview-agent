import socketio
import logging
import time
import sys

logging.basicConfig(level=logging.DEBUG)

sio = socketio.Client(logger=True, engineio_logger=True)

@sio.event
def connect():
    print('连接建立')
    # 发送 start_interview 事件
    data = {
        'interviewId': 'test-interview-id-123',
        'position': 'java_backend'
    }
    sio.emit('start_interview', data)
    print('已发送 start_interview')

@sio.event
def connected(data):
    print('收到 connected 事件:', data)

@sio.event
def error(data):
    print('收到 error 事件:', data)

@sio.event
def connect_error(data):
    print('连接失败:', data)

@sio.event
def disconnect():
    print('断开连接')

try:
    sio.connect('http://localhost:8083/ws/video')
    print('连接成功')
    # 等待一段时间接收事件
    time.sleep(5)
except Exception as e:
    print('错误:', e)
    import traceback
    traceback.print_exc()
finally:
    sio.disconnect()