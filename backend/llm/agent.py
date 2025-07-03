import boto3
import json
import os
import logging
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferMemory
from langchain.llms.bedrock import Bedrock
from typing import Dict, List, Optional, Any
import random
import re

from database.models import Interview, InterviewQuestion
from .prompts import SYSTEM_PROMPT, INTERVIEW_PROMPT, FOLLOW_UP_PROMPT, EVALUATION_PROMPT
from utils.resume_parser import extract_skills_from_resume

logger = logging.getLogger(__name__)

class LLMAgent:
    def __init__(self):
        # Initialize AWS Bedrock client
        self.bedrock_runtime = boto3.client(
            service_name="bedrock-runtime",
            region_name=os.getenv("AWS_REGION", "us-east-1"),
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        )
        
        # Initialize Mistral model through LangChain
        self.llm = Bedrock(
            client=self.bedrock_runtime,
            model_id="mistral.mistral-large-2402-v1:0",
            model_kwargs={
                "temperature": 0.7,
                "top_p": 0.9,
                "max_tokens": 1024
            }
        )
        
        # Initialize conversation memories for each interview
        self.interview_memories = {}
        
    def _get_interview_memory(self, interview_id: int) -> ConversationBufferMemory:
        """Get or create conversation memory for an interview"""
        if interview_id not in self.interview_memories:
            self.interview_memories[interview_id] = ConversationBufferMemory()
        return self.interview_memories[interview_id]
        
    def prepare_interview(self, interview: Interview) -> List[str]:
        """Generate initial list of questions based on resume and job description"""
        # Extract skills from resume
        skills = extract_skills_from_resume(interview.resume_path)
        
        # Prepare prompt for generating questions
        prompt = INTERVIEW_PROMPT.format(
            job_role=interview.job_role,
            job_description=interview.job_description,
            candidate_skills=", ".join(skills),
            difficulty=interview.difficulty
        )
        
        # Generate questions using LLM
        response = self.llm.invoke(prompt)
        
        try:
            # Parse questions from response
            questions = []
            for line in response.strip().split("\n"):
                if line and ("Q:" in line or line.startswith("1.") or line.startswith("- ")):
                    # Clean up the question text
                    question = line.replace("Q:", "").replace("1.", "").replace("- ", "").strip()
                    if question:
                        questions.append(question)
            
            # Add custom questions from HR if provided
            if interview.custom_questions:
                questions.extend(interview.custom_questions)
                
            return questions
            
        except Exception as e:
            logger.error(f"Error parsing questions: {e}")
            # Return a default set of questions if parsing fails
            return [
                "Tell me about your experience related to this position.",
                "What skills do you have that make you a good fit for this role?",
                "Describe a challenging situation you faced in a previous job and how you resolved it."
            ]
    
    def get_next_question(
    self, 
    interview: Interview, 
    current_question_id: Optional[int] = None, 
    answer: Optional[str] = None
) -> Dict[str, Any]:
        """Get the next question for the interview with variety and no duplicates"""
        memory = self._get_interview_memory(interview.id)
        
        # If an answer was provided, add it to memory
        if current_question_id is not None and answer:
            current_question = f"Question {current_question_id}"
            memory.save_context({"input": current_question}, {"output": answer})
            
            # Decide whether to ask a follow-up question
            if self._should_ask_followup(current_question, answer, interview):
                follow_up_question = self._generate_followup_question(current_question, answer, interview)
                return {
                    "id": float(current_question_id) + 0.1,
                    "question": follow_up_question,
                    "is_follow_up": True,
                    "follow_up_to": current_question_id
                }
        
        # Initialize question tracking if needed
        if not hasattr(self, 'interview_questions'):
            self.interview_questions = {}
        if interview.id not in self.interview_questions:
            self.interview_questions[interview.id] = self._prepare_structured_questions(interview)
        
        if not hasattr(self, 'asked_questions'):
            self.asked_questions = {}
        if interview.id not in self.asked_questions:
            self.asked_questions[interview.id] = set()
        
        # Get next question ID
        next_id = 1 if current_question_id is None else (int(float(current_question_id)) + 1)
        
        # Get available question categories that haven't been exhausted
        available_categories = [
            cat for cat in self.interview_questions[interview.id]
            if len(self.interview_questions[interview.id][cat]['questions']) > 0
        ]
        
        # If we have available categories, select one strategically
        if available_categories:
            # Prioritize categories we haven't asked from yet
            unused_categories = [
                cat for cat in available_categories
                if cat not in self.asked_questions[interview.id]
            ]
            
            selected_category = unused_categories[0] if unused_categories else random.choice(available_categories)
            
            # Get question from selected category
            question = self.interview_questions[interview.id][selected_category]['questions'].pop(0)
            self.asked_questions[interview.id].add(selected_category)
            
            return {
                "id": next_id,
                "question": question,
                "is_follow_up": False,
                "follow_up_to": None,
                "category": selected_category
            }
        else:
            # Generate a new question if we've exhausted our prepared questions
            if next_id <= 50:  # Absolute maximum
                new_question = self._generate_new_question_based_on_context(interview, memory)
                return {
                    "id": next_id,
                    "question": new_question,
                    "is_follow_up": False,
                    "follow_up_to": None,
                    "category": "Generated"
                }
            else:
                return {
                    "interview_complete": True,
                    "id": next_id,
                    "question": "Thank you for your time. This concludes our interview.",
                    "is_follow_up": False,
                    "follow_up_to": None
                }
    def _prepare_structured_questions(self, interview: Interview) -> Dict[str, Dict]:
        """Prepare a structured set of questions by category"""
        skills = extract_skills_from_resume(interview.resume_path)
        
        # Define question categories and templates
        categories = {
            "Technical Skills": {
                "weight": 0.4,
                "templates": [
                    "Can you explain your experience with {skill}?",
                    "How would you approach a problem using {skill}?",
                    "What challenges have you faced with {skill} and how did you overcome them?"
                ]
            },
            "Behavioral": {
                "weight": 0.3,
                "templates": [
                    "Tell me about a time you faced a difficult challenge at work and how you handled it.",
                    "Describe a situation where you had to work with a difficult team member.",
                    "Give an example of how you've handled a tight deadline."
                ]
            },
            "Scenario-Based": {
                "weight": 0.2,
                "templates": [
                    "If you encountered [job-specific scenario], how would you handle it?",
                    "How would you approach [job-specific problem]?",
                    "What would you do if [job-specific situation] occurred?"
                ]
            },
            "Company/Position": {
                "weight": 0.1,
                "templates": [
                    "What interests you about this position at our company?",
                    "How do you see yourself contributing to our team?",
                    "What do you know about our company's work in [relevant field]?"
                ]
            }
        }
        
        questions = {}
        for category, config in categories.items():
            questions[category] = {"questions": []}
            
            # Generate questions for this category
            if category == "Technical Skills":
                for skill in skills:
                    for template in config["templates"]:
                        questions[category]["questions"].append(
                            template.format(skill=skill)
                        )
            elif category == "Scenario-Based":
                for template in config["templates"]:
                    questions[category]["questions"].append(
                        template.replace("[job-specific scenario]", f"a {interview.job_role} scenario")
                        .replace("[job-specific problem]", f"a {interview.job_role} problem")
                        .replace("[job-specific situation]", f"a {interview.job_role} situation")
                    )
            else:
                questions[category]["questions"].extend(config["templates"])
        
        # Shuffle questions within each category
        for category in questions:
            random.shuffle(questions[category]["questions"])
        
        return questions

    def _should_ask_followup(self, question: str, answer: str, interview: Interview) -> bool:
        """Determine if a follow-up question is warranted"""
        prompt = f"""
        Analyze this interview exchange and determine if a follow-up question is needed.
        
        Job Role: {interview.job_role}
        Job Description: {interview.job_description}
        
        Question: {question}
        Answer: {answer}
        
        Should we ask a follow-up question? (YES/NO)
        If YES, briefly explain why.
        """
        
        response = self.llm.invoke(prompt)
        return "YES" in response.upper()

    def _generate_followup_question(self, question: str, answer: str, interview: Interview) -> str:
        """Generate a relevant follow-up question"""
        prompt = f"""
        Based on this interview exchange, generate one relevant follow-up question.
        
        Job Role: {interview.job_role}
        Job Description: {interview.job_description}
        
        Original Question: {question}
        Candidate's Answer: {answer}
        
        Generate a follow-up question that:
        1. Digs deeper into the candidate's response
        2. Explores related aspects not covered
        3. Is relevant to the job requirements
        
        Follow-up Question:
        """
        return self.llm.invoke(prompt).strip()

    def _generate_new_question_based_on_context(self, interview: Interview, memory: ConversationBufferMemory) -> str:
        """Generate a new question based on conversation context"""
        prompt = f"""
        Generate one new interview question based on:
        - Job requirements for {interview.job_role}
        - The conversation so far
        - Ensuring it's different from previous questions
        
        Job Description: {interview.job_description}
        Conversation History: {memory.load_memory_variables({})}
        
        The question should:
        1. Cover a new aspect not discussed yet
        2. Be relevant to the position
        3. Be open-ended to encourage detailed response
        
        New Question:
        """
        return self.llm.invoke(prompt).strip()
    def evaluate_interview(self, interview: Interview, questions_and_answers: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Evaluate the interview based on the questions and answers"""
        # Prepare the evaluation prompt
        prompt = f"""
        Evaluate this job interview for the position of {interview.job_role}.
        
        Job Description: {interview.job_description}
        
        Interview Transcript:
        {json.dumps([{"Q": qa["question"], "A": qa["answer"]} for qa in questions_and_answers], indent=2)}
        
        Please provide:
        1. A score from 0-100 where 100 is perfect
        2. A decision: "Fit" or "Not Fit"
        3. Detailed feedback with specific strengths and areas for improvement
        4. List of 3-5 specific strengths
        5. List of 3-5 specific areas for improvement
        
        Format your response like this:
        SCORE: [0-100]
        DECISION: [Fit/Not Fit]
        
        DETAILED FEEDBACK:
        [Your comprehensive evaluation]
        
        STRENGTHS:
        - [Strength 1]
        - [Strength 2]
        - [Strength 3]
        
        AREAS FOR IMPROVEMENT:
        - [Area 1]
        - [Area 2]
        - [Area 3]
        """
        
        # Generate evaluation using LLM
        response = self.llm.invoke(prompt)
        
        try:
            # Parse evaluation results
            result = {}
            
            # Extract score
            score_match = re.search(r"SCORE:\s*(\d+)", response)
            result["score"] = int(score_match.group(1)) if score_match else 50
            
            # Extract decision
            decision_match = re.search(r"DECISION:\s*(\w+\s*\w*)", response)
            decision_text = decision_match.group(1) if decision_match else "Not Fit"
            result["decision"] = "Fit" if any(fit_word in decision_text.lower() for fit_word in ["fit", "qualified", "yes", "hire"]) else "Not Fit"
            
            # Extract detailed feedback
            feedback_match = re.search(r"DETAILED FEEDBACK:(.*?)(?:STRENGTHS:|$)", response, re.DOTALL)
            result["detailed_feedback"] = feedback_match.group(1).strip() if feedback_match else ""
            
            # Extract strengths
            strengths = []
            strengths_match = re.search(r"STRENGTHS:(.*?)(?:AREAS FOR IMPROVEMENT:|$)", response, re.DOTALL)
            if strengths_match:
                strengths_text = strengths_match.group(1)
                for line in strengths_text.split("\n"):
                    line = line.strip()
                    if line.startswith(("- ", "• ", "* ")) and len(line) > 2:
                        strengths.append(line.replace("- ", "").replace("• ", "").replace("* ", ""))
            result["strengths"] = strengths
            
            # Extract areas for improvement
            weaknesses = []
            weaknesses_match = re.search(r"AREAS FOR IMPROVEMENT:(.*?)(?:$)", response, re.DOTALL)
            if weaknesses_match:
                weaknesses_text = weaknesses_match.group(1)
                for line in weaknesses_text.split("\n"):
                    line = line.strip()
                    if line.startswith(("- ", "• ", "* ")) and len(line) > 2:
                        weaknesses.append(line.replace("- ", "").replace("• ", "").replace("* ", ""))
            result["weaknesses"] = weaknesses
            
            return result
            
        except Exception as e:
            logger.error(f"Error evaluating interview: {e}")
            return {
                "score": 50,
                "decision": "Not Fit",
                "detailed_feedback": "Unable to generate detailed feedback due to an error.",
                "strengths": ["Participated in the interview process"],
                "weaknesses": ["Unable to properly evaluate responses due to a system error"]
            }

    def clear_interview_memory(self, interview_id: int) -> None:
        """Clear the conversation memory for an interview"""
        if interview_id in self.interview_memories:
            del self.interview_memories[interview_id]