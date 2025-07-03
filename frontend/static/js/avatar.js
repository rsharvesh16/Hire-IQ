// avatar.js - Enhanced Avatar visualization and speech functionality

// Global variables
let videoElement;
let videoIsInitialized = false;
let speechSynthesizer;
let selectedVoice = null;
let isSpeaking = false;
let currentUtterance = null;

// Initialize the video avatar
function initializeAvatar(videoId) {
    try {
        videoElement = document.getElementById(videoId);
        if (!videoElement) {
            console.error(`Video element with ID ${videoId} not found`);
            return;
        }
        
        // Update the video source path
        videoElement.src = "/static/assets/interview-ai2.mp4";
        
        // Set video attributes
        videoElement.muted = false; // Ensure video is not muted
        videoElement.load();
        
        // Configure video display properties
        videoElement.style.objectFit = "contain";
        videoElement.style.width = "100%";
        videoElement.style.height = "100%";
        videoElement.style.opacity = "1";
        
        // Add event listeners
        videoElement.addEventListener('ended', handleVideoEnd);
        videoElement.addEventListener('play', () => console.log("Video started playing"));
        videoElement.addEventListener('error', (e) => console.error("Video error:", e));
        
        // Set initialized flag
        videoIsInitialized = true;
        
        // Initialize speech synthesis
        speechSynthesizer = window.speechSynthesis;
        
        // Load voices and initialize
        if (speechSynthesizer.onvoiceschanged !== undefined) {
            speechSynthesizer.onvoiceschanged = loadVoices;
        }
        
        // Initial load
        loadVoices();
        
        // Fallback if voices aren't loaded immediately
        setTimeout(loadVoices, 1000);
        
        console.log("Avatar video initialized successfully");
    } catch (error) {
        console.error("Error initializing avatar:", error);
    }
}

// Load available voices with better filtering
function loadVoices() {
    try {
        const voices = speechSynthesizer.getVoices();
        console.log("Available voices:", voices.length);
        
        if (voices.length === 0) {
            console.log("No voices found, will retry...");
            setTimeout(loadVoices, 500);
            return;
        }
        
        // Select a female voice that works cross-browser
        const preferredVoices = [
            // Common female voices across platforms
            { name: "Samantha", lang: "en-US" },  // macOS/iOS
            { name: "Microsoft Zira", lang: "en-US" },  // Windows
            { name: "Google US English Female", lang: "en-US" },  // Chrome
            { name: "Karen", lang: "en-AU" },  // macOS/iOS
            { name: "Moira", lang: "en-IE" },  // macOS/iOS
            { name: "Tessa", lang: "en-ZA" },  // macOS/iOS
            { name: "Microsoft Susan", lang: "en-US" }  // Windows
        ];
        
        // Try to find one of our preferred voices
        for (const preferred of preferredVoices) {
            const match = voices.find(v => 
                v.name.includes(preferred.name) && 
                v.lang.includes(preferred.lang.split('-')[0])
            );
            
            if (match) {
                selectedVoice = match;
                console.log("Selected preferred voice:", match.name);
                break;
            }
        }
        
        // Fallback: find any female English voice
        if (!selectedVoice) {
            const femaleIndicators = ['female', 'woman', 'girl', 'samantha', 'zira', 'karen', 'susan'];
            
            for (const voice of voices) {
                if (voice.lang.includes('en')) {
                    const lowerName = voice.name.toLowerCase();
                    for (const indicator of femaleIndicators) {
                        if (lowerName.includes(indicator)) {
                            selectedVoice = voice;
                            console.log("Selected fallback female voice:", voice.name);
                            break;
                        }
                    }
                    if (selectedVoice) break;
                }
            }
        }
        
        // Last resort: any English voice
        if (!selectedVoice) {
            selectedVoice = voices.find(v => v.lang.includes('en'));
            console.log("Selected any English voice:", selectedVoice ? selectedVoice.name : "None");
        }
        
        // If we've selected a voice, read the current question
        if (selectedVoice) {
            setTimeout(readCurrentQuestion, 500);
        }
    } catch (error) {
        console.error("Error loading voices:", error);
    }
}

function handleVideoEnd() {
    if (videoElement) {
        videoElement.pause();
        videoElement.currentTime = 0;
    }
}

async function avatarSpeak(text) {
    if (!videoIsInitialized || !videoElement) {
        console.error("Video element not initialized");
        return;
    }
    
    // Stop any current speech
    stopSpeaking();
    
    if (!text || typeof text !== 'string' || text.trim() === '') {
        console.error("Invalid text for speech synthesis");
        return;
    }
    
    try {
        // First ensure the video is ready
        videoElement.currentTime = 0;
        
        // Play the video with autoplay fallbacks
        const playPromise = videoElement.play();
        
        if (playPromise !== undefined) {
            playPromise.catch(error => {
                console.warn("Autoplay prevented:", error);
                
                // Create a one-time interaction handler for the document
                const enableAudio = () => {
                    videoElement.play().then(() => {
                        speakText(text);
                        document.removeEventListener('click', enableAudio);
                        document.removeEventListener('touchstart', enableAudio);
                    }).catch(e => console.error("Video play error after interaction:", e));
                };
                
                document.addEventListener('click', enableAudio, { once: true });
                document.addEventListener('touchstart', enableAudio, { once: true });
                
                console.log("Touch or click anywhere to enable audio");
            }).then(() => {
                // If play was successful, start speaking
                speakText(text);
            });
        }
    } catch (error) {
        console.error("Error in avatarSpeak:", error);
    }
}

function speakText(text) {
    // Create new utterance
    currentUtterance = new SpeechSynthesisUtterance(text);
    isSpeaking = true;
    
    // Use the selected voice
    if (selectedVoice) {
        currentUtterance.voice = selectedVoice;
    } else {
        console.warn("No suitable voice found, using default");
    }
    
    // Set speech parameters
    currentUtterance.pitch = 1.1;    // Slightly higher pitch
    currentUtterance.rate = 0.95;    // Slightly slower rate
    currentUtterance.volume = 1.0;
    
    // Event handlers
    currentUtterance.onstart = () => {
        console.log("Speech started");
        isSpeaking = true;
    };
    
    currentUtterance.onend = () => {
        console.log("Speech ended");
        isSpeaking = false;
        handleVideoEnd();
        currentUtterance = null;
    };
    
    currentUtterance.onerror = (event) => {
        console.error("Speech error:", event.error);
        isSpeaking = false;
        handleVideoEnd();
        currentUtterance = null;
    };
    
    // Speak the text
    speechSynthesizer.speak(currentUtterance);
    
    // Calculate duration for video loop
    const duration = Math.max(3000, text.length * 60); // Approximate duration in ms
    
    // Loop video while speaking
    const loopInterval = setInterval(() => {
        if (videoElement && (videoElement.paused || videoElement.ended) && isSpeaking) {
            videoElement.currentTime = 0;
            videoElement.play().catch(e => console.error("Loop play error:", e));
        }
    }, 100);
    
    // Clean up when done
    setTimeout(() => {
        clearInterval(loopInterval);
        if (!isSpeaking && videoElement) {
            handleVideoEnd();
        }
    }, duration);
}

function stopSpeaking() {
    if (speechSynthesizer) {
        speechSynthesizer.cancel();
    }
    isSpeaking = false;
    currentUtterance = null;
}

function readCurrentQuestion() {
    const questionElement = document.querySelector('.current-question');
    if (questionElement) {
        const questionText = questionElement.textContent || questionElement.innerText;
        console.log("Reading question:", questionText);
        avatarSpeak(questionText);
    } else {
        console.error("No current question element found");
    }
}

function setupQuestionButtons() {
    // Find all navigation buttons
    const navButtons = document.querySelectorAll('.next-question-button, .question-navigation-button, .prev-question-button');
    
    navButtons.forEach(button => {
        button.addEventListener('click', function() {
            // Stop any current speech immediately
            stopSpeaking();
            
            // Add slight delay to allow DOM to update with new question
            setTimeout(readCurrentQuestion, 300);
        });
    });
    
    // Initial question read with delay to allow voices to load
    setTimeout(readCurrentQuestion, 1500);
}

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', function() {
    initializeAvatar('avatar-video');
    setupQuestionButtons();
    
    // Add a listener for user interaction to help with autoplay policies
    const userInteractionHandler = () => {
        // Attempt to initialize audio after user interaction
        if (speechSynthesizer && !selectedVoice) {
            loadVoices();
        }
        
        // Only need this once
        document.removeEventListener('click', userInteractionHandler);
        document.removeEventListener('touchstart', userInteractionHandler);
    };
    
    document.addEventListener('click', userInteractionHandler);
    document.addEventListener('touchstart', userInteractionHandler);
});

// Export to global scope
window.avatarSpeak = avatarSpeak;
window.initializeAvatar = initializeAvatar;
window.readCurrentQuestion = readCurrentQuestion;
window.stopSpeaking = stopSpeaking;