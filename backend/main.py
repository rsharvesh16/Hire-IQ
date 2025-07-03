from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form, status, Request, Response
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional, List
import shutil
import os
import uuid
import json
from pydantic import BaseModel
from starlette.responses import RedirectResponse

# Import project modules
from database.database import get_db, engine, Base
from database.models import User, Interview, InterviewResult
from database.schema import UserCreate, UserLogin, InterviewCreate, InterviewUpdate, InterviewResultCreate
from database.crud import (
    create_user, get_user_by_email, authenticate_user, create_interview,
    get_interviews_by_hr, get_interviews_by_candidate, get_interview,
    update_interview_status, create_interview_result, get_interview_result
)
from llm.agent import LLMAgent
from utils.report_generator import generate_pdf_report
from utils.voice_handling import set_up_sonic, process_audio
from utils.resume_parser import parse_resume

from starlette.middleware.sessions import SessionMiddleware


# Initialize FastAPI app
app = FastAPI(title="HireIQ API")


# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(SessionMiddleware, secret_key="lkadjdflkjvlkajddf")

# Mount static files
app.mount("/static", StaticFiles(directory="../frontend/static"), name="static")

# Set up templates
templates = Jinja2Templates(directory="../frontend/templates")

# Create database tables
Base.metadata.create_all(bind=engine)

# Set up OAuth2 password bearer
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Dependency to get current user
# Replace the get_current_user dependency function in your FastAPI app

async def get_current_user(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Get the current user from session or cookie.
    """
    user_email = request.session.get("user_email")
    if not user_email:
        user_email = request.cookies.get("auth_token")
        if not user_email:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated"
            )
        # Add to session for future requests
        request.session["user_email"] = user_email
    
    user = get_user_by_email(db, user_email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )
    
    return user
    
    # Try with cookie last
    auth_token = request.cookies.get("auth_token")
    if auth_token:
        user = get_user_by_email(db, auth_token)
        if user:
            return user
    
    # No authentication method worked
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
        headers={"WWW-Authenticate": "Bearer"},
    )

# Initialize LLMAgent
llm_agent = LLMAgent()

# Root endpoint
@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})

# Authentication endpoints
@app.post("/register")
async def register(user: UserCreate, db: Session = Depends(get_db)):
    db_user = get_user_by_email(db, user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    new_user = create_user(db, user)
    return {"message": "User registered successfully", "user_id": new_user.id, "user_type": new_user.user_type}

@app.post("/token")
async def login(
    request: Request,
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(), 
    db: Session = Depends(get_db)
):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Set session variable
    request.session["user_email"] = user.email
    
    # Set auth cookie directly in response
    response.set_cookie(
        key="auth_token",
        value=user.email,
        httponly=True,
        max_age=3600,
        path="/"
    )
    
    # Return token response
    return {"access_token": user.email, "token_type": "bearer", "user_type": user.user_type}

@app.post("/login", response_class=HTMLResponse)
async def login_form(
    request: Request,
    response: Response,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    user = authenticate_user(db, email, password)
    if not user:
        return templates.TemplateResponse(
            "login.html", 
            {"request": request, "error": "Invalid credentials"}
        )
    
    # Set both session and cookie
    request.session["user_email"] = user.email
    response.set_cookie(
        key="auth_token",
        value=user.email,
        httponly=True,
        max_age=3600,
        secure=False,  # Set to True in production with HTTPS
        samesite="lax"
    )
    
    # Redirect based on user type
    if user.user_type == "HR":
        return RedirectResponse(url="/hr/dashboard", status_code=status.HTTP_303_SEE_OTHER)
    else:
        return RedirectResponse(url="/candidate/dashboard", status_code=status.HTTP_303_SEE_OTHER)

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@app.get("/dashboard")
async def dashboard_redirect(request: Request, response: Response, db: Session = Depends(get_db)):
    """
    Redirect to the appropriate dashboard based on user type.
    If not authenticated, redirect to login page.
    """
    # Try to get user from session or cookie
    user_email = request.session.get("user_email")
    if not user_email:
        user_email = request.cookies.get("auth_token")
    
    if not user_email:
        # Not authenticated, redirect to login
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    
    # Get user from database
    user = get_user_by_email(db, user_email)
    if not user:
        # Invalid user, redirect to login
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    
    # Redirect based on user type
    if user.user_type == "HR":
        return RedirectResponse(url="/hr/dashboard", status_code=status.HTTP_303_SEE_OTHER)
    else:  # Candidate or any other type
        return RedirectResponse(url="/candidate/dashboard", status_code=status.HTTP_303_SEE_OTHER)


@app.get("/logout")
async def logout(request: Request, response: Response):
    """
    Clear user session and cookie to log the user out.
    Redirect to login page.
    """
    # Clear session
    if "user_email" in request.session:
        del request.session["user_email"]
    
    # Clear auth cookie
    response = RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie(key="auth_token", path="/")
    
    return response

# HR Dashboard endpoints
@app.get("/hr/dashboard", response_class=HTMLResponse)
async def hr_dashboard(
    request: Request, 
    message: str = None,
    user: User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    if user.user_type != "HR":
        raise HTTPException(status_code=403, detail="Access denied")
    
    interviews = get_interviews_by_hr(db, user.id)
    return templates.TemplateResponse("hr_dashboard.html", {
        "request": request, 
        "user": user, 
        "interviews": interviews,
        "message": message
    })

@app.get("/hr/create-interview", response_class=HTMLResponse)
async def create_interview_page(request: Request, user: User = Depends(get_current_user)):
    if user.user_type != "HR":
        raise HTTPException(status_code=403, detail="Access denied")
    
    return templates.TemplateResponse("create_interview.html", {"request": request, "user": user})

@app.post("/hr/create-interview")
async def create_new_interview(
    candidate_name: str = Form(...),
    job_role: str = Form(...),
    difficulty: str = Form(...),
    interview_date: str = Form(...),
    interview_duration: int = Form(...),
    resume: UploadFile = File(...),
    job_description: str = Form(...),
    custom_questions: str = Form(None),
    candidate_email: str = Form(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if user.user_type != "HR":
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Save resume file
    resume_filename = f"{uuid.uuid4()}.pdf"
    resume_path = f"uploads/resumes/{resume_filename}"
    os.makedirs("uploads/resumes", exist_ok=True)
    
    with open(resume_path, "wb") as buffer:
        shutil.copyfileobj(resume.file, buffer)
    
    # Parse resume
    resume_data = parse_resume(resume_path)
    
    # Process custom questions
    questions = []
    if custom_questions:
        questions = json.loads(custom_questions)
    
    # Create interview record
    candidate = get_user_by_email(db, candidate_email)
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    
    # Convert difficulty value to expected format (e.g., "very_easy" -> "Very Easy")
    difficulty_mapping = {
        "very_easy": "Very Easy",
        "easy": "Easy", 
        "medium": "Medium",
        "hard": "Hard"
    }
    
    formatted_difficulty = difficulty_mapping.get(difficulty.lower(), "Medium")
    
    interview_data = InterviewCreate(
        hr_id=user.id,
        candidate_id=candidate.id,
        candidate_name=candidate_name,
        job_role=job_role,
        difficulty=formatted_difficulty,  # Use the formatted difficulty value
        scheduled_date=datetime.strptime(interview_date, "%Y-%m-%dT%H:%M"),
        duration=interview_duration,
        resume_path=resume_path,
        job_description=job_description,
        custom_questions=questions,
        status="scheduled"
    )
    
    interview = create_interview(db, interview_data)
    return RedirectResponse(
        url="/hr/dashboard?message=Interview created successfully",
        status_code=status.HTTP_303_SEE_OTHER
    )

@app.get("/hr/interview/{interview_id}/report")
async def get_interview_report(
    interview_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if user.user_type != "HR":
        raise HTTPException(status_code=403, detail="Access denied")
    
    interview = get_interview(db, interview_id)
    if not interview or interview.hr_id != user.id:
        raise HTTPException(status_code=404, detail="Interview not found")
    
    result = get_interview_result(db, interview_id)
    if not result:
        # Check if interview is completed but no result exists
        if interview.status == "completed":
            raise HTTPException(status_code=404, detail="Interview results are being processed. Please try again later.")
        else:
            raise HTTPException(status_code=404, detail="Interview has not been completed yet")
    
    # Return PDF report
    return FileResponse(
        result.report_path,
        media_type="application/pdf",
        filename=f"interview_report_{interview_id}.pdf"
    )

# Candidate Dashboard endpoints
@app.get("/candidate/dashboard", response_class=HTMLResponse)
async def candidate_dashboard(request: Request, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if user.user_type != "Candidate":
        raise HTTPException(status_code=403, detail="Access denied")
    
    interviews = get_interviews_by_candidate(db, user.id)
    return templates.TemplateResponse("candidate_dashboard.html", {
        "request": request, 
        "user": user, 
        "interviews": interviews,
        "now": datetime.now()  # Add this line
    })

@app.get("/candidate/interview/{interview_id}", response_class=HTMLResponse)
async def interview_page(
    interview_id: int,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if user.user_type != "Candidate":
        raise HTTPException(status_code=403, detail="Access denied")
    
    interview = get_interview(db, interview_id)
    if not interview or interview.candidate_id != user.id:
        raise HTTPException(status_code=404, detail="Interview not found")
    
    # Update interview status
    update_interview_status(db, interview_id, "in_progress")
    
    return templates.TemplateResponse("interview.html", {"request": request, "user": user, "interview": interview})

@app.get("/candidate/interview/{interview_id}/complete", response_class=HTMLResponse)
async def interview_complete(
    interview_id: int,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if user.user_type != "Candidate":
        raise HTTPException(status_code=403, detail="Access denied")
    
    interview = get_interview(db, interview_id)
    if not interview or interview.candidate_id != user.id:
        raise HTTPException(status_code=404, detail="Interview not found")
    
    # Update interview status
    update_interview_status(db, interview_id, "completed")
    
    return templates.TemplateResponse("interview_results_candidate.html", {"request": request, "user": user})

# Interview process endpoints
@app.post("/interview/{interview_id}/question")
async def get_next_question(
    interview_id: int,
    current_question_id: Optional[str] = Form(None),
    answer: Optional[str] = Form(None),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get the next question from the LLM agent.
    Returns a question object with id, question text, and other metadata.
    """
    interview = get_interview(db, interview_id)
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")
    
    # Convert question ID to the appropriate type
    question_id = None
    if current_question_id:
        try:
            # Try to convert to float first to handle potential decimal IDs
            question_id = float(current_question_id)
        except (ValueError, TypeError):
            # If conversion fails, use as is
            question_id = current_question_id
    
    # Get next question from LLM
    question_obj = llm_agent.get_next_question(interview, question_id, answer)
    
    # Log the question for debugging
    print(f"Generated question: {question_obj}")
    
    # Handle potential None response
    if question_obj is None:
        # Provide a fallback question
        return {
            "id": 1 if question_id is None else (int(float(question_id)) + 1 if isinstance(question_id, (float, int, str)) else 1),
            "question": "Could you tell me about your relevant experience for this position?",
            "is_follow_up": False,
            "follow_up_to": None
        }
    
    # Return the question object
    return question_obj

@app.post("/interview/{interview_id}/process-audio")
async def process_interview_audio(
    interview_id: int,
    audio_data: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    interview = get_interview(db, interview_id)
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")
    
    # Process audio and transcribe
    audio_path = f"uploads/audio/{interview_id}_{uuid.uuid4()}.wav"
    os.makedirs("uploads/audio", exist_ok=True)
    
    with open(audio_path, "wb") as buffer:
        shutil.copyfileobj(audio_data.file, buffer)
    
    # Transcribe audio using AWS Bedrock Nova Sonic
    transcription = process_audio(audio_path)
    
    return {"transcription": transcription}

@app.post("/interview/{interview_id}/save-recording")
async def save_interview_recording(
    interview_id: int,
    video_data: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    interview = get_interview(db, interview_id)
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")
    
    # Save video recording
    video_path = f"uploads/videos/{interview_id}.webm"
    os.makedirs("uploads/videos", exist_ok=True)
    
    with open(video_path, "wb") as buffer:
        shutil.copyfileobj(video_data.file, buffer)
    
    return {"message": "Recording saved successfully"}

@app.post("/interview/{interview_id}/complete")
async def complete_interview(
    interview_id: int,
    interview_data: str = Form(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    interview = get_interview(db, interview_id)
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")
    
    # Update interview status
    update_interview_status(db, interview_id, "completed")
    
    # Parse interview data
    data = json.loads(interview_data)
    
    # Evaluate the interview using LLM agent
    if len(data["questions"]) > 0:
        # Use LLM to evaluate the interview
        evaluation = llm_agent.evaluate_interview(interview, data["questions"])
        
        # Update the interview data with evaluation results
        data.update(evaluation)
    
    # Generate PDF report
    report_path = f"uploads/reports/{interview_id}.pdf"
    os.makedirs("uploads/reports", exist_ok=True)
    
    generate_pdf_report(
        interview=interview,
        interview_data=data,
        output_path=report_path
    )
    
    # Create interview result
    result_data = InterviewResultCreate(
        interview_id=interview_id,
        score=data.get("score", 0),
        decision=data.get("decision", "Not Fit"),
        report_path=report_path,
        notes=data.get("detailed_feedback", "")
    )
    
    result = create_interview_result(db, result_data)
    return {"message": "Interview completed successfully", "result_id": result.id}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)