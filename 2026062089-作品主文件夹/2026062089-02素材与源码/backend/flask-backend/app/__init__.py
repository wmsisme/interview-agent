from flask import Flask
from flask_cors import CORS
from flask_socketio import SocketIO
import os

# 创建SocketIO实例
socketio = SocketIO()

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
    try:
        from .routes.websocket_video import init_video_websocket
        init_video_websocket(socketio)
        print("视频WebSocket路由已注册")
    except ImportError as e:
        print(f"警告：无法导入视频WebSocket路由: {e}")
    except Exception as e:
        print(f"警告：初始化视频WebSocket路由失败: {e}")
    
    from .models import database
    database.init_app(app)
    
    return app
