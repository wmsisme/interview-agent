from flask import Flask
from flask_cors import CORS
from flask_socketio import SocketIO
import os

# 创建SocketIO实例
socketio = SocketIO(async_mode='eventlet')

def create_app():
    app = Flask(__name__)
    
    CORS(app)
    
    app.config.from_pyfile('config/default.py')
    
    if os.environ.get('FLASK_ENV') == 'production':
        app.config.from_pyfile('config/production.py')
    else:
        app.config.from_pyfile('config/development.py')
    
    from .routes import interview, health, rag
    app.register_blueprint(interview.bp)
    app.register_blueprint(health.bp)
    app.register_blueprint(rag.bp)
    
    # 初始化SocketIO
    socketio.init_app(app, cors_allowed_origins="*", logger=False, engineio_logger=False)
    
    # 初始化视频WebSocket路由
    # 注意：视频面试是本项目唯一在用的面试链路，这里导入失败 = 核心功能不可用，
    # 因此必须打印醒目告警（历史事故：venv 缺 opencv 导致视频链路静默失效）。
    try:
        from .routes.websocket_video import init_video_websocket
        init_video_websocket(socketio)
        print("[OK] 视频WebSocket路由已注册（/ws/video）")
    except ImportError as e:
        print("!" * 72)
        print(f"[严重] 视频WebSocket路由导入失败，视频面试功能将不可用: {e}")
        print("       请确认依赖已装齐：pip install -r requirements.txt")
        print("!" * 72)
    except Exception as e:
        print("!" * 72)
        print(f"[严重] 初始化视频WebSocket路由失败，视频面试功能将不可用: {e}")
        print("!" * 72)
    
    from .models import database
    database.init_app(app)
    
    return app
