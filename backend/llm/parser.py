#llm/parser.py
import re
import json
from typing import Dict, List, Any, Optional

def parse_llm_interview_questions(llm_response: str) -> List[str]:
    """
    Parse interview questions from LLM response
    
    Args:
        llm_response: Raw text response from LLM
        
    Returns:
        List of extracted questions
    """
    questions = []
    
    # Try to extract questions with different patterns
    patterns = [
        r"(?:^|\n)(?:\d+\.\s*)(.+?)(?=\n\d+\.|\n\n|\Z)",  # Numbered list (1. Question)
        r"(?:^|\n)(?:Q\d*:?\s*)(.+?)(?=\n\s*Q\d*:?|\n\n|\Z)",  # Q: or Q1: format
        r"(?:^|\n)(?:•\s*|\*\s*|-\s*)(.+?)(?=\n\s*•|\n\s*\*|\n\s*-|\n\n|\Z)"  # Bullet points
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, llm_response, re.MULTILINE)
        if matches:
            questions.extend([q.strip() for q in matches if q.strip()])
    
    # If no patterns match, try splitting by newlines and filtering
    if not questions:
        lines = llm_response.strip().split('\n')
        questions = [line.strip() for line in lines if line.strip() and line.strip()[-1] == '?']
    
    return questions

def parse_llm_evaluation(llm_response: str) -> Dict[str, Any]:
    """
    Parse evaluation results from LLM response
    
    Args:
        llm_response: Raw text response from LLM
        
    Returns:
        Dictionary with parsed evaluation data
    """
    result = {
        "score": 0,
        "decision": "Not Fit",
        "feedback": "",
        "strengths": [],
        "weaknesses": []
    }
    
    # Extract score
    score_match = re.search(r"SCORE:?\s*(\d+(?:\.\d+)?)", llm_response, re.IGNORECASE)
    if score_match:
        result["score"] = float(score_match.group(1))
    
    # Extract decision
    decision_match = re.search(r"DECISION:?\s*(\w+(?:\s+\w+)*)", llm_response, re.IGNORECASE)
    if decision_match:
        decision = decision_match.group(1).strip().lower()
        result["decision"] = "Fit" if any(word in decision for word in ["fit", "qualified", "yes", "pass"]) else "Not Fit"
    
    # Extract detailed feedback
    feedback_match = re.search(r"DETAILED FEEDBACK:?([\s\S]+)(?=STRENGTHS:|$)", llm_response, re.IGNORECASE)
    if feedback_match:
        result["feedback"] = feedback_match.group(1).strip()
    
    # Extract strengths and weaknesses if available
    strengths_match = re.search(r"STRENGTHS:?([\s\S]+)(?=WEAKNESSES:|AREAS FOR IMPROVEMENT:|$)", llm_response, re.IGNORECASE)
    if strengths_match:
        strengths_text = strengths_match.group(1).strip()
        result["strengths"] = [item.strip() for item in re.split(r"(?:^|\n)\s*-\s*", strengths_text) if item.strip()]
    
    weaknesses_match = re.search(r"(?:WEAKNESSES|AREAS FOR IMPROVEMENT):?([\s\S]+)$", llm_response, re.IGNORECASE)
    if weaknesses_match:
        weaknesses_text = weaknesses_match.group(1).strip()
        result["weaknesses"] = [item.strip() for item in re.split(r"(?:^|\n)\s*-\s*", weaknesses_text) if item.strip()]
    
    return result

def parse_json_response(llm_response: str) -> Optional[Dict[str, Any]]:
    """
    Extract and parse JSON from LLM response
    
    Args:
        llm_response: Raw text response from LLM
        
    Returns:
        Parsed JSON object or None if parsing fails
    """
    try:
        # Try to find JSON object in the response
        json_match = re.search(r"```json\s*([\s\S]+?)\s*```", llm_response)
        if json_match:
            json_str = json_match.group(1)
        else:
            # Try to find JSON between curly braces
            json_match = re.search(r"(\{[\s\S]+\})", llm_response)
            if json_match:
                json_str = json_match.group(1)
            else:
                # Use the entire response
                json_str = llm_response
        
        # Parse JSON
        return json.loads(json_str)
    except (json.JSONDecodeError, AttributeError):
        return None