/**
 * WebSocket Camera Handler
 * Handles camera capture and WebSocket transmission for exercise analysis
 */
class WebSocketCameraHandler {
    constructor() {
        this.socket = null;
        this.videoElement = null;
        this.stream = null;
        this.isStreaming = false;
        this.videoCanvas = document.createElement('canvas');
        this.videoContext = this.videoCanvas.getContext('2d');
        this.framerate = 15; // Frames per second to send (adjust for performance)
        this.frameInterval = null;
        this.exerciseId = null;
    }

    /**
     * Initialize the camera and WebSocket connection
     * @param {string} socketUrl - WebSocket server URL
     * @param {string} exerciseId - Exercise identifier
     * @param {Object} options - Configuration options
     */
    async initialize(socketUrl, exerciseId, options = {}) {
        this.exerciseId = exerciseId;
        this.videoElement = options.videoElement || document.getElementById('camera-video');
        
        try {
            // Connect to WebSocket first (to avoid timeout issues)
            await this.connectWebSocket(socketUrl);
            
            // Then initialize camera
            await this.initializeCamera(options);
            
            return true;
        } catch (error) {
            console.error('Error initializing WebSocketCameraHandler:', error);
            return false;
        }
    }

    /**
     * Connect to the WebSocket server
     * @param {string} socketUrl - WebSocket server URL
     * @returns {Promise} - Resolves when connection is established
     */
    connectWebSocket(socketUrl) {
        return new Promise((resolve, reject) => {
            try {
                // Use Socket.IO client
                this.socket = io(socketUrl);
                
                this.socket.on('connect', () => {
                    console.log('WebSocket connected');
                    resolve();
                });
                
                this.socket.on('connect_error', (error) => {
                    console.error('WebSocket connection error:', error);
                    reject(error);
                });
                
                // Set a connection timeout
                const timeout = setTimeout(() => {
                    reject(new Error('WebSocket connection timeout'));
                }, 10000);
                
                this.socket.on('connect', () => {
                    clearTimeout(timeout);
                    resolve();
                });
            } catch (error) {
                reject(error);
            }
        });
    }

    /**
     * Initialize the camera stream
     * @param {Object} options - Camera options
     * @returns {Promise} - Resolves when camera is initialized
     */
    async initializeCamera(options = {}) {
        try {
            const constraints = {
                video: {
                    width: { ideal: options.width || 640 },
                    height: { ideal: options.height || 480 },
                    frameRate: { ideal: this.framerate }
                },
                audio: false
            };
            
            // Add facingMode for mobile devices if specified
            if (options.facingMode) {
                constraints.video.facingMode = options.facingMode;
            }
            
            this.stream = await navigator.mediaDevices.getUserMedia(constraints);
            
            // Set up video element with the stream
            this.videoElement.srcObject = this.stream;
            this.videoElement.play();
            
            // Set up canvas dimensions once video is loaded
            return new Promise((resolve) => {
                this.videoElement.onloadedmetadata = () => {
                    this.videoCanvas.width = this.videoElement.videoWidth;
                    this.videoCanvas.height = this.videoElement.videoHeight;
                    resolve();
                };
            });
        } catch (error) {
            console.error('Camera initialization error:', error);
            throw error;
        }
    }

    /**
     * Start sending video frames to the server
     */
    startStreaming() {
        if (this.isStreaming) return;
        
        // Inform server about starting exercise with this exercise ID
        this.socket.emit('start_exercise', { 
            exercise_id: this.exerciseId,
            client_stream: true // Indicate we're streaming from client
        });
        
        this.isStreaming = true;
        
        // Start sending frames at specified framerate
        this.frameInterval = setInterval(() => {
            this.captureAndSendFrame();
        }, 1000 / this.framerate);
    }

    /**
     * Capture and send a single frame
     */
    captureAndSendFrame() {
        if (!this.isStreaming || !this.socket || !this.socket.connected) return;
        
        try {
            // Draw current video frame to canvas
            this.videoContext.drawImage(
                this.videoElement, 
                0, 0, 
                this.videoCanvas.width, 
                this.videoCanvas.height
            );
            
            // Get frame as JPEG data URL (adjust quality as needed)
            const frameDataUrl = this.videoCanvas.toDataURL('image/jpeg', 0.7);
            
            // Extract base64 data and send to server
            const base64Data = frameDataUrl.split(',')[1];
            
            this.socket.emit('video_frame', {
                frame: base64Data,
                exercise_id: this.exerciseId
            });
        } catch (error) {
            console.error('Error capturing/sending frame:', error);
        }
    }

    /**
     * Stop streaming video frames
     */
    stopStreaming() {
        if (!this.isStreaming) return;
        
        this.isStreaming = false;
        clearInterval(this.frameInterval);
        
        // Tell server to stop the exercise
        if (this.socket && this.socket.connected) {
            this.socket.emit('stop_exercise');
        }
    }

    /**
     * Switch between front and back cameras (mobile devices)
     */
    async switchCamera() {
        if (!this.stream) return;
        
        // Stop current stream tracks
        this.stream.getTracks().forEach(track => track.stop());
        
        // Get current facing mode from video track settings if possible
        let currentFacingMode = 'user'; // Default to front camera
        try {
            const videoTrack = this.stream.getVideoTracks()[0];
            const settings = videoTrack.getSettings();
            currentFacingMode = settings.facingMode || 'user';
        } catch (error) {
            console.warn('Could not determine current facing mode:', error);
        }
        
        // Toggle facing mode
        const newFacingMode = currentFacingMode === 'user' ? 'environment' : 'user';
        
        // Reinitialize camera with new facing mode
        await this.initializeCamera({ facingMode: newFacingMode });
        
        // Restart streaming if it was active
        if (this.isStreaming) {
            this.startStreaming();
        }
    }

    /**
     * Clean up resources
     */
    cleanup() {
        this.stopStreaming();
        
        // Stop all tracks in the stream
        if (this.stream) {
            this.stream.getTracks().forEach(track => track.stop());
        }
        
        // Clear video element source
        if (this.videoElement && this.videoElement.srcObject) {
            this.videoElement.srcObject = null;
        }
        
        // Disconnect WebSocket
        if (this.socket) {
            this.socket.disconnect();
        }
    }
}

// Create global instance
window.wsCamera = new WebSocketCameraHandler();
