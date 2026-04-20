#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app

app = create_app()

if __name__ == '__main__':
    print("启动测试服务器...")
    app.run(host='0.0.0.0', port=8083, debug=True)