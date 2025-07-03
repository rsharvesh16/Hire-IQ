# backend/utils/video_processor.py
import cv2
import numpy as np
import os
import time
import uuid
import json
import logging
from typing import Dict, Any, List, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)

# Face detection cascades
try:
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')
except Exception as e:
    logger.error(f"Error loading cascades: {e}")
    face_cascade = None
    eye_cascade = None

class VideoProcessor:
    def __init__(self, interview_id: int, storage_dir: str = "uploads/videos"):
        """
        Initialize the video processor
        
        Args:
            interview_id: ID of the interview
            storage_dir: Directory to store video files
        """
        self.interview_id = interview_id
        self.storage_dir = storage_dir
        os.makedirs(storage_dir, exist_ok=True)
        
        # Analysis results
        self.eye_contact_scores = []
        self.facial_expression_scores = []
        self.attention_scores = []
        self.anomalies = []
        
        # Create a subdirectory for the interview
        self.interview_dir = os.path.join(storage_dir, f"interview_{interview_id}")
        os.makedirs(self.interview_dir, exist_ok=True)
        
        # Initialize analysis file
        self.analysis_file = os.path.join(self.interview_dir, "analysis.json")
        if not os.path.exists(self.analysis_file):
            with open(self.analysis_file, 'w') as f:
                json.dump({
                    "interview_id": interview_id,
                    "analysis_data": [],
                    "summary": {},
                    "anomalies": []
                }, f)
    
    def save_video_chunk(self, video_data: bytes) -> str:
        """
        Save a video chunk to disk
        
        Args:
            video_data: Raw video data
            
        Returns:
            Path to the saved video file
        """
        timestamp = int(time.time())
        chunk_filename = f"chunk_{timestamp}_{uuid.uuid4().hex[:8]}.webm"
        chunk_path = os.path.join(self.interview_dir, chunk_filename)
        
        try:
            with open(chunk_path, 'wb') as f:
                f.write(video_data)
            logger.info(f"Saved video chunk: {chunk_path}")
            return chunk_path
        except Exception as e:
            logger.error(f"Error saving video chunk: {e}")
            return ""
    
    def analyze_video_frame(self, frame: np.ndarray, timestamp: float) -> Dict[str, Any]:
        """
        Analyze a video frame for facial expressions, eye contact, etc.
        
        Args:
            frame: Video frame as numpy array
            timestamp: Timestamp of the frame
            
        Returns:
            Dictionary with analysis results
        """
        if face_cascade is None:
            return {"error": "Face detection not available"}
        
        try:
            # Convert to grayscale for detection
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Detect faces
            faces = face_cascade.detectMultiScale(gray, 1.3, 5)
            
            # Analysis results
            result = {
                "timestamp": timestamp,
                "faces_detected": len(faces),
                "eye_contact": 0.0,
                "facial_expression": "neutral",
                "attention_score": 0.0,
                "anomaly": False,
                "anomaly_reason": None
            }
            
            if len(faces) == 0:
                result["anomaly"] = True
                result["anomaly_reason"] = "No face detected"
                self.anomalies.append({
                    "timestamp": timestamp,
                    "reason": "No face detected"
                })
                return result
            
            if len(faces) > 1:
                result["anomaly"] = True
                result["anomaly_reason"] = "Multiple faces detected"
                self.anomalies.append({
                    "timestamp": timestamp,
                    "reason": "Multiple faces detected"
                })
            
            # Process the primary face (assuming the largest is the candidate)
            face_sizes = [w*h for (x, y, w, h) in faces]
            primary_face_idx = face_sizes.index(max(face_sizes))
            x, y, w, h = faces[primary_face_idx]
            
            # Extract the face region
            face_region = gray[y:y+h, x:x+w]
            
            # Detect eyes
            eyes = eye_cascade.detectMultiScale(face_region)
            result["eyes_detected"] = len(eyes)
            
            # Calculate eye contact score (simplified)
            # In a real system, this would use more sophisticated gaze tracking
            if len(eyes) >= 2:
                # Check if eyes are roughly in the middle third of the frame width
                frame_center_x = frame.shape[1] / 2
                frame_width_third = frame.shape[1] / 3
                
                eye_positions = []
                for (ex, ey, ew, eh) in eyes:
                    eye_center_x = x + ex + ew/2
                    eye_positions.append(eye_center_x)
                
                # Calculate average eye position
                avg_eye_x = sum(eye_positions) / len(eye_positions)
                
                # Check if looking roughly at camera
                if frame_center_x - frame_width_third <= avg_eye_x <= frame_center_x + frame_width_third:
                    result["eye_contact"] = 0.8
                else:
                    result["eye_contact"] = 0.3
            else:
                result["eye_contact"] = 0.0
                if len(faces) > 0:  # Face detected but no eyes
                    result["anomaly"] = True
                    result["anomaly_reason"] = "Eyes not visible"
                    self.anomalies.append({
                        "timestamp": timestamp,
                        "reason": "Eyes not visible"
                    })
            
            # Append to eye contact scores
            self.eye_contact_scores.append(result["eye_contact"])
            
            # For demonstration: simple attention score based on face position and eyes
            # In a real system, this would use more sophisticated attention tracking
            attention_score = 0.0
            if len(faces) == 1 and len(eyes) >= 2:
                # Face centered in frame is good
                face_center_x = x + w/2
                face_center_y = y + h/2
                
                face_center_score = 1.0 - min(
                    abs(face_center_x - frame.shape[1]/2) / (frame.shape[1]/2),
                    abs(face_center_y - frame.shape[0]/2) / (frame.shape[0]/2)
                )
                
                attention_score = (face_center_score * 0.5) + (result["eye_contact"] * 0.5)
            
            result["attention_score"] = attention_score
            self.attention_scores.append(attention_score)
            
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing video frame: {e}")
            return {"error": str(e)}
    
    def analyze_video_chunk(self, video_path: str, frame_interval: int = 30) -> List[Dict[str, Any]]:
        """
        Analyze a video chunk by sampling frames at the given interval
        
        Args:
            video_path: Path to the video file
            frame_interval: Number of frames to skip between analyses
            
        Returns:
            List of frame analysis results
        """
        try:
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                logger.error(f"Could not open video: {video_path}")
                return []
            
            frame_count = 0
            analysis_results = []
            
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Only analyze every frame_interval frames
                if frame_count % frame_interval == 0:
                    timestamp = cap.get(cv2.CAP_PROP_POS_MSEC) / 1000.0
                    result = self.analyze_video_frame(frame, timestamp)
                    analysis_results.append(result)
                
                frame_count += 1
            
            cap.release()
            
            # Save analysis results
            self._append_analysis_results(analysis_results)
            
            return analysis_results
            
        except Exception as e:
            logger.error(f"Error analyzing video chunk: {e}")
            return []
    
    def _append_analysis_results(self, results: List[Dict[str, Any]]) -> None:
        """
        Append analysis results to the analysis file
        
        Args:
            results: List of analysis results
        """
        try:
            # Load existing analysis
            with open(self.analysis_file, 'r') as f:
                analysis_data = json.load(f)
            
            # Append new results
            analysis_data["analysis_data"].extend(results)
            
            # Update anomalies
            analysis_data["anomalies"] = self.anomalies
            
            # Save updated analysis
            with open(self.analysis_file, 'w') as f:
                json.dump(analysis_data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error appending analysis results: {e}")
    
    def generate_summary(self) -> Dict[str, Any]:
        """
        Generate a summary of the video analysis
        
        Returns:
            Dictionary with summary statistics
        """
        try:
            # Load analysis data
            with open(self.analysis_file, 'r') as f:
                analysis_data = json.load(f)
            
            # Calculate summary statistics
            eye_contact = self.eye_contact_scores
            attention = self.attention_scores
            anomalies = self.anomalies
            
            summary = {
                "interview_id": self.interview_id,
                "average_eye_contact": sum(eye_contact) / max(len(eye_contact), 1),
                "average_attention": sum(attention) / max(len(attention), 1),
                "anomaly_count": len(anomalies),
                "total_frames_analyzed": len(analysis_data["analysis_data"]),
                "timestamp": datetime.now().isoformat()
            }
            
            # Update the analysis file with summary
            analysis_data["summary"] = summary
            with open(self.analysis_file, 'w') as f:
                json.dump(analysis_data, f, indent=2)
            
            return summary
            
        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            return {}
    
    def extract_key_moments(self, threshold: float = 0.3) -> List[Dict[str, Any]]:
        """
        Extract key moments from the video analysis
        
        Args:
            threshold: Threshold for determining significant attention changes
            
        Returns:
            List of key moments with timestamps
        """
        try:
            # Load analysis data
            with open(self.analysis_file, 'r') as f:
                analysis_data = json.load(f)
            
            key_moments = []
            prev_attention = None
            
            for frame in analysis_data["analysis_data"]:
                timestamp = frame.get("timestamp", 0)
                # backend/utils/video_processor.py (continued)
                attention = frame.get("attention_score", 0.0)
                
                # Check for significant attention changes
                if prev_attention is not None and abs(attention - prev_attention) > threshold:
                    key_moments.append({
                        "timestamp": timestamp,
                        "type": "attention_change",
                        "from": prev_attention,
                        "to": attention,
                        "description": "Significant change in candidate attention"
                    })
                
                # Check for anomalies
                if frame.get("anomaly", False):
                    key_moments.append({
                        "timestamp": timestamp,
                        "type": "anomaly",
                        "reason": frame.get("anomaly_reason", "Unknown anomaly"),
                        "description": f"Anomaly detected: {frame.get('anomaly_reason', 'Unknown')}"
                    })
                
                prev_attention = attention
            
            return key_moments
            
        except Exception as e:
            logger.error(f"Error extracting key moments: {e}")
            return []
    
    def generate_thumbnails(self, interval_seconds: int = 60) -> List[str]:
        """
        Generate thumbnails from the video at the specified interval
        
        Args:
            interval_seconds: Interval between thumbnails in seconds
            
        Returns:
            List of paths to the generated thumbnails
        """
        try:
            # Find all video chunks in the interview directory
            video_files = [f for f in os.listdir(self.interview_dir) if f.startswith("chunk_") and f.endswith(".webm")]
            if not video_files:
                logger.error("No video files found for thumbnail generation")
                return []
            
            # Sort by timestamp in filename
            video_files.sort()
            
            # Create thumbnails directory
            thumbnails_dir = os.path.join(self.interview_dir, "thumbnails")
            os.makedirs(thumbnails_dir, exist_ok=True)
            
            thumbnail_paths = []
            current_time = 0
            
            for video_file in video_files:
                video_path = os.path.join(self.interview_dir, video_file)
                cap = cv2.VideoCapture(video_path)
                
                if not cap.isOpened():
                    logger.error(f"Could not open video for thumbnails: {video_path}")
                    continue
                
                fps = cap.get(cv2.CAP_PROP_FPS)
                duration = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) / fps)
                
                for sec in range(0, duration, interval_seconds):
                    # Position the video at the target second
                    cap.set(cv2.CAP_PROP_POS_MSEC, sec * 1000)
                    ret, frame = cap.read()
                    
                    if ret:
                        # Save the thumbnail
                        thumbnail_path = os.path.join(
                            thumbnails_dir, 
                            f"thumbnail_{current_time + sec}.jpg"
                        )
                        cv2.imwrite(thumbnail_path, frame)
                        thumbnail_paths.append(thumbnail_path)
                
                current_time += duration
                cap.release()
            
            return thumbnail_paths
            
        except Exception as e:
            logger.error(f"Error generating thumbnails: {e}")
            return []
    
    def merge_video_chunks(self) -> str:
        """
        Merge all video chunks into a single video file
        
        Returns:
            Path to the merged video file
        """
        try:
            # Find all video chunks in the interview directory
            video_files = [f for f in os.listdir(self.interview_dir) if f.startswith("chunk_") and f.endswith(".webm")]
            if not video_files:
                logger.error("No video files found for merging")
                return ""
            
            # Sort by timestamp in filename
            video_files.sort()
            
            # Create a file list for ffmpeg
            file_list_path = os.path.join(self.interview_dir, "file_list.txt")
            with open(file_list_path, 'w') as f:
                for video_file in video_files:
                    f.write(f"file '{os.path.join(self.interview_dir, video_file)}'\n")
            
            # Output file path
            output_path = os.path.join(self.interview_dir, f"interview_{self.interview_id}_complete.webm")
            
            # Use ffmpeg to concatenate files
            import subprocess
            cmd = [
                "ffmpeg", 
                "-f", "concat", 
                "-safe", "0", 
                "-i", file_list_path, 
                "-c", "copy", 
                output_path
            ]
            
            subprocess.run(cmd, check=True)
            
            # Clean up file list
            os.remove(file_list_path)
            
            return output_path
            
        except Exception as e:
            logger.error(f"Error merging video chunks: {e}")
            return ""