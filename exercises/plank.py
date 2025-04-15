import cv2
from utils import calculate_angle, mp_pose, pose

def plank(sound):
    """
    Track plank exercise and monitor duration with proper form
    
    Args:
        sound: Pygame sound object for alerts
        
    Yields:
        Video frames with pose tracking
    """
    cap = cv2.VideoCapture(0)
    plank_start_time = None
    plank_duration = 0
    correct_posture = False
    sound_playing = False
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
            
        # Flip frame horizontally
        frame = cv2.flip(frame, 1)
        image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = pose.process(image)
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
        
        if results.pose_landmarks:
            landmarks = results.pose_landmarks.landmark
            
            # Get important landmarks for plank
            left_shoulder = [landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].x, 
                             landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].y]
            right_shoulder = [landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value].x, 
                              landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value].y]
            left_hip = [landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].x, 
                        landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].y]
            right_hip = [landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value].x, 
                         landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value].y]
            left_ankle = [landmarks[mp_pose.PoseLandmark.LEFT_ANKLE.value].x, 
                          landmarks[mp_pose.PoseLandmark.LEFT_ANKLE.value].y]
            right_ankle = [landmarks[mp_pose.PoseLandmark.RIGHT_ANKLE.value].x, 
                           landmarks[mp_pose.PoseLandmark.RIGHT_ANKLE.value].y]
            left_knee = [landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value].x, 
                         landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value].y]
            right_knee = [landmarks[mp_pose.PoseLandmark.RIGHT_KNEE.value].x, 
                          landmarks[mp_pose.PoseLandmark.RIGHT_KNEE.value].y]
            
            # Convert to pixel coordinates
            left_shoulder_coords = (int(left_shoulder[0] * image.shape[1]), int(left_shoulder[1] * image.shape[0]))
            right_shoulder_coords = (int(right_shoulder[0] * image.shape[1]), int(right_shoulder[1] * image.shape[0]))
            left_hip_coords = (int(left_hip[0] * image.shape[1]), int(left_hip[1] * image.shape[0]))
            right_hip_coords = (int(right_hip[0] * image.shape[1]), int(right_hip[1] * image.shape[0]))
            left_ankle_coords = (int(left_ankle[0] * image.shape[1]), int(left_ankle[1] * image.shape[0]))
            right_ankle_coords = (int(right_ankle[0] * image.shape[1]), int(right_ankle[1] * image.shape[0]))
            left_knee_coords = (int(left_knee[0] * image.shape[1]), int(left_knee[1] * image.shape[0]))
            right_knee_coords = (int(right_knee[0] * image.shape[1]), int(right_knee[1] * image.shape[0]))
            
            # Draw body lines
            cv2.line(image, left_shoulder_coords, left_hip_coords, (0, 255, 0), 2)
            cv2.line(image, right_shoulder_coords, right_hip_coords, (0, 255, 0), 2)
            cv2.line(image, left_hip_coords, left_knee_coords, (0, 255, 0), 2)
            cv2.line(image, right_hip_coords, right_knee_coords, (0, 255, 0), 2)
            cv2.line(image, left_knee_coords, left_ankle_coords, (0, 255, 0), 2)
            cv2.line(image, right_knee_coords, right_ankle_coords, (0, 255, 0), 2)
            cv2.line(image, left_shoulder_coords, right_shoulder_coords, (0, 255, 255), 2)
            cv2.line(image, left_hip_coords, right_hip_coords, (0, 255, 255), 2)
            
            # Draw joints
            for point in [left_shoulder_coords, right_shoulder_coords, left_hip_coords, right_hip_coords, 
                          left_ankle_coords, right_ankle_coords, left_knee_coords, right_knee_coords]:
                cv2.circle(image, point, 7, (0, 0, 255), -1)
            
            # Calculate important angles for plank form check
            # Body angle (shoulder-hip-ankle)
            left_body_angle = calculate_angle(left_shoulder, left_hip, left_ankle)
            right_body_angle = calculate_angle(right_shoulder, right_hip, right_ankle)
            
            # Knee angle (hip-knee-ankle)
            left_knee_angle = calculate_angle(left_hip, left_knee, left_ankle)
            right_knee_angle = calculate_angle(right_hip, right_knee, right_ankle)
            
            # Display angles
            cv2.putText(image, f'Body Angle L: {int(left_body_angle)}', (10, 150), 
                      cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2, cv2.LINE_AA)
            cv2.putText(image, f'Body Angle R: {int(right_body_angle)}', (10, 180),
                      cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2, cv2.LINE_AA)
            cv2.putText(image, f'Knee Angle L: {int(left_knee_angle)}', (10, 210),
                      cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2, cv2.LINE_AA)
            cv2.putText(image, f'Knee Angle R: {int(right_knee_angle)}', (10, 240),
                      cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2, cv2.LINE_AA)
            
            # Check plank form
            # In proper plank: body angle should be close to 180° (straight)
            # Knee angle should also be close to 180° (straight legs)
            
            # Set angle thresholds
            body_angle_min = 160  # Minimum body straightness angle
            knee_angle_min = 160  # Minimum knee straightness angle
            
            # Check form
            if (left_body_angle > body_angle_min and right_body_angle > body_angle_min and
                left_knee_angle > knee_angle_min and right_knee_angle > knee_angle_min):
                correct_posture = True
                # Start timer if not already started
                if plank_start_time is None:
                    plank_start_time = cv2.getTickCount()
                
                # Stop sound if playing
                if sound_playing:
                    sound.stop()
                    sound_playing = False
                    
                # Calculate duration
                current_time = cv2.getTickCount()
                elapsed_time = (current_time - plank_start_time) / cv2.getTickFrequency()
                plank_duration = elapsed_time
                
            else:
                correct_posture = False
                # Reset timer when form breaks
                plank_start_time = None
                
                # Play sound alert if not already playing
                if not sound_playing:
                    sound.play()
                    sound_playing = True
            
            # Display status and time
            status_text = "Correct Posture" if correct_posture else "Incorrect Posture"
            status_color = (0, 255, 0) if correct_posture else (0, 0, 255)  # Green for correct, red for incorrect
            
            cv2.putText(image, status_text, (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, status_color, 2, cv2.LINE_AA)
            
            # Display time only if posture is correct
            if correct_posture:
                minutes = int(plank_duration // 60)
                seconds = int(plank_duration % 60)
                cv2.putText(image, f'Time: {minutes:02d}:{seconds:02d}', (10, 100),
                          cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2, cv2.LINE_AA)
        
        # Convert to JPEG for streaming
        ret, buffer = cv2.imencode('.jpg', image)
        frame = buffer.tobytes()
        
        # Yield frame for Flask response
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')