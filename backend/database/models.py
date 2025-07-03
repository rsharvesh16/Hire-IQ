from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    user_type = Column(String, nullable=False)  # "HR" or "Candidate"
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    hr_interviews = relationship("Interview", foreign_keys="Interview.hr_id", back_populates="hr")
    candidate_interviews = relationship("Interview", foreign_keys="Interview.candidate_id", back_populates="candidate")

class Interview(Base):
    __tablename__ = "interviews"

    id = Column(Integer, primary_key=True, index=True)
    hr_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    candidate_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    candidate_name = Column(String, nullable=False)
    job_role = Column(String, nullable=False)
    difficulty = Column(String, nullable=False)  # "Very Easy", "Easy", "Medium", "Hard"
    scheduled_date = Column(DateTime, nullable=False)
    duration = Column(Integer, nullable=False)  # in minutes
    resume_path = Column(String, nullable=False)
    job_description = Column(Text, nullable=False)
    custom_questions = Column(JSON, nullable=True)
    status = Column(String, nullable=False)  # "scheduled", "in_progress", "completed", "cancelled"
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    hr = relationship("User", foreign_keys=[hr_id], back_populates="hr_interviews")
    candidate = relationship("User", foreign_keys=[candidate_id], back_populates="candidate_interviews")
    results = relationship("InterviewResult", back_populates="interview", uselist=False)
    questions = relationship("InterviewQuestion", back_populates="interview")

class InterviewQuestion(Base):
    __tablename__ = "interview_questions"

    id = Column(Integer, primary_key=True, index=True)
    interview_id = Column(Integer, ForeignKey("interviews.id"), nullable=False)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=func.now())
    follow_up_to = Column(Integer, ForeignKey("interview_questions.id"), nullable=True)
    
    # Relationships
    interview = relationship("Interview", back_populates="questions")
    follow_ups = relationship("InterviewQuestion", foreign_keys=[follow_up_to])

class InterviewResult(Base):
    __tablename__ = "interview_results"

    id = Column(Integer, primary_key=True, index=True)
    interview_id = Column(Integer, ForeignKey("interviews.id"), unique=True, nullable=False)
    score = Column(Float, nullable=False)  # 0-100
    decision = Column(String, nullable=False)  # "Fit" or "Not Fit"
    report_path = Column(String, nullable=False)
    video_path = Column(String, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    interview = relationship("Interview", back_populates="results")