import eventlet

eventlet.monkey_patch()

import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE_DIR, 'common'))

import socketio
import eventlet.wsgi
from server import app

if len(sys.argv) < 2:
    # 表示启动时忘了传递端口号参数
    print('Usage: python main.py [port]')
    exit(1)  # 表示程序异常退出
port = int(sys.argv[1])

import chat

eventlet.wsgi.server(eventlet.listen(('', port)), app)
