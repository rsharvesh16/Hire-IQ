// webrtc.js - Handle WebRTC for video and audio capture

// Global variables
window.mediaStream = null;
const constraints = {
    audio: true,
    video: {
        width: { ideal: 1280 },
        height: { ideal: 720 },
        facingMode: "user"
    }
};

// Initialize WebRTC for video/audio capture
async function initializeWebRTC(videoElementId) {
    const videoElement = document.getElementById(videoElementId);
    
    if (!videoElement) {
        console.error(`Video element with ID ${videoElementId} not found`);
        return;
    }
    
    try {
        // Request permission and access media devices
        window.mediaStream = await navigator.mediaDevices.getUserMedia(constraints);
        
        // Connect the stream to the video element
        videoElement.srcObject = window.mediaStream;
        
        // Log success
        console.log('Media stream created and connected to video element');
        
        // Add event listeners for tracking media state
        trackMediaState(window.mediaStream);
        
    } catch (error) {
        console.error('Error accessing media devices:', error);
        alert('Failed to access camera and microphone. Please ensure permissions are granted and try again.');
    }
}

// Track the state of media tracks
function trackMediaState(mediaStream) {
    if (!mediaStream) return;
    
    const videoTrack = mediaStream.getVideoTracks()[0];
    const audioTrack = mediaStream.getAudioTracks()[0];
    
    if (videoTrack) {
        videoTrack.onended = () => {
            console.warn('Video track ended');
            // Attempt to recover
            restartVideoTrack();
        };
        
        videoTrack.onmute = () => {
            console.warn('Video track muted');
        };
        
        videoTrack.onunmute = () => {
            console.log('Video track unmuted');
        };
    }
    
    if (audioTrack) {
        audioTrack.onended = () => {
            console.warn('Audio track ended');
            // Attempt to recover
            restartAudioTrack();
        };
        
        audioTrack.onmute = () => {
            console.warn('Audio track muted');
        };
        
        audioTrack.onunmute = () => {
            console.log('Audio track unmuted');
        };
    }
}

// Attempt to restart video track if it fails
async function restartVideoTrack() {
    try {
        const newStream = await navigator.mediaDevices.getUserMedia({ video: constraints.video });
        const newVideoTrack = newStream.getVideoTracks()[0];
        
        const videoElement = document.getElementById('userVideo');
        if (videoElement && videoElement.srcObject) {
            const currentStream = videoElement.srcObject;
            
            // Remove old video track
            const oldVideoTrack = currentStream.getVideoTracks()[0];
            if (oldVideoTrack) {
                currentStream.removeTrack(oldVideoTrack);
            }
            
            // Add new video track
            currentStream.addTrack(newVideoTrack);
            
            // Update global stream
            window.mediaStream = currentStream;
            
            console.log('Video track restarted successfully');
        }
    } catch (error) {
        console.error('Failed to restart video track:', error);
    }
}

// Attempt to restart audio track if it fails
async function restartAudioTrack() {
    try {
        const newStream = await navigator.mediaDevices.getUserMedia({ audio: true });
        const newAudioTrack = newStream.getAudioTracks()[0];
        
        const videoElement = document.getElementById('userVideo');
        if (videoElement && videoElement.srcObject) {
            const currentStream = videoElement.srcObject;
            
            // Remove old audio track
            const oldAudioTrack = currentStream.getAudioTracks()[0];
            if (oldAudioTrack) {
                currentStream.removeTrack(oldAudioTrack);
            }
            
            // Add new audio track
            currentStream.addTrack(newAudioTrack);
            
            // Update global stream
            window.mediaStream = currentStream;
            
            console.log('Audio track restarted successfully');
        }
    } catch (error) {
        console.error('Failed to restart audio track:', error);
    }
}

// Stop all media tracks
function stopMediaTracks() {
    if (!window.mediaStream) return;
    
    window.mediaStream.getTracks().forEach(track => {
        track.stop();
    });
    
    window.mediaStream = null;
    console.log('Media tracks stopped');
}

// Clean up on page unload
window.addEventListener('beforeunload', () => {
    stopMediaTracks();
});