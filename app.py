from flask import Flask, Response, render_template, request, jsonify, send_from_directory
from flask_socketio import SocketIO, emit
import cv2
import os
import json
import pygame
import time
import base64
from gtts import gTTS
from flask_cors import CORS
import asyncio
import traceback
from concurrent.futures import ThreadPoolExecutor
import numpy as np
import threading
import datetime

# Import WebRTC processing
from rtc_video_server import process_offer

# Import exercise modules
from utils import calculate_angle
from exercises.bicep_curl import hummer
from exercises.front_raise import dumbbell_front_raise
from exercises.squat import squat
from exercises.triceps_extension import triceps_extension
from exercises.lunges import lunges
from exercises.shoulder_press import shoulder_press
from exercises.plank import plank
from exercises.lateral_raise import side_lateral_raise
from exercises.triceps_kickback import triceps_kickback_side
from exercises.push_ups import push_ups

app = Flask(__name__, static_folder='static')
CORS(app)  # Enable CORS for all routes

# Update SocketIO configuration with proper settings for Cloud Run
try:
    import gevent
except ImportError:
    pass

socketio = SocketIO(
    app, 
    cors_allowed_origins="*",
    async_mode='eventlet',  # Change to eventlet for better Cloud Run compatibility
    ping_timeout=60,      # Longer timeouts for Cloud Run
    ping_interval=25,     # More frequent pings
    engineio_logger=True, # For debugging, set to False in production
    logger=True,
    always_connect=True  # Important for Cloud Run
)

# Setup for async processing
executor = ThreadPoolExecutor()

# Dummy sound class to avoid file path issues
class DummySound:
    def __init__(self):
        self.is_playing = False
    
    def play(self):
        self.is_playing = True
        print("Dummy sound play")
    
    def stop(self):
        self.is_playing = False
        print("Dummy sound stop")

# Use dummy sound instead of loading from a specific path
sound = DummySound()

# Ensure audio directory exists
os.makedirs("audio", exist_ok=True)

# Dictionary to store active sessions
active_sessions = {}

# Dictionary to store exercise functions
exercise_map = {
    'hummer': hummer,
    'front_raise': dumbbell_front_raise,
    'squat': squat,
    'triceps': triceps_extension,
    'lunges': lunges,
    'shoulder_press': shoulder_press,
    'plank': plank,
    'side_lateral_raise': side_lateral_raise,
    'triceps_kickback_side': triceps_kickback_side,
    'push_ups': push_ups
}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/static/<path:path>')
def serve_static(path):
    return send_from_directory('static', path)

# Original endpoint for direct exercise
@app.route('/exercise/<exercise>')
def direct_exercise(exercise):
    valid_exercises = list(exercise_map.keys())
    
    if exercise not in valid_exercises:
        app.logger.error(f"Invalid exercise requested: {exercise}")
        return "Exercise not found", 404
        
    return render_template('websocket_exercise.html', exercise_id=exercise)



#===========================test=============================================== 


# direct_video_fast.html

@app.route('/fast_video/<exercise>')
def fast_video(exercise):
    valid_exercises = [
        "hummer", "front_raise", "squat", "triceps", "lunges", 
        "shoulder_press", "plank", "side_lateral_raise", 
        "triceps_kickback_side", "push_ups"
    ]
    
    if exercise not in valid_exercises:
        app.logger.error(f"Invalid exercise requested: {exercise}")
        return "Exercise not found", 404
        
    return render_template('direct_video_fast.html', exercise_id=exercise)



# direct_video_debug.html

@app.route('/debug_video/<exercise>')
def debug_video(exercise):
    valid_exercises = [
        "hummer", "front_raise", "squat", "triceps", "lunges", 
        "shoulder_press", "plank", "side_lateral_raise", 
        "triceps_kickback_side", "push_ups"
    ]
    
    if exercise not in valid_exercises:
        app.logger.error(f"Invalid exercise requested: {exercise}")
        return "Exercise not found", 404
        
    return render_template('direct_video_debug.html', exercise_id=exercise)




#===========================test=============================================== 














# New endpoint for WebSocket-based exercise viewing
@app.route('/websocket_exercise/<exercise>')
def websocket_exercise(exercise):
    valid_exercises = list(exercise_map.keys())
    
    if exercise not in valid_exercises:
        app.logger.error(f"Invalid exercise requested: {exercise}")
        return "Exercise not found", 404
        
    return render_template('websocket_exercise.html', exercise_id=exercise)

# For backward compatibility
@app.route('/direct_video/<exercise>')
def direct_video(exercise):
    valid_exercises = list(exercise_map.keys())
    
    if exercise not in valid_exercises:
        app.logger.error(f"Invalid exercise requested: {exercise}")
        return "Exercise not found", 404
        
    return render_template('websocket_exercise.html', exercise_id=exercise)

@app.route('/api/rtc_offer', methods=['POST'])
def rtc_offer():
    try:
        data = request.json
        app.logger.info(f"Received WebRTC offer for exercise: {data.get('exercise', 'unknown')}")
        
        # Use ThreadPoolExecutor to handle async processing
        future = executor.submit(asyncio.run, process_offer(data))
        response = future.result()
        
        return jsonify(response)
    except Exception as e:
        app.logger.error(f"Error in rtc_offer: {str(e)}")
        app.logger.error(traceback.format_exc())
        return jsonify({"error": str(e)}), 500

@app.route('/api/exercises', methods=['GET'])
def get_exercises():
    try:
        exercises = [
            {"id": "hummer", "name": "Bicep Curl (Hammer)"},
            {"id": "front_raise", "name": "Dumbbell Front Raise"},
            {"id": "squat", "name": "Squat"},
            {"id": "triceps", "name": "Triceps Extension"},
            {"id": "lunges", "name": "Lunges"},
            {"id": "shoulder_press", "name": "Shoulder Press"},
            {"id": "plank", "name": "Plank"},
            {"id": "side_lateral_raise", "name": "Side Lateral Raise"},
            {"id": "triceps_kickback_side", "name": "Triceps Kickback (Side View)"},
            {"id": "push_ups", "name": "Push Ups"}
        ]
        return jsonify(exercises)
    except Exception as e:
        app.logger.error(f"Error in get_exercises: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/pose_data')
def pose_data():
    try:
        data = {
            "status": "ok",
            "timestamp": time.time(),
            "message": "Pose data API is working"
        }
        return jsonify(data)
    except Exception as e:
        app.logger.error(f"Error in pose_data: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/camera_test')
def camera_test():
    return render_template('camera_test.html')

# Original MJPEG streaming endpoint for backwards compatibility
@app.route('/video_feed/<exercise>')
def video_feed(exercise):
    try:
        if exercise in exercise_map:
            # Add debug logging
            print(f"Starting video feed for exercise: {exercise}")
            
            # Add cache control headers
            return Response(
                exercise_map[exercise](sound), 
                mimetype='multipart/x-mixed-replace; boundary=frame',
                headers={
                    'Cache-Control': 'no-cache, no-store, must-revalidate',
                    'Pragma': 'no-cache',
                    'Expires': '0'
                }
            )
        else:
            return "Invalid exercise", 400
    except Exception as e:
        app.logger.error(f"Error in video_feed: {str(e)}")
        app.logger.error(traceback.format_exc())
        return "Error processing video", 500

# ====================== WebSocket Event Handlers ======================

@socketio.on('connect')
def handle_connect():
    print(f"Client connected: {request.sid}")
    emit('connection_status', {'status': 'connected', 'session_id': request.sid})

@socketio.on('disconnect')
def handle_disconnect():
    print(f"Client disconnected: {request.sid}")
    # Clean up any active session on disconnect
    if request.sid in active_sessions:
        session_data = active_sessions[request.sid]
        if 'stop_event' in session_data:
            session_data['stop_event'].set()
        if 'cap' in session_data and session_data['cap'] is not None:
            session_data['cap'].release()
        del active_sessions[request.sid]

@socketio.on('start_exercise')
def handle_start_exercise(data):
    try:
        exercise_id = data.get('exercise_id')
        print(f"Starting exercise: {exercise_id} for session {request.sid}")
        
        if not exercise_id or exercise_id not in exercise_map:
            emit('error', {'message': f'Invalid exercise: {exercise_id}'})
            return
        
        # Stop any currently active session
        if request.sid in active_sessions:
            session_data = active_sessions[request.sid]
            if 'stop_event' in session_data:
                session_data['stop_event'].set()
            if 'cap' in session_data and session_data['cap'] is not None:
                session_data['cap'].release()
        
        # Create a stop event to allow safe termination
        stop_event = threading.Event()
        
        # Store session data
        active_sessions[request.sid] = {
            'exercise_id': exercise_id,
            'stop_event': stop_event,
            'cap': None,
            'left_counter': 0,
            'right_counter': 0
        }
        
        # Start a thread to process the exercise
        exercise_thread = threading.Thread(
            target=process_exercise_frames,
            args=(request.sid, exercise_id, stop_event)
        )
        exercise_thread.daemon = True
        exercise_thread.start()
        
        emit('exercise_started', {'exercise_id': exercise_id})
        
    except Exception as e:
        print(f"Error starting exercise: {str(e)}")
        traceback.print_exc()
        emit('error', {'message': f'Error starting exercise: {str(e)}'})

@socketio.on('stop_exercise')
def handle_stop_exercise():
    try:
        print(f"Stopping exercise for session {request.sid}")
        
        if request.sid in active_sessions:
            session_data = active_sessions[request.sid]
            if 'stop_event' in session_data:
                session_data['stop_event'].set()
            if 'cap' in session_data and session_data['cap'] is not None:
                session_data['cap'].release()
            
        emit('exercise_stopped')
        
    except Exception as e:
        print(f"Error stopping exercise: {str(e)}")
        emit('error', {'message': f'Error stopping exercise: {str(e)}'})

def process_exercise_frames(session_id, exercise_id, stop_event):
    """
    Process exercise frames and send them via WebSocket
    
    Args:
        session_id: WebSocket session ID
        exercise_id: ID of the exercise to track
        stop_event: Event to signal when to stop processing
    """
    try:
        print(f"Processing exercise frames for {exercise_id}, session {session_id}")
        
        # Initialize video capture
        cap = cv2.VideoCapture(0)
        
        if not cap.isOpened():
            print("Failed to open camera")
            socketio.emit('error', {'message': 'Failed to open camera'}, room=session_id)
            return
        
        # Update session data
        active_sessions[session_id]['cap'] = cap
        
        # Initial variables
        left_counter = 0
        right_counter = 0
        left_state = None
        right_state = None
        
        while not stop_event.is_set():
            ret, frame = cap.read()
            if not ret:
                print("Failed to capture frame")
                break
            
            # Flip the frame horizontally
            frame = cv2.flip(frame, 1)
            
            # Convert to RGB for mediapipe
            image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = pose.process(image)
            image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
            
            # Exercise variables
            form_feedback = ""
            
            if results.pose_landmarks:
                landmarks = results.pose_landmarks.landmark
                
                # Draw the pose landmarks
                mp_drawing.draw_landmarks(
                    image, 
                    results.pose_landmarks, 
                    mp_pose.POSE_CONNECTIONS,
                    mp_drawing.DrawingSpec(color=(245, 117, 66), thickness=2, circle_radius=4),
                    mp_drawing.DrawingSpec(color=(245, 66, 230), thickness=2, circle_radius=2)
                )
                
                # Define arm landmarks for exercise tracking
                arm_sides = {
                    'left': {
                        'shoulder': mp_pose.PoseLandmark.LEFT_SHOULDER,
                        'elbow': mp_pose.PoseLandmark.LEFT_ELBOW,
                        'wrist': mp_pose.PoseLandmark.LEFT_WRIST,
                        'hip': mp_pose.PoseLandmark.LEFT_HIP
                    },
                    'right': {
                        'shoulder': mp_pose.PoseLandmark.RIGHT_SHOULDER,
                        'elbow': mp_pose.PoseLandmark.RIGHT_ELBOW,
                        'wrist': mp_pose.PoseLandmark.RIGHT_WRIST,
                        'hip': mp_pose.PoseLandmark.RIGHT_HIP
                    }
                }
                
                # Track angles and exercise state
                for side, joints in arm_sides.items():
                    shoulder = [
                        landmarks[joints['shoulder'].value].x,
                        landmarks[joints['shoulder'].value].y,
                    ]
                    elbow = [
                        landmarks[joints['elbow'].value].x,
                        landmarks[joints['elbow'].value].y,
                    ]
                    wrist = [
                        landmarks[joints['wrist'].value].x,
                        landmarks[joints['wrist'].value].y,
                    ]
                    
                    # Calculate elbow angle
                    elbow_angle = calculate_angle(shoulder, elbow, wrist)
                    
                    # Display angle on frame
                    cv2.putText(
                        image,
                        f'{int(elbow_angle)}',
                        tuple(np.multiply(elbow, [image.shape[1], image.shape[0]]).astype(int)),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.5,
                        (255, 255, 255),
                        2,
                        cv2.LINE_AA
                    )
                    
                    # Exercise specific logic - using hammer curl as an example
                    if exercise_id == 'hummer':
                        if side == 'left':
                            if elbow_angle > 160:
                                left_state = 'down'
                            if elbow_angle < 30 and left_state == 'down':
                                left_state = 'up'
                                left_counter += 1
                                print(f'Left Counter: {left_counter}')
                                form_feedback = "جيد! استمر"
                        
                        if side == 'right':
                            if elbow_angle > 160:
                                right_state = 'down'
                            if elbow_angle < 30 and right_state == 'down':
                                right_state = 'up'
                                right_counter += 1
                                print(f'Right Counter: {right_counter}')
                                form_feedback = "ممتاز! استمر"
                    
                    # (Add more exercise-specific logic here for other exercises)
                
                # Display counters on frame
                cv2.putText(image, f'Left: {left_counter}', (10, 50), 
                         cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2, cv2.LINE_AA)
                cv2.putText(image, f'Right: {right_counter}', (10, 100), 
                         cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2, cv2.LINE_AA)
                
                # Update session counters
                active_sessions[session_id]['left_counter'] = left_counter
                active_sessions[session_id]['right_counter'] = right_counter
                
            # Convert frame to base64 for WebSocket transmission
            ret, buffer = cv2.imencode('.jpg', image)
            frame_data = base64.b64encode(buffer).decode('utf-8')
            
            # Send frame and data
            socketio.emit('exercise_frame', {
                'frame': frame_data,
                'left_counter': left_counter,
                'right_counter': right_counter,
                'feedback': form_feedback
            }, room=session_id)
            
            # Short delay to reduce CPU usage
            time.sleep(0.03)  # ~30 fps
        
        # Clean up camera when done
        if cap.isOpened():
            cap.release()
        
        print(f"Exercise processing stopped for session {session_id}")
        
    except Exception as e:
        print(f"Error in process_exercise_frames: {str(e)}")
        traceback.print_exc()
        socketio.emit('error', {'message': f'Error processing exercise: {str(e)}'}, room=session_id)
        
        # Cleanup
        if session_id in active_sessions:
            session_data = active_sessions[session_id]
            if 'cap' in session_data and session_data['cap'] is not None:
                session_data['cap'].release()

@app.route('/socket-health')
def socket_health():
    return {
        'status': 'online',
        'socketio_version': socketio.__version__,
        'timestamp': datetime.datetime.now().isoformat()
    }

@app.route('/socket-diagnostic')
def socket_diagnostic():
    """Diagnostic endpoint to check Socket.IO configuration"""
    socketio_config = {
        'async_mode': socketio.async_mode,
        'cors_allowed_origins': socketio.cors_allowed_origins,
        'ping_timeout': socketio.ping_timeout,
        'ping_interval': socketio.ping_interval,
    }
    
    return {
        'status': 'online',
        'socketio_version': socketio.__version__,
        'socketio_config': socketio_config,
        'timestamp': datetime.datetime.now().isoformat(),
        'environment': os.environ.get('GAE_ENV', 'not-on-app-engine')
    }

@app.route('/api/long-poll/<exercise_id>', methods=['GET'])
def long_poll_exercise(exercise_id):
    """Fallback HTTP long polling endpoint for environments where WebSockets don't work"""
    try:
        # Simple validation
        if not exercise_id or exercise_id not in [exercise['id'] for exercise in get_exercises().json]:
            return jsonify({"error": "Invalid exercise ID"}), 400
            
        # Generate a frame
        frame_data = generate_exercise_frame(exercise_id)
        
        return jsonify(frame_data)
    except Exception as e:
        print(f"Error in long polling: {str(e)}")
        return jsonify({"error": str(e)}), 500

def generate_exercise_frame(exercise_id):
    """Generate a single exercise frame for long polling"""
    # This is a simplified version - in a real app, you'd use the same
    # logic as in your WebSocket code to generate a frame
    return {
        "frame": None,  # No frame in test mode
        "left_counter": 0,
        "right_counter": 0, 
        "feedback": "HTTP polling fallback active",
        "timestamp": datetime.datetime.now().isoformat()
    }

@app.route('/api/socketio-config')
def socketio_config():
    """Detailed diagnostic endpoint for Socket.IO configuration"""
    config = {
        "version": socketio.__version__,
        "async_mode": socketio.async_mode,
        "cors_allowed_origins": socketio.cors_allowed_origins if hasattr(socketio, 'cors_allowed_origins') else "Not set",
        "ping_timeout": socketio.ping_timeout if hasattr(socketio, 'ping_timeout') else "Not set",
        "ping_interval": socketio.ping_interval if hasattr(socketio, 'ping_interval') else "Not set",
        "handlers": list(socketio.handlers.keys()) if hasattr(socketio, 'handlers') else [],
        "environment": {
            "GAE_ENV": os.environ.get('GAE_ENV', 'not-set'),
            "PORT": os.environ.get('PORT', 'not-set'),
            "K_SERVICE": os.environ.get('K_SERVICE', 'not-set'),
            "PYTHONPATH": os.environ.get('PYTHONPATH', 'not-set')
        },
        "server": request.headers.get('Host', 'unknown')
    }
    return jsonify(config)

@app.after_request
def add_cors_headers(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    # These are critical for WebSocket
    response.headers.add('Access-Control-Allow-Credentials', 'true')
    return response

if __name__ == '__main__':
    # Initialize mediapipe
    try:
        import mediapipe as mp
        print(f"Mediapipe loaded successfully")
        
        # Initialize pose
        mp_drawing = mp.solutions.drawing_utils
        mp_pose = mp.solutions.pose
        pose = mp_pose.Pose(
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
            model_complexity=1  # Medium complexity for balance between performance and accuracy
        )
        print("Pose model initialized successfully")
    except Exception as e:
        print(f"Error initializing libraries: {e}")
    
    port = int(os.environ.get('PORT', 8080))
    print(f"Starting server on port {port}")
    socketio.run(
        app, 
        host='0.0.0.0', 
        port=port,
        debug=os.environ.get('DEBUG', 'False').lower() == 'true',
        allow_unsafe_werkzeug=True  # Required for eventlet/gevent in newer Flask versions
    )