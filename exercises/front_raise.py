import cv2
import pygame
import os
from gtts import gTTS
from utils import calculate_angle, mp_pose, pose

def dumbbell_front_raise(sound):
    """
    Track dumbbell front raise exercise
    
    Args:
        sound: Pygame sound object for alerts (not used with voice feedback)
        
    Yields:
        Video frames with pose tracking
    """
    left_counter = 0
    right_counter = 0
    left_state = "down"
    right_state = "down"
    cap = cv2.VideoCapture(0)
    voice_playing = False  # Flag to track if voice guidance is playing
    current_instruction = None  # Track current instruction
    
    # Initialize pygame mixer if not already initialized
    if not pygame.mixer.get_init():
        pygame.mixer.init()
    
    # Create audio directory if it doesn't exist
    os.makedirs("audio", exist_ok=True)
    
    # Define feedback instructions
    instructions = {
        "lower_arm": "LOWER YOUR ARM! YOUR ANGLE IS TOO HIGH!",
        "elbow_bend": "KEEP YOUR ELBOW SLIGHTLY BENT, NOT LOCKED!",
        "arm_position": "KEEP YOUR ARM IN FRONT OF YOUR BODY!",
        "slow_down": "SLOW DOWN! CONTROL THE MOVEMENT!"
    }
    
    # Dictionary to store voice instruction sound objects
    voice_objects = {}
    
    # Generate voice instructions if needed
    try:
        from gtts import gTTS
        
        for key, message in instructions.items():
            filepath = f"audio/front_raise_{key}.mp3"
            
            # Create audio file if it doesn't exist
            if not os.path.exists(filepath):
                print(f"Creating voice instruction: {filepath}")
                tts = gTTS(text=message, lang='en')
                tts.save(filepath)
            
            # Load sound object
            voice_objects[key] = pygame.mixer.Sound(filepath)
    except ImportError:
        print("gTTS not available, voice files must be created manually")
    except Exception as e:
        print(f"Error with voice setup: {e}")

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
            elbow_too_straight = False
            moving_too_fast = False
            arm_position_wrong = False
            current_violation = None

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

                # Check for form issues
                # 1. Check if shoulder angle exceeds 150 degrees (arm raised too high)
                if shoulder_angle > 150:
                    arm_angle_violated = True
                    current_violation = "lower_arm"
                    # Highlight the angle in red to indicate violation
                    cv2.putText(image, f'{int(shoulder_angle)}', shoulder_coords, 
                              cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
                
                # 2. Check if elbow is too straight (locked)
                if elbow_angle > 170:
                    elbow_too_straight = True
                    if not arm_angle_violated:  # Only set if no higher priority violation
                        current_violation = "elbow_bend"
                    # Mark the elbow angle in red
                    cv2.putText(image, f'{int(elbow_angle)}', elbow_coords, 
                              cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
                
                # 3. Check if arm position is correct (in front of body)
                # This is a simplified check - adjust based on your needs
                if wrist.y < shoulder.y and abs(wrist_x - shoulder_x) > 100:
                    arm_position_wrong = True
                    if not (arm_angle_violated or elbow_too_straight):
                        current_violation = "arm_position"

                wrist_x = wrist.x * image.shape[1]
                shoulder_x = shoulder.x * image.shape[1]
                wrist_y = wrist.y * image.shape[0]
                shoulder_y = shoulder.y * image.shape[0]

                # Rep counting logic - only count if form is correct
                if side == 'left':
                    if elbow_angle >= 110 and left_state == "down" and not (arm_angle_violated or elbow_too_straight or arm_position_wrong):
                        if wrist.y < shoulder.y and 30 < abs(wrist_x - shoulder_x) < 100:
                            left_state = "up"
                            left_counter += 1
                            # Print confirmation for debugging
                            print(f"Left arm rep counted! Total: {left_counter}")
                    elif elbow_angle > 160 and wrist.y > shoulder.y and left_state == "up":
                        left_state = "down"
                        print("Left arm ready for next rep")

                elif side == 'right':
                    if elbow_angle >= 110 and right_state == "down" and not (arm_angle_violated or elbow_too_straight or arm_position_wrong):
                        if wrist.y < shoulder.y and 30 < abs(wrist_x - shoulder_x) < 100:
                            right_state = "up"
                            right_counter += 1
                            # Print confirmation for debugging
                            print(f"Right arm rep counted! Total: {right_counter}")
                    elif elbow_angle > 160 and wrist.y > shoulder.y and right_state == "up":
                        right_state = "down"
                        print("Right arm ready for next rep")

            # Voice feedback control based on detected violations
            any_violation = arm_angle_violated or elbow_too_straight or arm_position_wrong or moving_too_fast
            
            if any_violation and current_violation:
                # If violation detected and voice not playing or playing a different instruction
                if not voice_playing or current_instruction != current_violation:
                    # Stop any current playback
                    pygame.mixer.stop()
                    
                    # Play the appropriate voice instruction
                    if current_violation in voice_objects:
                        voice_objects[current_violation].play()
                        voice_playing = True
                        current_instruction = current_violation
                        print(f"Playing instruction: {current_violation}")
                    else:
                        print(f"Warning: Missing voice for {current_violation}")
            elif voice_playing:
                # Stop voice playback when form is corrected
                pygame.mixer.stop()
                voice_playing = False
                current_instruction = None
                print("Form corrected, stopping voice guidance")
            
            # Display instruction message whenever the angle is violated (while voice is active)
            if voice_playing and current_instruction:
                # Get the actual instruction text being spoken
                text = instructions[current_instruction]
                
                # Centered text with background for better visibility
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
                
                # Draw text - use the exact voice instruction text
                cv2.putText(image, text, (text_x, text_y),
                          cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA)

            # Display counters and form status indicators
            cv2.putText(image, f'Left Counter: {left_counter}', (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2, cv2.LINE_AA)
            cv2.putText(image, f'Right Counter: {right_counter}', (10, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2, cv2.LINE_AA)
            
            # Add form status indicator
            form_status = "GOOD FORM" if not any_violation else "FIX YOUR FORM"
            form_color = (0, 255, 0) if not any_violation else (0, 0, 255)  # Green if good, red if needs fixing
            
            cv2.putText(image, form_status, (10, 150), cv2.FONT_HERSHEY_SIMPLEX, 1, form_color, 2, cv2.LINE_AA)
            
            # Add exercise guidance at the bottom of the screen
            cv2.putText(image, "Front Raise: Lift arms to shoulder height", (10, image.shape[0] - 90), 
                      cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1, cv2.LINE_AA)
            cv2.putText(image, "Keep elbows slightly bent", (10, image.shape[0] - 60), 
                      cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1, cv2.LINE_AA)
            cv2.putText(image, "Maximum shoulder angle: 150 degrees", (10, image.shape[0] - 30), 
                      cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1, cv2.LINE_AA)

        cv2.waitKey(1)
        ret, buffer = cv2.imencode('.jpg', image)
        frame = buffer.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')