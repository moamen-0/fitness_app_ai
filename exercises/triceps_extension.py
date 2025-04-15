import cv2
from utils import calculate_angle, mp_pose, pose

def triceps_extension(sound):
    """
    Track triceps extension exercise
    
    Args:
        sound: Pygame sound object for alerts
        
    Yields:
        Video frames with pose tracking
    """
    counter = 0  
    state = None 
    cap = cv2.VideoCapture(0)

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        # Flip horizontally
        frame = cv2.flip(frame, 1)
        image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = pose.process(image)
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

        if results.pose_landmarks:
            landmarks = results.pose_landmarks.landmark

            # Define landmarks for both arms
            arm_sides = {
                'right': {
                    'shoulder': mp_pose.PoseLandmark.RIGHT_SHOULDER,
                    'elbow': mp_pose.PoseLandmark.RIGHT_ELBOW,
                    'wrist': mp_pose.PoseLandmark.RIGHT_WRIST
                },
                'left': {
                    'shoulder': mp_pose.PoseLandmark.LEFT_SHOULDER,
                    'elbow': mp_pose.PoseLandmark.LEFT_ELBOW,
                    'wrist': mp_pose.PoseLandmark.LEFT_WRIST
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

                # Convert to pixel coordinates
                shoulder_coords = (int(shoulder[0] * image.shape[1]), int(shoulder[1] * image.shape[0]))
                elbow_coords = (int(elbow[0] * image.shape[1]), int(elbow[1] * image.shape[0]))
                wrist_coords = (int(wrist[0] * image.shape[1]), int(wrist[1] * image.shape[0]))

                # Draw lines
                cv2.line(image, shoulder_coords, elbow_coords, (0, 255, 0), 2)
                cv2.line(image, elbow_coords, wrist_coords, (0, 255, 0), 2)

                # Draw joint circles
                cv2.circle(image, shoulder_coords, 7, (0, 0, 255), -1)
                cv2.circle(image, elbow_coords, 7, (0, 0, 255), -1)
                cv2.circle(image, wrist_coords, 7, (0, 0, 255), -1)

                # Calculate angle
                elbow_angle = calculate_angle(shoulder, elbow, wrist)

                # Display angle
                cv2.putText(
                    image,
                    f'{int(elbow_angle)}°',
                    elbow_coords,
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (255, 255, 255),
                    2,
                    cv2.LINE_AA
                )

                # Count repetitions
                if elbow_angle < 45:
                    state = "down"
                if elbow_angle > 160 and state == "down":
                    state = "up"
                    counter += 1
                    print(f'Triceps Reps: {counter}')

            # Display counter
            cv2.putText(image, f'Triceps Reps: {counter}', (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2, cv2.LINE_AA)

        # Convert to JPEG for streaming
        ret, buffer = cv2.imencode('.jpg', image)
        frame = buffer.tobytes()

        # Yield frame for Flask response
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')