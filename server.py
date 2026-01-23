from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
import logging

# Disable Flask logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# Clients store
clients = {}

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('connect')
def handle_connect():
    client_id = request.sid
    user_agent = request.headers.get('User-Agent')
    
    device_type = "PC"
    if "Mobile" in user_agent or "Android" in user_agent or "iPhone" in user_agent:
        device_type = "Mobile"
        
    clients[client_id] = {"device": device_type, "ua": user_agent}
    print(f"[Web] New Client Connected: {device_type} ({client_id})")
    emit('status', {'state': 'connected', 'message': 'Connected to Pixel Core'})

@socketio.on('disconnect')
def handle_disconnect():
    if request.sid in clients:
        del clients[request.sid]

def start_server():
    """Starts the Flask-SocketIO server"""
    print("Starting Web Interface on 0.0.0.0:5000")
    socketio.run(app, host='0.0.0.0', port=5000, allow_unsafe_werkzeug=True)

def emit_status(state, text=""):
    """
    Emits a status update to all connected clients.
    States: 'listening', 'processing', 'speaking', 'idle'
    """
    try:
        socketio.emit('pixel_state', {'state': state, 'text': text})
    except Exception as e:
        print(f"Socket Error: {e}")

# Callback for input handling (Text or Audio)
input_callback = None

def set_input_handler(callback):
    global input_callback
    input_callback = callback

@socketio.on('audio_input')
def handle_audio_input(data):
    """
    Receives raw text from Browser Speech Recognition API (Web Speech API).
    Using Web Speech API is faster and easier than streaming raw audio.
    """
    text = data.get('text')
    if text and input_callback:
        print(f"[Web] Received Voice Command: {text}")
        input_callback(text)

def send_notification(target_device, message):
    """
    Sends a notification event to specific devices.
    target_device: 'Mobile', 'PC', or 'All'
    """
    count = 0
    for sid, info in clients.items():
        if target_device == "All" or info['device'] == target_device:
            socketio.emit('notification', {'message': message}, room=sid)
            count += 1
    return count
