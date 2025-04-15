import cv2
from utils import calculate_angle, mp_pose, pose

def lunges(sound):
    """
    Track lunges exercise
    
    Args:
        sound: Pygame sound object for alerts
        
    Yields:
        Video frames with pose tracking
    """
    left_counter = 0
    right_counter = 0
    left_stage = None
    right_stage = None
    cap = cv2.VideoCapture(0)
    sound_playing = False
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
            
        # Flip the frame horizontally
        frame = cv2.flip(frame, 1)
        image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = pose.process(image)
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
        
        form_violated = False
        
        if results.pose_landmarks:
            landmarks = results.pose_landmarks.landmark
            
            # Get leg landmarks for both legs
            leg_sides = {
                'left': {
                    'hip': mp_pose.PoseLandmark.LEFT_HIP,
                    'knee': mp_pose.PoseLandmark.LEFT_KNEE,
                    'ankle': mp_pose.PoseLandmark.LEFT_ANKLE
                },
                'right': {
                    'hip': mp_pose.PoseLandmark.RIGHT_HIP,
                    'knee': mp_pose.PoseLandmark.RIGHT_KNEE,
                    'ankle': mp_pose.PoseLandmark.RIGHT_ANKLE
                }
            }
            
            # Get coordinates for shoulders to check torso alignment
            left_shoulder = [
                landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].x,
                landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].y
            ]
            right_shoulder = [
                landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value].x,
                landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value].y
            ]
            
            # Draw