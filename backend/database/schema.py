from pydantic import BaseModel, EmailStr, validator, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

# User schemas
class UserBase(BaseModel):
    email: EmailStr
    name: str

class UserCreate(UserBase):
    password: str
    confirm_password: str
    user_type: str
    
    @validator('confirm_password')
    def passwords_match(cls, v, values, **kwargs):
        if 'password' in values and v != values['password']:
            raise ValueError('Passwords do not match')
        return v
    
    @validator('user_type')
    def valid_user_type(cls, v):
        if v not in ["HR", "Candidate"]:
            raise ValueError('User type must be either HR or Candidate')
        return v

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(UserBase):
    id: int
    user_type: str
    created_at: datetime
    
    class Config:
        orm_mode = True

# Interview schemas
class InterviewBase(BaseModel):
    hr_id: int
    candidate_id: int
    candidate_name: str
    job_role: str
    difficulty: str
    scheduled_date: datetime
    duration: int
    job_description: str
    custom_questions: Optional[List[str]] = None

class InterviewCreate(InterviewBase):
    resume_path: str
    status: str = "scheduled"
    
    @validator('difficulty')
    def valid_difficulty(cls, v):
        if v not in ["Very Easy", "Easy", "Medium", "Hard"]:
            raise ValueError('Difficulty must be one of: Very Easy, Easy, Medium, Hard')
        return v
    
    @validator('status')
    def valid_status(cls, v):
        if v not in ["scheduled", "in_progress", "completed", "cancelled"]:
            raise ValueError('Status must be one of: scheduled, in_progress, completed, cancelled')
        return v

class InterviewUpdate(BaseModel):
    status: Optional[str] = None
    
    @validator('status')
    def valid_status(cls, v):
        if v not in ["scheduled", "in_progress", "completed", "cancelled"]:
            raise ValueError('Status must be one of: scheduled, in_progress, completed, cancelled')
        return v

class InterviewResponse(InterviewBase):
    id: int
    resume_path: str
    status: str
    created_at: datetime
    
    class Config:
        orm_mode = True

# Interview Question schemas
class InterviewQuestionBase(BaseModel):
    interview_id: int
    question: str
    follow_up_to: Optional[int] = None

class InterviewQuestionCreate(InterviewQuestionBase):
    pass

class InterviewQuestionUpdate(BaseModel):
    answer: str

class InterviewQuestionResponse(InterviewQuestionBase):
    id: int
    answer: Optional[str] = None
    timestamp: datetime
    
    class Config:
        orm_mode = True

# Interview Result schemas
class InterviewResultBase(BaseModel):
    interview_id: int
    score: float = Field(..., ge=0, le=100)
    decision: str
    notes: Optional[str] = None

class InterviewResultCreate(InterviewResultBase):
    report_path: str
    video_path: Optional[str] = None
    
    @validator('decision')
    def valid_decision(cls, v):
        if v not in ["Fit", "Not Fit"]:
            raise ValueError('Decision must be either Fit or Not Fit')
        return v

class InterviewResultResponse(InterviewResultBase):
    id: int
    report_path: str
    video_path: Optional[str] = None
    created_at: datetime
    
    class Config:
        orm_mode = True