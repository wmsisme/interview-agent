import socketio
import logging
import sys

logging.basicConfig(level=logging.DEBUG)

sio = socketio.Client(logger=True, engineio_logger=True)

@sio.event
def connect():
    print('连接建立')

@sio.event
def connect_error(data):
    print('连接失败:', data)

@sio.event
def disconnect():
    print('断开连接')

try:
    sio.connect('http://localhost:8083/ws/video')
    print('连接成功')
    sio.wait()
except Exception as e:
    print('错误:', e)
finally:
    sio.disconnect()