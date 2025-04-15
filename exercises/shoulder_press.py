import cv2
import pygame
import os
from gtts import gTTS
from utils import calculate_angle, mp_pose, pose

def shoulder_press(sound):
    """
    Track shoulder press exercise with voice instructions
    
    Args:
        sound: Pygame sound object (not used, replaced with voice instructions)
        
    Yields:
        Video frames with pose tracking
    """
    counter = 0  # Counter for reps
    stage = None  # State of the exercise
    cap = cv2.VideoCapture(0)
    voice_playing = False  # Flag to track if voice is playing
    current_instruction = None  # Track current instruction being played
    
    # Initialize pygame mixer if not already initialized
    if not pygame.mixer.get_init():
        pygame.mixer.init()
    
    # Create audio directory if it doesn't exist
    os.makedirs("audio", exist_ok=True)
    
    # Define clear and helpful instructions for the user
    instructions = {
        "raise_elbows": "RAISE YOUR ELBOW POINTS HIGHER!",
        "lower_arms": "LOWER YOUR ARMS TO 40 DEGREES!",
        "keep_straight": "KEEP YOUR BACK STRAIGHT!",
        "arms_even": "KEEP BOTH ARMS EVEN!"
    }
    
    # Dictionary to store voice instruction sound objects
    voice_objects = {}
    
    # Generate voice instructions if needed
    try:
        from gtts import gTTS
        
        for key, message in instructions.items():
            filepath = f"audio/shoulder_press_{key}.mp3"
            
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
    
    print("Shoulder Press Exercise Started")
    
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
        low_elbow_angle = False  # Flag for low elbow angle
        arms_not_even = False  # Flag for uneven arms
        instruction_message = ""
        current_violation = None
        
        if results.pose_landmarks:
            landmarks = results.pose_landmarks.landmark
            
            # Define landmarks for both arms
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
            
            # Variables to track whether both arms are in correct position
            left_arm_down = False
            right_arm_down = False
            left_arm_at_150 = False
            right_arm_at_150 = False
            
            left_elbow_angle = 0
            right_elbow_angle = 0
            
            # Process each arm
            for side, joints in arm_sides.items():
                # Get coordinates for each joint
                shoulder = [
                    landmarks[joints['shoulder'].value].x,
                    landmarks[joints['shoulder'].value].y
                ]
                elbow = [
                    landmarks[joints['elbow'].value].x,
                    landmarks[joints['elbow'].value].y
                ]
                wrist = [
                    landmarks[joints['wrist'].value].x,
                    landmarks[joints['wrist'].value].y
                ]
                hip = [
                    landmarks[joints['hip'].value].x,
                    landmarks[joints['hip'].value].y
                ]
                
                # Convert to pixel coordinates
                shoulder_coords = (int(shoulder[0] * image.shape[1]), int(shoulder[1] * image.shape[0]))
                elbow_coords = (int(elbow[0] * image.shape[1]), int(elbow[1] * image.shape[0]))
                wrist_coords = (int(wrist[0] * image.shape[1]), int(wrist[1] * image.shape[0]))
                hip_coords = (int(hip[0] * image.shape[1]), int(hip[1] * image.shape[0]))
                
                # Draw arm lines
                cv2.line(image, shoulder_coords, elbow_coords, (0, 255, 0), 2)
                cv2.line(image, elbow_coords, wrist_coords, (0, 255, 0), 2)
                cv2.line(image, shoulder_coords, hip_coords, (0, 255, 0), 2)
                
                # Draw joint circles
                cv2.circle(image, shoulder_coords, 7, (0, 0, 255), -1)
                cv2.circle(image, elbow_coords, 7, (0, 0, 255), -1)
                cv2.circle(image, wrist_coords, 7, (0, 0, 255), -1)
                cv2.circle(image, hip_coords, 7, (0, 0, 255), -1)
                
                # Calculate angles
                elbow_angle = calculate_angle(shoulder, elbow, wrist)
                shoulder_angle = calculate_angle(hip, shoulder, elbow)
                
                # Store elbow angles for each arm
                if side == 'left':
                    left_elbow_angle = elbow_angle
                else:
                    right_elbow_angle = elbow_angle
                
                # Display angles
                elbow_color = (255, 255, 255)  # Default white
                
                # Check if elbow angle is too low (30 degrees or less)
                if elbow_angle <= 30:
                    low_elbow_angle = True
                    current_violation = "raise_elbows"
                    elbow_color = (0, 0, 255)  # Red when angle is too low
                
                # Check if at target angle for UP position (around 150 degrees)
                elif 140 <= elbow_angle <= 160:
                    elbow_color = (0, 255, 0)  # Green when at target angle
                    if side == 'left':
                        left_arm_at_150 = True
                    else:
                        right_arm_at_150 = True
                
                # Check if at target angle for DOWN position (around 40 degrees)
                elif 35 <= elbow_angle <= 45:
                    elbow_color = (0, 255, 255)  # Yellow when at down position
                    if side == 'left':
                        left_arm_down = True
                    else:
                        right_arm_down = True
                
                cv2.putText(
                    image,
                    f'E: {int(elbow_angle)}°',
                    elbow_coords,
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    elbow_color,
                    2,
                    cv2.LINE_AA
                )
                
                cv2.putText(
                    image,
                    f'S: {int(shoulder_angle)}°',
                    shoulder_coords,
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (255, 255, 255),
                    2,
                    cv2.LINE_AA
                )
                
                # Check for proper form in DOWN position
                if 35 <= elbow_angle <= 45:
                    if side == 'left':
                        left_arm_down = True
                    else:
                        right_arm_down = True
                else:
                    # If not in proper position and not at target up angle
                    if not (140 <= elbow_angle <= 160) and wrist[1] > shoulder[1] and elbow_angle > 45:
                        form_violated = True
                        if not low_elbow_angle:  # Don't overwrite the low elbow angle instruction
                            current_violation = "lower_arms"
                        instruction_message = "LOWER YOUR ARMS TO 40 DEGREES!"
            
            # Check if arms are even (similar angles)
            if abs(left_elbow_angle - right_elbow_angle) > 15:  # More than 15 degrees difference
                arms_not_even = True
                if not (low_elbow_angle or form_violated):  # Lower priority than other violations
                    current_violation = "arms_even"
                    instruction_message = "KEEP BOTH ARMS EVEN!"
            
            # Display arm status for debugging
            cv2.putText(
                image,
                f'L: {int(left_elbow_angle)}° {"DOWN" if left_arm_down else "UP" if left_arm_at_150 else "MID"}',
                (10, image.shape[0] - 150),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (255, 255, 255),
                1,
                cv2.LINE_AA
            )
            
            cv2.putText(
                image,
                f'R: {int(right_elbow_angle)}° {"DOWN" if right_arm_down else "UP" if right_arm_at_150 else "MID"}',
                (10, image.shape[0] - 120),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (255, 255, 255),
                1,
                cv2.LINE_AA
            )
            
            # Track the shoulder press movement using both arms
            if left_arm_down and right_arm_down:
                if stage != "down":
                    print("Setting stage to DOWN")
                stage = "down"
            elif left_arm_at_150 and right_arm_at_150 and stage == "down":
                counter += 1
                stage = "up"
                print(f"Counter increased! Count: {counter}")
            
            # Handle voice feedback based on form violations
            any_violation = low_elbow_angle or form_violated or arms_not_even
            
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
                        instruction_message = instructions[current_violation]
                        print(f"Playing voice instruction: {current_violation}")
                    else:
                        print(f"Warning: Missing voice for {current_violation}")
            elif voice_playing:
                # Stop voice playback when form is corrected
                pygame.mixer.stop()
                voice_playing = False
                current_instruction = None
                print("Form corrected, stopping voice feedback")
            
            # Display instruction message whenever a violation is detected
            if any_violation and instruction_message:
                text_size = cv2.getTextSize(instruction_message, cv2.FONT_HERSHEY_SIMPLEX, 1, 2)[0]
                text_x = (image.shape[1] - text_size[0]) // 2
                text_y = image.shape[0] // 2
                
                # Draw semi-transparent background
                overlay = image.copy()
                cv2.rectangle(overlay, 
                             (text_x - 10, text_y - text_size[1] - 10),
                             (text_x + text_size[0] + 10, text_y + 10),
                             (0, 0, 0), -1)
                cv2.addWeighted(overlay, 0.5, image, 0.5, 0, image)
                
                # Draw text
                cv2.putText(
                    image, 
                    instruction_message, 
                    (text_x, text_y),
                    cv2.FONT_HERSHEY_SIMPLEX, 
                    1, 
                    (0, 0, 255), 
                    2, 
                    cv2.LINE_AA
                )
            
            # Display counter and stage
            cv2.putText(
                image, 
                f'Count: {counter}',
                (10, 50), 
                cv2.FONT_HERSHEY_SIMPLEX, 
                1, 
                (255, 0, 0), 
                2, 
                cv2.LINE_AA
            )
            
            cv2.putText(
                image, 
                f'Stage: {stage if stage else "None"}',
                (10, 90), 
                cv2.FONT_HERSHEY_SIMPLEX, 
                1, 
                (255, 0, 0), 
                2, 
                cv2.LINE_AA
            )
            
            # Add form status indicator
            form_status = "GOOD FORM" if not any_violation else "FIX YOUR FORM"
            form_color = (0, 255, 0) if not any_violation else (0, 0, 255)  # Green if good, red if needs fixing
            
            cv2.putText(image, form_status, (10, 130), cv2.FONT_HERSHEY_SIMPLEX, 1, form_color, 2, cv2.LINE_AA)
            
            # Add target angle indicators
            cv2.putText(
                image,
                "Down: 40° | Up: 150°",
                (10, image.shape[0] - 90),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 255, 0),
                1,
                cv2.LINE_AA
            )
            
            # Add form guidance text
            cv2.putText(
                image,
                "Start with elbows at 40°",
                (10, image.shape[0] - 60),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (255, 255, 255),
                1,
                cv2.LINE_AA
            )
            cv2.putText(
                image,
                "Press until elbows reach 150°",
                (10, image.shape[0] - 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (255, 255, 255),
                1,
                cv2.LINE_AA
            )
        
        # Convert image to JPEG for streaming
        ret, buffer = cv2.imencode('.jpg', image)
        frame = buffer.tobytes()
        
        # Yield frame for Flask response
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')