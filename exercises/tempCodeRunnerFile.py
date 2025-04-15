import cv2
from utils import calculate_angle, mp_pose, pose

def dumbbell_front_raise(sound):
    """
    Track dumbbell front raise exercise
    
    Args:
        sound: Pygame sound object for alerts
        
    Yields:
        Video frames with pose tracking
    """
    left_counter = 0
    right_counter = 0
    left_state = "down"
    right_state = "down"
    cap = cv2.VideoCapture(0)
    sound_playing = False  # Add flag to track if sound is playing

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        # Flip the frame horizontally
        frame = cv2.flip(frame, 1)
        image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = pose.process(image)
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

        if results.pose_landmarks:
            landmarks = results.pose_landmarks.landmark

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

            arm_angle_violated = False

            for side, joints in arm_sides.items():
                shoulder = landmarks[joints['shoulder'].value]
                elbow = landmarks[joints['elbow'].value]
                wrist = landmarks[joints['wrist'].value]
                hip = landmarks[joints['hip'].value]

                shoulder_coords = (int(shoulder.x * image.shape[1]), int(shoulder.y * image.shape[0]))
                elbow_coords = (int(elbow.x * image.shape[1]), int(elbow.y * image.shape[0]))
                wrist_coords = (int(wrist.x * image.shape[1]), int(wrist.y * image.shape[0]))
                hip_coords = (int(hip.x * image.shape[1]), int(hip.y * image.shape[0]))

                cv2.line(image, shoulder_coords, elbow_coords, (0, 255, 0), 2)
                cv2.line(image, elbow_coords, wrist_coords, (0, 255, 0), 2)
                cv2.line(image, hip_coords, shoulder_coords, (0, 255, 0), 2)

                for point in [shoulder_coords, elbow_coords, wrist_coords, hip_coords]:
                    cv2.circle(image, point, 7, (0, 0, 255), -1)

                elbow_angle = calculate_angle([shoulder.x, shoulder.y], [elbow.x, elbow.y], [wrist.x, wrist.y])
                shoulder_angle = calculate_angle([hip.x, hip.y], [shoulder.x, shoulder.y], [elbow.x, elbow.y])

                cv2.putText(image, f'{int(elbow_angle)}', elbow_coords, cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
                cv2.putText(image, f'{int(shoulder_angle)}', shoulder_coords, cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)

                # Check if shoulder angle exceeds 160 degrees and mark as violated
                if shoulder_angle > 150:
                    arm_angle_violated = True
                    # Highlight the angle in red to indicate violation
                    cv2.putText(image, f'{int(shoulder_angle)}', shoulder_coords, 
                              cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)

                wrist_x = wrist.x * image.shape[1]
                shoulder_x = shoulder.x * image.shape[1]
                wrist_y = wrist.y * image.shape[0]
                shoulder_y = shoulder.y * image.shape[0]

                # ==== تعديل حساب العدّة ====
                if side == 'left':
                    if elbow_angle >= 110 and left_state == "down":
                        if wrist.y < shoulder.y and 30 < abs(wrist_x - shoulder_x) < 100:
                            left_state = "up"
                            left_counter += 1
                    elif elbow_angle > 160 and wrist.y > shoulder.y and left_state == "up":
                        left_state = "down"

                elif side == 'right':
                    if elbow_angle >= 110 and right_state == "down":
                        if wrist.y < shoulder.y and 30 < abs(wrist_x - shoulder_x) < 100:
                            right_state = "up"
                            right_counter += 1
                    elif elbow_angle > 160 and wrist.y > shoulder.y and right_state == "up":
                        right_state = "down"

            # Control the sound alert
            if arm_angle_violated and not sound_playing:
                sound.play()
                sound_playing = True
            elif not arm_angle_violated and sound_playing:
                sound.stop()
                sound_playing = False
            
            # Display instruction message whenever the angle is violated (while alert is active)
            if sound_playing:
                # Add instruction message to lower arms when angle is too high
                # Centered text with background for better visibility
                text = "LOWER YOUR ARM!"
                text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 1, 2)[0]
                text_x = (image.shape[1] - text_size[0]) // 2
                text_y = image.shape[0] // 2
                
                # Draw semi-transparent background for text
                overlay = image.copy()
                cv2.rectangle(overlay, 
                             (text_x - 10, text_y - text_size[1] - 10),
                             (text_x + text_size[0] + 10, text_y + 10),
                             (0, 0, 0), -1)
                cv2.addWeighted(overlay, 0.5, image, 0.5, 0, image)
                
                # Draw text
                cv2.putText(image, text, (text_x, text_y),
                          cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA)

            cv2.putText(image, f'Left Counter: {left_counter}', (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2, cv2.LINE_AA)
            cv2.putText(image, f'Right Counter: {right_counter}', (10, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2, cv2.LINE_AA)

        cv2.waitKey(1)
        ret, buffer = cv2.imencode('.jpg', image)
        frame = buffer.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')