#!/usr/bin/env python3
import os
# Remove monkey patching - it's causing compatibility issues with Python 3.13
# from gevent import monkey
# monkey.patch_all()

from backend import create_app
from backend.extensions import socketio

app = create_app()

if __name__ == "__main__":
    host = os.environ.get("FLASK_HOST", "0.0.0.0")
    port = int(os.environ.get("FLASK_PORT", 1337))
    
    print(f"Starting AuthBerry with WebSocket support on {host}:{port}")
    
    if os.environ.get("FLASK_DEBUG") == "1":
        # Run with SocketIO's development server in debug mode
        socketio.run(app, host=host, port=port, debug=True, use_reloader=True, 
                    log_output=True, allow_unsafe_werkzeug=True)
    else:
        # Run with SocketIO's production server
        socketio.run(app, host=host, port=port, debug=False, 
                    log_output=True, allow_unsafe_werkzeug=True)
