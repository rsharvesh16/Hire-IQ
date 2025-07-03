// interview.js - Main interview functionality

// Global variables
let currentInterviewId;
let currentQuestionId = null;
let currentAnswer = '';
let interviewTimer;
let interviewPaused = false;
let mediaRecorder;
let recordedChunks = [];
let isRecording = false;
let interviewEnded = false;
let speechRecognition;
let interviewData = {
    questions: [],
    score: 0,
    decision: "Pending",
    detailed_feedback: ""
};

// Initialize the interview
function initializeInterview(interviewId) {
    currentInterviewId = interviewId;
    
    // Show the interview prompt
    const interviewPrompt = document.getElementById('interviewPrompt');
    interviewPrompt.classList.add('active');
    
    // Get the first question after 3 seconds
    setTimeout(() => {
        interviewPrompt.classList.remove('active');
        getNextQuestion();
        
        // Start recording after the first question
        startRecording();
        
        // Start speech recognition
        startSpeechRecognition();
    }, 3000);
}

// Get the next question
async function getNextQuestion() {
    try {
        // Show loading state
        document.getElementById('currentQuestion').textContent = 'Loading next question...';
        
        // Prepare form data
        const formData = new FormData();
        if (currentQuestionId !== null) {
            formData.append('current_question_id', currentQuestionId);
        }
        if (currentAnswer) {
            formData.append('answer', currentAnswer);
        }
        
        // Send request to get next question
        const response = await fetch(`/interview/${currentInterviewId}/question`, {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            throw new Error('Failed to get next question');
        }
        
        const questionData = await response.json();
        
        // Update UI with new question
        document.getElementById('currentQuestion').textContent = questionData.question;
        
        // Make avatar speak the question
        speakQuestion(questionData.question);
        
        // Update current question ID
        currentQuestionId = questionData.id;
        
        // Reset current answer
        currentAnswer = '';
        document.getElementById('answerTranscription').textContent = 'Your answer will appear here as you speak...';
        
    } catch (error) {
        console.error('Error getting next question:', error);
        document.getElementById('currentQuestion').textContent = 'Error loading question. Please try again.';
    }
}

// Process and get next question
function processAndGetNextQuestion() {
    if (interviewEnded) return;
    
    // Process current answer if any
    if (currentAnswer.trim()) {
        // Store the question and answer
        interviewData.questions.push({
            id: currentQuestionId,
            question: document.getElementById('currentQuestion').textContent,
            answer: currentAnswer,
            is_follow_up: currentQuestionId.toString().includes('.')
        });
    }
    
    // Get next question
    getNextQuestion();
}

// Start the interview timer
function startInterviewTimer(durationMinutes) {
    let totalSeconds = durationMinutes * 60;
    const timerElement = document.getElementById('timeRemaining');
    
    interviewTimer = setInterval(() => {
        if (!interviewPaused) {
            totalSeconds--;
            
            if (totalSeconds <= 0) {
                clearInterval(interviewTimer);
                endInterview();
                return;
            }
            
            const minutes = Math.floor(totalSeconds / 60);
            const seconds = totalSeconds % 60;
            
            timerElement.textContent = `${minutes}:${seconds.toString().padStart(2, '0')}`;
        }
    }, 1000);
}

// Toggle pause/resume
function togglePause() {
    const pauseBtn = document.getElementById('pauseBtn');
    
    if (interviewPaused) {
        // Resume
        interviewPaused = false;
        pauseBtn.innerHTML = '<i class="fas fa-pause mr-1"></i> Pause';
        // Resume speech recognition
        if (speechRecognition) {
            speechRecognition.start();
        }
    } else {
        // Pause
        interviewPaused = true;
        pauseBtn.innerHTML = '<i class="fas fa-play mr-1"></i> Resume';
        // Pause speech recognition
        if (speechRecognition) {
            speechRecognition.stop();
        }
    }
}

// Show end interview modal
function showEndInterviewModal() {
    document.getElementById('endInterviewModal').classList.remove('hidden');
}

// Hide end interview modal
function hideEndInterviewModal() {
    document.getElementById('endInterviewModal').classList.add('hidden');
}

// End the interview
async function endInterview() {
    if (interviewEnded) return;
    interviewEnded = true;
    
    // Stop timer
    clearInterval(interviewTimer);
    
    // Stop recording
    if (isRecording && mediaRecorder && mediaRecorder.state !== 'inactive') {
        mediaRecorder.stop();
    }
    
    try {
        // Stop speech recognition
        if (speechRecognition) {
            speechRecognition.stop();
        }
        
        // Send complete interview data to server
        const formData = new FormData();
        formData.append('interview_data', JSON.stringify(interviewData));
        
        await fetch(`/interview/${currentInterviewId}/complete`, {
            method: 'POST',
            body: formData
        });
        
        // Redirect to results page
        window.location.href = `/candidate/interview/${currentInterviewId}/complete`;
        
    } catch (error) {
        console.error('Error ending interview:', error);
        alert('Error completing interview. Please try again.');
    }
}

// Start recording audio and video
function startRecording() {
    if (isRecording) return;
    
    try {
        // Access global mediaStream from WebRTC module
        if (!window.mediaStream) {
            console.error('Media stream not available');
            return;
        }
        
        // Create MediaRecorder instance
        mediaRecorder = new MediaRecorder(window.mediaStream, {
            mimeType: 'video/webm;codecs=vp9,opus'
        });
        
        // Event handlers
        mediaRecorder.ondataavailable = (event) => {
            if (event.data.size > 0) {
                recordedChunks.push(event.data);
            }
        };
        
        mediaRecorder.onstop = async () => {
            // Create a blob from recorded chunks
            const recordedBlob = new Blob(recordedChunks, { type: 'video/webm' });
            
            try {
                // Save the recording
                const formData = new FormData();
                formData.append('video_data', recordedBlob);
                
                await fetch(`/interview/${currentInterviewId}/save-recording`, {
                    method: 'POST',
                    body: formData
                });
                
                console.log('Recording saved successfully');
                
            } catch (error) {
                console.error('Error saving recording:', error);
            }
        };
        
        // Start recording
        mediaRecorder.start(1000); // Collect data every second
        isRecording = true;
        
    } catch (error) {
        console.error('Error starting recording:', error);
    }
}

// Speech recognition for transcribing answers
function startSpeechRecognition() {
    // Check browser support
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
        console.error('Speech recognition not supported in this browser');
        document.getElementById('answerTranscription').textContent = 'Speech recognition not supported in your browser. Please try another browser.';
        return;
    }
    
    // Initialize speech recognition
    speechRecognition = new SpeechRecognition();
    speechRecognition.continuous = true;
    speechRecognition.interimResults = true;
    speechRecognition.lang = 'en-US';
    
    // Set up event handlers
    speechRecognition.onresult = (event) => {
        if (interviewPaused || interviewEnded) return;
        
        let interimTranscript = '';
        let finalTranscript = currentAnswer;
        
        for (let i = event.resultIndex; i < event.results.length; i++) {
            const transcript = event.results[i][0].transcript;
            
            if (event.results[i].isFinal) {
                finalTranscript += ' ' + transcript;
                
                // Process audio chunk for transcription
                processAudioChunk();
            } else {
                interimTranscript += transcript;
            }
        }
        
        // Update current answer with final transcript
        currentAnswer = finalTranscript.trim();
        
        // Update UI
        document.getElementById('answerTranscription').textContent = currentAnswer + ' ' + interimTranscript;
    };
    
    speechRecognition.onerror = (event) => {
        console.error('Speech recognition error:', event.error);
    };
    
    speechRecognition.onend = () => {
        if (!interviewPaused && !interviewEnded) {
            // Restart if not paused or ended
            speechRecognition.start();
        }
    };
    
    // Start speech recognition
    speechRecognition.start();
}

// Process audio chunk with backend for better transcription
async function processAudioChunk() {
    // This would typically send audio data to the backend for processing
    // For now, we're using the browser's speech recognition
    // In a real implementation, you would process the audio on the server
    
    if (!window.mediaStream) return;
    
    try {
        // Create a recorder for this audio chunk
        const audioTrack = window.mediaStream.getAudioTracks()[0];
        if (!audioTrack) return;
        
        // Create a media recorder for the audio track only
        const audioStream = new MediaStream([audioTrack]);
        const audioRecorder = new MediaRecorder(audioStream, { mimeType: 'audio/webm' });
        
        const audioChunks = [];
        
        audioRecorder.ondataavailable = (event) => {
            if (event.data.size > 0) {
                audioChunks.push(event.data);
            }
        };
        
        audioRecorder.onstop = async () => {
            // Create blob from chunks
            const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
            
            // Send to server for processing
            const formData = new FormData();
            formData.append('audio_data', audioBlob);
            
            try {
                const response = await fetch(`/interview/${currentInterviewId}/process-audio`, {
                    method: 'POST',
                    body: formData
                });
                
                if (response.ok) {
                    const data = await response.json();
                    if (data.transcription) {
                        // Update with more accurate transcription from server
                        // In practice, we'd merge or compare this with our local transcription
                        console.log('Server transcription:', data.transcription);
                    }
                }
            } catch (error) {
                console.error('Error processing audio chunk:', error);
            }
        };
        
        // Record for a short time
        audioRecorder.start();
        setTimeout(() => {
            if (audioRecorder.state !== 'inactive') {
                audioRecorder.stop();
            }
        }, 5000); // Record 5 seconds at a time
        
    } catch (error) {
        console.error('Error in processing audio chunk:', error);
    }
}

// Make the avatar speak the question
function speakQuestion(question) {
    // Call the avatar's speak function from avatar.js
    if (window.avatarSpeak) {
        window.avatarSpeak(question);
    } else {
        console.error('Avatar speak function not available');
    }
}