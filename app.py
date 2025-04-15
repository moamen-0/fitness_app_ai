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

# Configure Socket.IO with settings optimized for App Engine
socketio = SocketIO(
    app,
    cors_allowed_origins="*",
    async_mode='eventlet',
    engineio_logger=True,  # Enable logging for debugging
    logger=True,
    ping_interval=int(os.environ.get('SOCKETIO_PING_INTERVAL', 25)),
    ping_timeout=int(os.environ.get('SOCKETIO_PING_TIMEOUT', 60)),
    # Force long-polling as first transport for App Engine compatibility
    transports=['polling', 'websocket']
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

# Global variables that will be initialized later
mp_drawing = None
mp_pose = None
pose = None

def _setup_global_variables(drawing, pose_lib, pose_instance):
    """Set up global variables for use in the app"""
    global mp_drawing, mp_pose, pose
    mp_drawing = drawing
    mp_pose = pose_lib
    pose = pose_instance
    print("Global mediapipe variables initialized successfully")

@app.route('/')
def index():
    try:
        # Basic health check information
        health_info = {
            "status": "ok",
            "app": "Fitness App",
            "version": "1.0.0",
            "environment": os.environ.get('GAE_ENV', 'local'),
            "instance": os.environ.get('GAE_INSTANCE', 'local')
        }
        # Log the health check
        app.logger.info(f"Health check performed: {health_info}")
        
        # Try to render the template with health info
        try:
            return render_template('index.html', health_info=health_info)
        except Exception as template_error:
            # If template rendering fails, return a simple HTML response
            app.logger.error(f"Template error: {str(template_error)}")
            return f"""
            <!DOCTYPE html>
            <html>
            <head><title>Fitness App</title></head>
            <body>
                <h1>Fitness App is Running</h1>
                <p>Server is operational, but there was an error with the template.</p>
                <p>Environment: {os.environ.get('GAE_ENV', 'local')}</p>
                <p>Instance: {os.environ.get('GAE_INSTANCE', 'local')}</p>
                <p><a href="/websocket_test">WebSocket Test</a></p>
            </body>
            </html>
            """
    except Exception as e:
        app.logger.error(f"Error in index route: {str(e)}")
        # Return a simple text response in case of an error
        return f"App is running, but encountered an error: {str(e)}", 500

@app.route('/healthz')
def health_check():
    return jsonify({"status": "ok", "message": "Service is running"})

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
        
    return render_template('direct_exercise.html', exercise_id=exercise)

@app.route('/fast_video/<exercise>')
def fast_video(exercise):
    valid_exercises = list(exercise_map.keys())
    
    if exercise not in valid_exercises:
        app.logger.error(f"Invalid exercise requested: {exercise}")
        return "Exercise not found", 404
        
    return render_template('direct_video_fast.html', exercise_id=exercise)

@app.route('/debug_video/<exercise>')
def debug_video(exercise):
    valid_exercises = list(exercise_map.keys())
    
    if exercise not in valid_exercises:
        app.logger.error(f"Invalid exercise requested: {exercise}")
        return "Exercise not found", 404
        
    return render_template('direct_video_debug.html', exercise_id=exercise)

@app.route('/websocket_exercise/<exercise>')
def websocket_exercise(exercise):
    valid_exercises = list(exercise_map.keys())
    
    if exercise not in valid_exercises:
        app.logger.error(f"Invalid exercise requested: {exercise}")
        return "Exercise not found", 404
        
    return render_template('websocket_exercise.html', exercise_id=exercise)

@app.route('/direct_video/<exercise>')
def direct_video(exercise):
    valid_exercises = list(exercise_map.keys())
    
    if exercise not in valid_exercises:
        app.logger.error(f"Invalid exercise requested: {exercise}")
        return "Exercise not found", 404
        
    return render_template('direct_video.html', exercise_id=exercise)

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

@app.route('/video_feed/<exercise>')
def video_feed(exercise):
    try:
        if exercise in exercise_map:
            print(f"Starting video feed for exercise: {exercise}")
            
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

@socketio.on('connect')
def handle_connect():
    print(f"Client connected: {request.sid}")
    emit('connection_status', {'status': 'connected', 'session_id': request.sid})

@socketio.on('disconnect')
def handle_disconnect():
    print(f"Client disconnected: {request.sid}")
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
        client_stream = data.get('client_stream', False)
        session_id = request.sid
        
        print(f"Starting exercise {exercise_id} for session {session_id}, client streaming: {client_stream}")
        
        if session_id not in active_sessions:
            active_sessions[session_id] = {
                'exercise_id': exercise_id,
                'left_counter': 0,
                'right_counter': 0,
                'client_stream': client_stream,
                'stop_event': threading.Event(),
                'last_frame': None,
                'cap': None
            }
        else:
            active_sessions[session_id]['exercise_id'] = exercise_id
            active_sessions[session_id]['left_counter'] = 0
            active_sessions[session_id]['right_counter'] = 0
            active_sessions[session_id]['client_stream'] = client_stream
            active_sessions[session_id]['stop_event'].clear()
        
        emit('exercise_started', {'status': 'ok', 'exercise_id': exercise_id})
        
        if not client_stream:
            stop_event = active_sessions[session_id]['stop_event']
            processing_thread = threading.Thread(
                target=process_exercise_frames,
                args=(session_id, exercise_id, stop_event)
            )
            processing_thread.daemon = True
            processing_thread.start()
    except Exception as e:
        print(f"Error in handle_start_exercise: {str(e)}")
        emit('error', {'message': f'Failed to start exercise: {str(e)}'})

@socketio.on('video_frame')
def handle_video_frame(data):
    try:
        session_id = request.sid
        if session_id not in active_sessions:
            return
        
        frame_b64 = data.get('frame')
        if not frame_b64:
            return
        
        img_data = base64.b64decode(frame_b64)
        np_arr = np.frombuffer(img_data, np.uint8)
        frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        
        if frame is None:
            print("Invalid frame received")
            return
        
        active_sessions[session_id]['last_frame'] = frame
        
        process_client_frame(session_id, frame)
    except Exception as e:
        print(f"Error processing video frame: {str(e)}")
        traceback.print_exc()

def process_client_frame(session_id, frame):
    try:
        if session_id not in active_sessions:
            return
        
        session_data = active_sessions[session_id]
        exercise_id = session_data['exercise_id']
        left_counter = session_data.get('left_counter', 0)
        right_counter = session_data.get('right_counter', 0)
        
        image = frame.copy()
        
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        results = pose.process(image_rgb)
        
        form_feedback = ""
        
        if results.pose_landmarks:
            mp_drawing.draw_landmarks(
                image, 
                results.pose_landmarks, 
                mp_pose.POSE_CONNECTIONS,
                mp_drawing.DrawingSpec(color=(245, 117, 66), thickness=2, circle_radius=4),
                mp_drawing.DrawingSpec(color=(245, 66, 230), thickness=2, circle_radius=2)
            )
            
            landmarks = results.pose_landmarks.landmark
            
            arm_sides = {
                'left': {
                    'shoulder': mp_pose.PoseLandmark.LEFT_SHOULDER,
                    'elbow': mp_pose.PoseLandmark.LEFT_ELBOW,
                    'wrist': mp_pose.PoseLandmark.LEFT_WRIST
                },
                'right': {
                    'shoulder': mp_pose.PoseLandmark.RIGHT_SHOULDER,
                    'elbow': mp_pose.PoseLandmark.RIGHT_ELBOW,
                    'wrist': mp_pose.PoseLandmark.RIGHT_WRIST
                }
            }
            
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
                
                elbow_angle = calculate_angle(shoulder, elbow, wrist)
                
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
                
                if exercise_id == 'hummer':
                    if side == 'left':
                        if elbow_angle > 160:
                            if active_sessions[session_id].get('left_state') != 'down':
                                active_sessions[session_id]['left_state'] = 'down'
                        if elbow_angle < 30:
                            if active_sessions[session_id].get('left_state') == 'down':
                                left_counter += 1
                                active_sessions[session_id]['left_counter'] = left_counter
                                active_sessions[session_id]['left_state'] = 'up'
                                form_feedback = "Good form! Keep going"
                    else:
                        if elbow_angle > 160:
                            if active_sessions[session_id].get('right_state') != 'down':
                                active_sessions[session_id]['right_state'] = 'down'
                        if elbow_angle < 30:
                            if active_sessions[session_id].get('right_state') == 'down':
                                right_counter += 1
                                active_sessions[session_id]['right_counter'] = right_counter
                                active_sessions[session_id]['right_state'] = 'up'
                                form_feedback = "Good form! Keep going"
        
        cv2.putText(image, f'Left: {left_counter}', (10, 50), 
                     cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2, cv2.LINE_AA)
        cv2.putText(image, f'Right: {right_counter}', (10, 100), 
                     cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2, cv2.LINE_AA)
        
        ret, buffer = cv2.imencode('.jpg', image)
        frame_data = base64.b64encode(buffer).decode('utf-8')
        
        socketio.emit('exercise_frame', {
            'frame': frame_data,
            'left_counter': left_counter,
            'right_counter': right_counter,
            'feedback': form_feedback
        }, room=session_id)
        
    except Exception as e:
        print(f"Error in process_client_frame: {str(e)}")
        traceback.print_exc()

def process_exercise_frames(session_id, exercise_id, stop_event):
    try:
        print(f"Processing exercise frames for {exercise_id}, session {session_id}")
        
        cap = cv2.VideoCapture(0)
        
        if not cap.isOpened():
            print("Failed to open camera")
            socketio.emit('error', {'message': 'Failed to open camera'}, room=session_id)
            return
        
        active_sessions[session_id]['cap'] = cap
        
        left_counter = 0
        right_counter = 0
        left_state = None
        right_state = None
        
        while not stop_event.is_set():
            ret, frame = cap.read()
            if not ret:
                print("Failed to capture frame")
                break
            
            frame = cv2.flip(frame, 1)
            
            image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = pose.process(image)
            image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
            
            form_feedback = ""
            
            if results.pose_landmarks:
                landmarks = results.pose_landmarks.landmark
                
                mp_drawing.draw_landmarks(
                    image, 
                    results.pose_landmarks, 
                    mp_pose.POSE_CONNECTIONS,
                    mp_drawing.DrawingSpec(color=(245, 117, 66), thickness=2, circle_radius=4),
                    mp_drawing.DrawingSpec(color=(245, 66, 230), thickness=2, circle_radius=2)
                )
                
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
                    
                    elbow_angle = calculate_angle(shoulder, elbow, wrist)
                    
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
                    
                cv2.putText(image, f'Left: {left_counter}', (10, 50), 
                         cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2, cv2.LINE_AA)
                cv2.putText(image, f'Right: {right_counter}', (10, 100), 
                         cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2, cv2.LINE_AA)
                
                active_sessions[session_id]['left_counter'] = left_counter
                active_sessions[session_id]['right_counter'] = right_counter
                    
            ret, buffer = cv2.imencode('.jpg', image)
            frame_data = base64.b64encode(buffer).decode('utf-8')
            
            socketio.emit('exercise_frame', {
                'frame': frame_data,
                'left_counter': left_counter,
                'right_counter': right_counter,
                'feedback': form_feedback
            }, room=session_id)
            
            time.sleep(0.03)
        
        if cap.isOpened():
            cap.release()
            
        print(f"Exercise processing stopped for session {session_id}")
    except Exception as e:
        print(f"Error in process_exercise_frames: {str(e)}")
        traceback.print_exc()
        socketio.emit('error', {'message': f'Error processing exercise: {str(e)}'}, room=session_id)
        
        if session_id in active_sessions:
            session_data = active_sessions[session_id]
            if 'cap' in session_data and session_data['cap'] is not None:
                session_data['cap'].release()

@app.route('/websocket_test')
def websocket_test():
    return render_template('websocket_test.html')

@socketio.on('ping')
def handle_ping(data):
    try:
        print(f"Received ping from client: {data}")
        emit('pong', {
            'server_time': time.time(),
            'message': 'Pong from server',
            'received_data': data
        })
    except Exception as e:
        print(f"Error in handle_ping: {str(e)}")
        emit('error', {'message': f'Error handling ping: {str(e)}'})

if __name__ == '__main__':
    # Only run this for local development
    try:
        # Initialize mediapipe locally if running this file directly
        import mediapipe as mp
        print(f"Mediapipe loaded successfully")
        
        mp_drawing = mp.solutions.drawing_utils
        mp_pose = mp.solutions.pose
        pose = mp_pose.Pose(
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
            model_complexity=1
        )
        print("Pose model initialized successfully")
    except Exception as e:
        print(f"Error initializing libraries: {e}")
    
    port = int(os.environ.get('PORT', 8080))
    
    socketio.run(
        app, 
        host='0.0.0.0', 
        port=port,
        debug=False,
        use_reloader=False,
        cors_allowed_origins="*",
        allow_unsafe_werkzeug=True
    )