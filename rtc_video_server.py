import json
import cv2
import asyncio
import threading
import numpy as np
import mediapipe as mp
from utils import calculate_angle, mp_pose, pose
import asyncio

# Dictionary to store active video processors
video_processors = {}

# Function to process WebRTC offer and setup connection
async def process_offer(offer_data):
    sdp = offer_data.get('sdp')
    video_type = offer_data.get('exercise', 'default')
    
    # Create a proper WebRTC answer
    # Note: In a real WebRTC implementation, we would process the offer SDP
    # and create a real answer. This is a simplified version.
    response = {
        'sdp': {
            'type': 'answer',
            'sdp': sdp.get('sdp')  # Properly extract SDP from the offer
        },
        'ice_candidates': [
            # Example ICE candidates - in real implementation these would be dynamic
            {'candidate': 'candidate:1 1 UDP 2130706431 192.168.1.1 8888 typ host', 'sdpMLineIndex': 0}
        ]
    }
    
    # Start a new video processing thread for this connection
    if video_type not in video_processors:
        # Start appropriate video processor based on exercise type
        await start_video_processor(video_type)
    
    return response

async def start_video_processor(exercise_type):
    """
    Start a new thread to process video for the given exercise type
    
    Args:
        exercise_type: Type of exercise to track
    """
    processor_thread = threading.Thread(target=await video_processor_worker(exercise_type))
    processor_thread.daemon = True
    processor_thread.start()
    video_processors[exercise_type] = processor_thread
    print(f"Started video processor for {exercise_type}")

async def video_processor_worker(exercise_type):
    """
    Worker function that processes the video from the WebRTC connection.
    
    Args:
        exercise_type: Type of exercise to track
    """
    # Initialize WebRTC connection and start receiving video
    try:
        # Create a PeerConnection
        pc = RTCPeerConnection()
        
        # Add video track to peer connection
        video_track = VideoStreamTrack(exercise_type)
        pc.addTrack(video_track)

        # Create and send offer to client
        offer = await pc.createOffer()
        await pc.setLocalDescription(offer)

        # Here, send the SDP answer to the client

        # Process frames from the video track
        while True:
            frame = await video_track.recv()
            if frame is not None:
                # Call your exercise processing code here, e.g., using the frame
                await process_exercise_frame(frame, exercise_type)
                
            await asyncio.sleep(0.1)  # Avoid high CPU usage

    except Exception as e:
        print(f"Error in video processor: {str(e)}")
    finally:
        # Clean up resources
        print(f"Video processor for {exercise_type} stopped")

async def process_exercise_frame(frame, exercise_type):
    """
    Process the frames for the given exercise type.
    
    Args:
        frame: The video frame
        exercise_type: Type of exercise being performed
    """
    # Process frame here - you can add your frame processing logic
    print(f"Processing frame for {exercise_type}")
    # Example: Using OpenCV to process the frame
    # processed_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    # frame_data = processed_frame
    return

from aiortc import RTCPeerConnection, VideoStreamTrack

async def process_offer(offer_data):
    try:
        sdp = offer_data.get('sdp', {})
        exercise = offer_data.get('exercise', 'default')
        
        # Create a simplified WebRTC response
        response = {
            'sdp': {
                'type': 'answer',
                'sdp': sdp.get('sdp', '')
            },
            'ice_candidates': []
        }
        
        return response
    except Exception as e:
        print(f"Error processing offer: {str(e)}")
        return {"error": str(e)}




import asyncio
from aiortc import RTCPeerConnection, VideoStreamTrack

async def process_offer(offer_data):
    try:
        sdp = offer_data.get('sdp', {})
        exercise = offer_data.get('exercise', 'default')
        
        # Simplified WebRTC response
        response = {
            'sdp': {
                'type': 'answer',
                'sdp': sdp.get('sdp', '')
            },
            'ice_candidates': []
        }
        
        return response
    except Exception as e:
        print(f"Error processing WebRTC offer: {str(e)}")
        return {"error": str(e)}
    



    
def get_frame_from_exercise(exercise_type):
    """
    Get the latest processed frame for a specific exercise
    
    Args:
        exercise_type: Type of exercise
        
    Returns:
        Latest processed frame or None if not available
    """
    # In a real implementation, this would retrieve the latest frame
    # For now it just returns None
    return None
