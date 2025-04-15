import numpy as np
import math
import mediapipe as mp
import os

# Initialize mediapipe pose
mp_drawing = mp.solutions.drawing_utils
mp_pose = mp.solutions.pose

# Create pose instance with reasonable defaults for cloud environment
# Note: We're using lower confidence thresholds to ensure better performance in cloud
pose = mp_pose.Pose(
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5,
    model_complexity=1  # Medium complexity for balance between performance and accuracy
)

def calculate_angle(a, b, c):
    """
    Calculate the angle between three points
    
    Args:
        a: First point [x, y]
        b: Mid point [x, y]
        c: End point [x, y]
        
    Returns:
        Angle in degrees
    """
    a = np.array(a)  # First
    b = np.array(b)  # Mid
    c = np.array(c)  # End

    ab = a - b
    bc = c - b

    # Calculate the angle using dot product
    # Use clip to handle floating point errors
    cosine_angle = np.clip(np.dot(ab, bc) / (np.linalg.norm(ab) * np.linalg.norm(bc)), -1.0, 1.0)
    angle = np.arccos(cosine_angle)
    
    # Convert to degrees
    return math.degrees(angle)

def ensure_directories():
    """
    Ensure required directories exist
    """
    # Create audio directory for voice feedback
    os.makedirs("audio", exist_ok=True)