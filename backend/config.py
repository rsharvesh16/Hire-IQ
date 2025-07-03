import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
load_dotenv()

# Base configuration
class Config:
    # API Keys
    AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
    AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
    
    # Database
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./hireiq.db")
    
    # Application settings
    SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-for-development")
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours
    
    # File storage paths
    UPLOAD_DIR = Path("uploads")
    RESUME_DIR = UPLOAD_DIR / "resumes"
    AUDIO_DIR = UPLOAD_DIR / "audio"
    VIDEO_DIR = UPLOAD_DIR / "videos"
    REPORT_DIR = UPLOAD_DIR / "reports"
    
    # LLM settings
    MAX_QUESTIONS = 15
    INTERVIEW_MAX_DURATION = 30  # minutes
    
    # Create directories if they don't exist
    @classmethod
    def setup(cls):
        cls.RESUME_DIR.mkdir(parents=True, exist_ok=True)
        cls.AUDIO_DIR.mkdir(parents=True, exist_ok=True)
        cls.VIDEO_DIR.mkdir(parents=True, exist_ok=True)
        cls.REPORT_DIR.mkdir(parents=True, exist_ok=True)

# Initialize directories
Config.setup()