# Cloud Run entry point
from app import app, socketio

# Load mediapipe at module level for Cloud compatibility
import mediapipe as mp
mp_drawing = mp.solutions.drawing_utils
mp_pose = mp.solutions.pose
pose = mp_pose.Pose(
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5,
    model_complexity=1
)

# This makes the global variables available to the app module
from app import _setup_global_variables
_setup_global_variables(mp_drawing, mp_pose, pose)

# For Cloud Run deployment - WSGI application
application = socketio.middleware(app)

if __name__ == "__main__":
    # Development server
    import os
    port = int(os.environ.get('PORT', 8080))
    socketio.run(
        app,
        host='0.0.0.0',
        port=port,
        debug=False, 
        use_reloader=False,
        cors_allowed_origins="*"
    )
