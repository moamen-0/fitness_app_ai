import cv2
from utils import calculate_angle, mp_pose, pose

def push_ups(sound):
    """
    Track push-ups exercise
    
    Args:
        sound: Pygame sound object for alerts
        
    Yields:
        Video frames with pose tracking
    """
    counter = 0  # عداد التكرارات
    state = None  # حالة التمرين
    cap = cv2.VideoCapture(0)
    sound_playing = False  # حالة تشغيل الصوت
    
    print("Push-ups Exercise Started")
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
            
        # قلب الإطار أفقياً
        frame = cv2.flip(frame, 1)
        image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = pose.process(image)
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
        
        form_violated = False
        instruction_message = ""
        
        if results.pose_landmarks:
            landmarks = results.pose_landmarks.landmark
            
            # تحديد نقاط مهمة للذراعين والجسم
            arm_sides = {
                'left': {
                    'shoulder': mp_pose.PoseLandmark.LEFT_SHOULDER,
                    'elbow': mp_pose.PoseLandmark.LEFT_ELBOW,
                    'wrist': mp_pose.PoseLandmark.LEFT_WRIST,
                    'hip': mp_pose.PoseLandmark.LEFT_HIP,
                    'knee': mp_pose.PoseLandmark.LEFT_KNEE
                },
                'right': {
                    'shoulder': mp_pose.PoseLandmark.RIGHT_SHOULDER,
                    'elbow': mp_pose.PoseLandmark.RIGHT_ELBOW,
                    'wrist': mp_pose.PoseLandmark.RIGHT_WRIST,
                    'hip': mp_pose.PoseLandmark.RIGHT_HIP,
                    'knee': mp_pose.PoseLandmark.RIGHT_KNEE
                }
            }
            
            # حساب زاوية الجسم الكلي
            left_shoulder = [
                landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].x,
                landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].y
            ]
            right_shoulder = [
                landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value].x,
                landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value].y
            ]
            left_hip = [
                landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].x,
                landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].y
            ]
            right_hip = [
                landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value].x,
                landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value].y
            ]
            
            # حساب زاوية الجسم الإجمالية
            body_midpoint_shoulder = [(left_shoulder[0] + right_shoulder[0])/2, 
                                      (left_shoulder[1] + right_shoulder[1])/2]
            body_midpoint_hip = [(left_hip[0] + right_hip[0])/2, 
                                 (left_hip[1] + right_hip[1])/2]
            
            # نقطة رأسية فوق نقطة الوسط
            vertical_point = [body_midpoint_shoulder[0], body_midpoint_shoulder[1] - 0.2]
            
            # زاوية الجسم
            body_angle = calculate_angle(vertical_point, body_midpoint_shoulder, body_midpoint_hip)
            
            # متغيرات لتتبع حالة الذراعين
            left_arm_state = "up"
            right_arm_state = "up"
            
            # معالجة كل ذراع
            for side, joints in arm_sides.items():
                # الحصول على إحداثيات المفاصل
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
                
                # تحويل الإحداثيات إلى إحداثيات الصورة
                shoulder_coords = (int(shoulder[0] * image.shape[1]), int(shoulder[1] * image.shape[0]))
                elbow_coords = (int(elbow[0] * image.shape[1]), int(elbow[1] * image.shape[0]))
                wrist_coords = (int(wrist[0] * image.shape[1]), int(wrist[1] * image.shape[0]))
                hip_coords = (int(hip[0] * image.shape[1]), int(hip[1] * image.shape[0]))
                
                # رسم الخطوط والنقاط
                cv2.line(image, shoulder_coords, elbow_coords, (0, 255, 0), 2)
                cv2.line(image, elbow_coords, wrist_coords, (0, 255, 0), 2)
                cv2.line(image, shoulder_coords, hip_coords, (0, 255, 0), 2)
                
                cv2.circle(image, shoulder_coords, 7, (0, 0, 255), -1)
                cv2.circle(image, elbow_coords, 7, (0, 0, 255), -1)
                cv2.circle(image, wrist_coords, 7, (0, 0, 255), -1)
                cv2.circle(image, hip_coords, 7, (0, 0, 255), -1)
                
                # حساب الزوايا
                elbow_angle = calculate_angle(shoulder, elbow, wrist)
                shoulder_angle = calculate_angle(hip, shoulder, elbow)
                
                # عرض الزوايا
                cv2.putText(image, f'Elbow: {int(elbow_angle)}°', elbow_coords, 
                          cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2, cv2.LINE_AA)
                cv2.putText(image, f'Shoulder: {int(shoulder_angle)}°', shoulder_coords, 
                          cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2, cv2.LINE_AA)
                
                # التحقق من صحة الأداء
                # زاوية المرفق يجب أن تكون حوالي 90 درجة عند النزول
                # زاوية المرفق يجب أن تكون قريبة من 180 درجة عند الرفع
                if elbow_angle < 130:  # نزول
                    if side == 'left':
                        left_arm_state = "down"
                    else:
                        right_arm_state = "down"
                    
                    # التحقق من زاوية الجسم
                    if body_angle > 20:  # انحناء الجسم أكثر من 20 درجة
                        form_violated = True
                        instruction_message = "KEEP YOUR BODY STRAIGHT!"
                        
                elif elbow_angle > 170:  # رفع
                    if side == 'left':
                        left_arm_state = "up"
                    else:
                        right_arm_state = "up"
            
            # منطق حساب التكرارات
            if left_arm_state == "down" and right_arm_state == "down":
                state = "down"
            elif left_arm_state == "up" and right_arm_state == "up" and state == "down":
                counter += 1
                state = "up"
                print(f"Push-up counted! Total: {counter}")
            
            # التحكم في الصوت والتنبيهات
            if form_violated and not sound_playing:
                sound.play()
                sound_playing = True
            elif not form_violated and sound_playing:
                sound.stop()
                sound_playing = False
            
            # عرض رسالة التعليمات
            if sound_playing and instruction_message:
                text_size = cv2.getTextSize(instruction_message, cv2.FONT_HERSHEY_SIMPLEX, 1, 2)[0]
                text_x = (image.shape[1] - text_size[0]) // 2
                text_y = image.shape[0] // 2
                
                # رسم خلفية شبه شفافة
                overlay = image.copy()
                cv2.rectangle(overlay, 
                             (text_x - 10, text_y - text_size[1] - 10),
                             (text_x + text_size[0] + 10, text_y + 10),
                             (0, 0, 0), -1)
                cv2.addWeighted(overlay, 0.5, image, 0.5, 0, image)
                
                # رسم النص
                cv2.putText(image, instruction_message, (text_x, text_y),
                          cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA)
            
            # عرض العداد
            cv2.putText(image, f'Push-ups: {counter}', (10, 50), 
                      cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2, cv2.LINE_AA)
            
            # عرض توجيهات إضافية
            cv2.putText(image, "Keep body straight", (10, image.shape[0] - 90),
                      cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1, cv2.LINE_AA)
            cv2.putText(image, "Elbows at 90° when down", (10, image.shape[0] - 60),
                      cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1, cv2.LINE_AA)
            cv2.putText(image, "Full extension at top", (10, image.shape[0] - 30),
                      cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1, cv2.LINE_AA)
        
        # تحويل الصورة
        ret, buffer = cv2.imencode('.jpg', image)
        frame = buffer.tobytes()
        
        # إرسال الإطار
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')