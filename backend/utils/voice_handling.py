import boto3
import json
import base64
import os
import logging
from typing import Dict, Any, Optional
import numpy as np
import soundfile as sf
import wave
import io

logger = logging.getLogger(__name__)

class VoiceProcessor:
    def __init__(self):
        # Initialize AWS Bedrock client
        self.bedrock_runtime = boto3.client(
            service_name="bedrock-runtime",
            region_name=os.getenv("AWS_REGION", "us-east-1"),
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        )
    
    def transcribe_audio(self, audio_file_path: str) -> str:
        """
        Transcribe audio using AWS Bedrock Nova Sonic model
        
        Args:
            audio_file_path: Path to the audio file
            
        Returns:
            Transcribed text
        """
        try:
            # Read the audio file
            with open(audio_file_path, "rb") as audio_file:
                audio_bytes = audio_file.read()
            
            # Encode audio bytes to base64
            audio_base64 = base64.b64encode(audio_bytes).decode("utf-8")
            
            # Prepare request body for AWS Bedrock Nova Sonic
            request_body = {
                "inputText": "",  # No input text for pure transcription
                "inputAudio": audio_base64,
                "taskType": "TRANSCRIPTION"
            }
            
            # Call AWS Bedrock Nova Sonic model
            response = self.bedrock_runtime.invoke_model(
                modelId="amazon.nova-sonic-v1:0",  # Correct Nova Sonic model ID
                contentType="application/json",
                accept="application/json",
                body=json.dumps(request_body)
            )
            
            # Parse response
            response_body = json.loads(response["body"].read().decode("utf-8"))
            transcription = response_body.get("results", {}).get("transcription", "")
            
            return transcription
            
        except Exception as e:
            logger.error(f"Error transcribing audio: {e}")
            return ""
    
    def text_to_speech(self, text: str, output_file_path: str) -> str:
        """
        Convert text to speech using AWS Bedrock TTS model
        
        Args:
            text: Text to convert to speech
            output_file_path: Path to save the audio file
            
        Returns:
            Path to the generated audio file
        """
        try:
            # Prepare request body for AWS Bedrock
            request_body = {
                "text": text,
                "voice": "alloy",  # Default voice
                "accept_format": "pcm"
            }
            
            # Call AWS Bedrock TTS model
            response = self.bedrock_runtime.invoke_model(
                modelId="amazon.titan-tts-expressive",  # TTS model ID
                contentType="application/json",
                accept="audio/pcm",
                body=json.dumps(request_body)
            )
            
            # Parse response
            audio_bytes = response["body"].read()
            
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(output_file_path), exist_ok=True)
            
            # Save audio to file
            with open(output_file_path, "wb") as audio_file:
                audio_file.write(audio_bytes)
            
            return output_file_path
            
        except Exception as e:
            logger.error(f"Error generating speech: {e}")
            return ""


# Initialize voice processor
voice_processor = VoiceProcessor()

def set_up_sonic() -> VoiceProcessor:
    """
    Set up and return the voice processor
    
    Returns:
        Initialized VoiceProcessor instance
    """
    return voice_processor

def process_audio(audio_file_path: str) -> str:
    """
    Process audio file and return transcription
    
    Args:
        audio_file_path: Path to the audio file
        
    Returns:
        Transcribed text
    """
    return voice_processor.transcribe_audio(audio_file_path)

def text_to_speech(text: str, output_file_path: str) -> str:
    """
    Convert text to speech
    
    Args:
        text: Text to convert to speech
        output_file_path: Path to save the audio file
        
    Returns:
        Path to the generated audio file
    """
    return voice_processor.text_to_speech(text, output_file_path)

def convert_webm_to_wav(webm_file_path: str, wav_file_path: str) -> str:
    """
    Convert WebM audio file to WAV format
    
    Args:
        webm_file_path: Path to the WebM file
        wav_file_path: Path to save the WAV file
        
    Returns:
        Path to the converted WAV file
    """
    try:
        import subprocess
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(wav_file_path), exist_ok=True)
        
        # Use ffmpeg to convert WebM to WAV
        subprocess.run([
            "ffmpeg", "-i", webm_file_path, "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1", wav_file_path
        ], check=True)
        
        return wav_file_path
        
    except Exception as e:
        logger.error(f"Error converting WebM to WAV: {e}")
        return ""