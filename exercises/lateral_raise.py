import cv2
import math
import pygame
import os
from gtts import gTTS
from utils import calculate_angle, mp_pose, pose

def side_lateral_raise(sound):
    """
    Track side lateral raise exercise
    
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
    voice_playing = False  # Flag to track if voice is playing
    current_instruction = None  # Track current instruction being played
    
    # Initialize pygame mixer if not already initialized
    if not pygame.mixer.get_init():
        pygame.mixer.init()
    
    # Create audio directory if it doesn't exist
    os.makedirs("audio", exist_ok=True)
    
    # Define feedback instructions
    instructions = {
        "lower_arms": "LOWER YOUR ARMS! ANGLE TOO HIGH!",
        "straighten_elbows": "STRAIGHTEN YOUR ELBOWS SLIGHTLY!",
        "arms_too_forward": "KEEP ARMS TO THE SIDE, NOT FORWARD!",
        "slow_down": "SLOW DOWN! CONTROL THE MOVEMENT!"
    }
    
    # Dictionary to store voice instruction sound objects
    voice_objects = {}
    
    # Generate voice instructions if needed
    try:
        from gtts import gTTS
        
        for key, message in instructions.items():
            filepath = f"audio/lateral_raise_{key}.mp3"
            
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

            # Initialize violation tracking variables
            shoulder_angle_too_high = False
            elbow_angle_too_low = False
            arms_too_forward = False
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

                # Draw connections
                cv2.line(image, shoulder_coords, elbow_coords, (0, 255, 0), 2)
                cv2.line(image, elbow_coords, wrist_coords, (0, 255, 0), 2)
                cv2.line(image, hip_coords, shoulder_coords, (0, 255, 0), 2)

                # Draw joints
                for point in [shoulder_coords, elbow_coords, wrist_coords, hip_coords]:
                    cv2.circle(image, point, 7, (0, 0, 255), -1)

                # Calculate angles
                elbow_angle = calculate_angle([shoulder.x, shoulder.y], [elbow.x, elbow.y], [wrist.x, wrist.y])
                
                # For side lateral raise, we need to measure the angle between hip, shoulder, and elbow
                shoulder_angle = calculate_angle([hip.x, hip.y], [shoulder.x, shoulder.y], [elbow.x, elbow.y])
                
                # Display angles - default color (white)
                elbow_color = (255, 255, 255)
                shoulder_color = (255, 255, 255)
                
                # Check for form issues
                
                # 1. Check if shoulder angle exceeds maximum (110 degrees for lateral raise)
                max_shoulder_angle = 110
                if shoulder_angle > max_shoulder_angle:
                    shoulder_angle_too_high = True
                    if not current_violation:  # Set if no higher priority violation
                        current_violation = "lower_arms"
                    # Highlight the angle in red to indicate violation
                    shoulder_color = (0, 0, 255)
                
                # 2. Check for proper elbow angle (alert if too bent - 100 degrees or less)
                if elbow_angle <= 100:
                    elbow_angle_too_low = True
                    if not shoulder_angle_too_high and not current_violation:
                        current_violation = "straighten_elbows"
                    # Highlight the angle in red
                    elbow_color = (0, 0, 255)
                
                # We've removed the "arms too low" check since raising arms is part of the exercise
                # and not an error condition
                    
                # 4. Check if arms are too far forward (simplified check)
                # This would use z-coordinates in 3D, but we'll use a simplification
                # For demonstration, we'll check the relative positions as a simplified approach
                
                # Display angles with appropriate colors
                cv2.putText(image, f'E: {int(elbow_angle)}', elbow_coords, 
                          cv2.FONT_HERSHEY_SIMPLEX, 0.5, elbow_color, 2)
                cv2.putText(image, f'S: {int(shoulder_angle)}', shoulder_coords, 
                          cv2.FONT_HERSHEY_SIMPLEX, 0.5, shoulder_color, 2)
                
                # Draw a visual indicator showing the target angle of 85 degrees
                # This helps the user see where they need to raise their arm to
                target_angle_rad = math.radians(85)
                target_line_length = 100  # pixels
                
                # Calculate end point for the target angle line
                if side == 'left':
                    target_x = shoulder_coords[0] - target_line_length * math.sin(target_angle_rad)
                    target_y = shoulder_coords[1] - target_line_length * math.cos(target_angle_rad)
                else:  # right side
                    target_x = shoulder_coords[0] + target_line_length * math.sin(target_angle_rad)
                    target_y = shoulder_coords[1] - target_line_length * math.cos(target_angle_rad)
                
                # Draw dotted line showing target angle
                target_point = (int(target_x), int(target_y))
                cv2.line(image, shoulder_coords, target_point, (0, 255, 255), 1, cv2.LINE_AA)
                cv2.putText(image, "85°", target_point, cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
                
                # Rep counting logic - only count if form is correct
                if side == 'left':
                    # Only count when form is good (no violations)
                    if shoulder_angle >= 85 and left_state == "down" and not (shoulder_angle_too_high or elbow_angle_too_low):
                        left_state = "up"
                        left_counter += 1
                        print(f"Left arm rep counted! Total: {left_counter}")
                    
                    # DOWN state detection - arms at sides
                    elif shoulder_angle < 20 and left_state == "up":
                        left_state = "down"
                        print("Left arm ready for next rep")
                    
                elif side == 'right':
                    # Only count when form is good (no violations)
                    if shoulder_angle >= 85 and right_state == "down" and not (shoulder_angle_too_high or elbow_angle_too_low):
                        right_state = "up"
                        right_counter += 1
                        print(f"Right arm rep counted! Total: {right_counter}")
                    
                    # DOWN state detection - arms at sides
                    elif shoulder_angle < 20 and right_state == "up":
                        right_state = "down"
                        print("Right arm ready for next rep")
                
                # Display current state on image for debugging
                state_text = "up" if (side == "left" and left_state == "up") or (side == "right" and right_state == "up") else "down"
                cv2.putText(image, f'{side} state: {state_text}', 
                         (int(shoulder.x * image.shape[1]), int(shoulder.y * image.shape[0] - 30)),
                         cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

            # Voice feedback control based on detected violations - removed arms_too_low
            any_violation = shoulder_angle_too_high or elbow_angle_too_low or arms_too_forward
            
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
            
            # Display instruction message whenever voice is active
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

            # Display counters and form status
            cv2.putText(image, f'Left Counter: {left_counter}', (10, 50), 
                      cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2, cv2.LINE_AA)
            cv2.putText(image, f'Right Counter: {right_counter}', (10, 100), 
                      cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2, cv2.LINE_AA)
            
            # Add form status indicator
            form_status = "GOOD FORM" if not any_violation else "FIX YOUR FORM"
            form_color = (0, 255, 0) if not any_violation else (0, 0, 255)  # Green if good, red if needs fixing
            
            cv2.putText(image, form_status, (10, 150), cv2.FONT_HERSHEY_SIMPLEX, 1, form_color, 2, cv2.LINE_AA)
            
            # Add exercise guidance at the bottom of the screen
            cv2.putText(image, f"Left state: {left_state} | Right state: {right_state}", (10, image.shape[0] - 120),
                      cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 1, cv2.LINE_AA)
            cv2.putText(image, "Raise arms laterally to 85 degrees", (10, image.shape[0] - 90),
                      cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1, cv2.LINE_AA)
            cv2.putText(image, "Maximum shoulder angle: 110 degrees", (10, image.shape[0] - 60),
                      cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1, cv2.LINE_AA)
            cv2.putText(image, "Keep elbows above 100 degrees", (10, image.shape[0] - 30),
                      cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1, cv2.LINE_AA)

        # Convert to JPEG for streaming
        ret, buffer = cv2.imencode('.jpg', image)
        frame = buffer.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')