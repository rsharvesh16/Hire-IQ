from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List, Optional
import hashlib
import uuid

from . import models, schema

# User operations
def create_user(db: Session, user: schema.UserCreate):
    # Create salt and hash password
    salt = uuid.uuid4().hex
    hashed_password = hashlib.sha256(salt.encode() + user.password.encode()).hexdigest() + ':' + salt
    
    db_user = models.User(
        name=user.name,
        email=user.email,
        hashed_password=hashed_password,
        user_type=user.user_type
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def authenticate_user(db: Session, email: str, password: str):
    user = get_user_by_email(db, email)
    if not user:
        return None
    
    # Check password
    hashed_password, salt = user.hashed_password.split(':')
    if hashed_password == hashlib.sha256(salt.encode() + password.encode()).hexdigest():
        return user
    return None

# Interview operations
def create_interview(db: Session, interview: schema.InterviewCreate):
    db_interview = models.Interview(**interview.dict())
    db.add(db_interview)
    db.commit()
    db.refresh(db_interview)
    return db_interview

def get_interview(db: Session, interview_id: int):
    return db.query(models.Interview).filter(models.Interview.id == interview_id).first()

def get_interviews_by_hr(db: Session, hr_id: int):
    return db.query(models.Interview).filter(models.Interview.hr_id == hr_id).all()

def get_interviews_by_candidate(db: Session, candidate_id: int):
    return db.query(models.Interview).filter(models.Interview.candidate_id == candidate_id).all()

def update_interview_status(db: Session, interview_id: int, status: str):
    db_interview = get_interview(db, interview_id)
    if db_interview:
        db_interview.status = status
        db.commit()
        db.refresh(db_interview)
    return db_interview

# Interview Question operations
def create_interview_question(db: Session, question: schema.InterviewQuestionCreate):
    db_question = models.InterviewQuestion(**question.dict())
    db.add(db_question)
    db.commit()
    db.refresh(db_question)
    return db_question

def get_interview_questions(db: Session, interview_id: int):
    return db.query(models.InterviewQuestion).filter(models.InterviewQuestion.interview_id == interview_id).all()

def update_interview_question(db: Session, question_id: int, answer: str):
    db_question = db.query(models.InterviewQuestion).filter(models.InterviewQuestion.id == question_id).first()
    if db_question:
        db_question.answer = answer
        db.commit()
        db.refresh(db_question)
    return db_question

# Interview Result operations
def create_interview_result(db: Session, result: schema.InterviewResultCreate):
    db_result = models.InterviewResult(**result.dict())
    db.add(db_result)
    db.commit()
    db.refresh(db_result)
    return db_result

def get_interview_result(db: Session, interview_id: int):
    return db.query(models.InterviewResult).filter(models.InterviewResult.interview_id == interview_id).first()