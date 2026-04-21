#!/usr/bin/env python3
import os
import sys
import logging
from dotenv import load_dotenv
from app import create_app, socketio

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    # 加载环境变量
    load_dotenv()
    # 设置环境变量
    if not os.environ.get('FLASK_ENV'):
        os.environ['FLASK_ENV'] = 'development'
    
    # 创建Flask应用
    app = create_app()
    
    # 获取配置
    host = app.config.get('SERVER_HOST', '0.0.0.0')
    port = app.config.get('SERVER_PORT', 8083)
    
    logger.info(f"Starting AI Interview Flask backend on {host}:{port}")
    logger.info(f"Environment: {os.environ.get('FLASK_ENV')}")
    logger.info(f"Debug mode: {app.config.get('DEBUG', False)}")
    
    # 运行应用
    if app.config.get('DEBUG', False):
        # 开发模式 - 使用SocketIO
        socketio.run(
            app,
            host=host,
            port=port,
            debug=True,
            use_reloader=False,
            allow_unsafe_werkzeug=True
        )
    else:
        # 生产模式 - 使用gunicorn with eventlet
        from gunicorn.app.base import BaseApplication
        
        class FlaskApplication(BaseApplication):
            def __init__(self, app, options=None):
                self.application = app
                self.options = options or {}
                super().__init__()
            
            def load_config(self):
                for key, value in self.options.items():
                    if key in self.cfg.settings and value is not None:
                        self.cfg.set(key.lower(), value)
            
            def load(self):
                return self.application
        
        options = {
            'bind': f'{host}:{port}',
            'workers': 4,
            'worker_class': 'eventlet',
            'timeout': 120,
            'accesslog': '-',
            'errorlog': '-',
            'loglevel': 'info'
        }
        
        FlaskApplication(app, options).run()

if __name__ == '__main__':
    main()
