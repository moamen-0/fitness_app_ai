import cv2
from utils import calculate_angle, mp_pose, pose

def squat(sound):
    """
    Track squat exercise
    
    Args:
        sound: Pygame sound object for alerts
        
    Yields:
        Video frames with pose tracking
    """
    counter = 0  # Counter for squats
    state = None  # State for squat position
    cap = cv2.VideoCapture(0)
    sound_playing = False  # Add flag to track sound state
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
            
        # Flip the frame horizontally
        frame = cv2.flip(frame, 1)
        image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = pose.process(image)
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
        
        angle_too_low = False  # Flag to track if angle is too low
        
        if results.pose_landmarks:
            landmarks = results.pose_landmarks.landmark
            
            # Define landmarks for both legs
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
            
            for side, joints in leg_sides.items():
                # Get coordinates for each side
                hip = [
                    landmarks[joints['hip'].value].x,
                    landmarks[joints['hip'].value].y,
                ]
                knee = [
                    landmarks[joints['knee'].value].x,
                    landmarks[joints['knee'].value].y,
                ]
                ankle = [
                    landmarks[joints['ankle'].value].x,
                    landmarks[joints['ankle'].value].y,
                ]
                
                # Convert normalized coordinates to image coordinates
                hip_coords = (int(hip[0] * image.shape[1]), int(hip[1] * image.shape[0]))
                knee_coords = (int(knee[0] * image.shape[1]), int(knee[1] * image.shape[0]))
                ankle_coords = (int(ankle[0] * image.shape[1]), int(ankle[1] * image.shape[0]))
                
                # Draw lines between hip, knee, and ankle
                cv2.line(image, hip_coords, knee_coords, (0, 255, 0), 2)  # Green line
                cv2.line(image, knee_coords, ankle_coords, (0, 255, 0), 2)  # Green line
                
                # Draw circles at hip, knee, and ankle
                cv2.circle(image, hip_coords, 7, (0, 0, 255), -1)  # Red circle
                cv2.circle(image, knee_coords, 7, (0, 0, 255), -1)  # Red circle
                cv2.circle(image, ankle_coords, 7, (0, 0, 255), -1)  # Red circle
                
                # Calculate angles
                knee_angle = calculate_angle(hip, knee, ankle)
                
                # Display angles
                cv2.putText(
                    image,
                    f' {int(knee_angle)}',
                    knee_coords,
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (255, 255, 255),
                    2,
                    cv2.LINE_AA
                )
                
                # Check if the knee angle is less than 70 degrees (90-20)
                if knee_angle < 70:
                    angle_too_low = True
                
                # Check for squat logic
                if knee_angle < 90:
                    state = "down"
                if knee_angle > 160 and state == "down":
                    state = "up"
                    counter += 1
                    print(f'Squat Counter: {counter}')
            
            # Draw counter on the image
            cv2.putText(image, f'Squat Counter: {counter}', (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2, cv2.LINE_AA)
            
            # Handle alert for angle too low
            if angle_too_low:
                # Play alert sound if not already playing
                if not sound_playing:
                    sound.play()
                    sound_playing = True
                
                # Add message with better visibility
                warning_text = "WARNING! Knee angle too low. Adjust your position!"
                text_size = cv2.getTextSize(warning_text, cv2.FONT_HERSHEY_SIMPLEX, 0.8, 2)[0]
                text_x = (image.shape[1] - text_size[0]) // 2
                text_y = image.shape[0] // 2
                
                # Add semi-transparent background for better text visibility
                overlay = image.copy()
                cv2.rectangle(overlay, 
                             (text_x - 10, text_y - text_size[1] - 10),
                             (text_x + text_size[0] + 10, text_y + 10),
                             (0, 0, 0), -1)
                cv2.addWeighted(overlay, 0.5, image, 0.5, 0, image)
                
                # Draw warning text
                cv2.putText(image, warning_text, (text_x, text_y), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2, cv2.LINE_AA)
            else:
                # Stop sound if it was playing
                if sound_playing:
                    sound.stop()
                    sound_playing = False
        
        # Convert the image to JPEG format for streaming
        ret, buffer = cv2.imencode('.jpg', image)
        frame = buffer.tobytes()
        
        # Yield the frame to the Flask response
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')