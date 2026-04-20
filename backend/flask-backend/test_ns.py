import socketio
import logging
import time

logging.basicConfig(level=logging.DEBUG)

sio = socketio.Client(logger=True, engineio_logger=True)

@sio.event(namespace='/ws/video')
def connect():
    print('连接建立 /ws/video')
    data = {
        'interviewId': 'test-interview-id-456',
        'position': 'java_backend'
    }
    sio.emit('start_interview', data, namespace='/ws/video')
    print('已发送 start_interview')

@sio.event(namespace='/ws/video')
def connected(data):
    print('收到 connected 事件:', data)

@sio.event(namespace='/ws/video')
def error(data):
    print('收到 error 事件:', data)

@sio.event
def connect_error(data):
    print('连接失败:', data)

@sio.event
def disconnect():
    print('断开连接')

try:
    sio.connect('http://localhost:8083', namespaces=['/ws/video'])
    print('连接成功')
    time.sleep(5)
except Exception as e:
    print('错误:', e)
    import traceback
    traceback.print_exc()
finally:
    sio.disconnect()