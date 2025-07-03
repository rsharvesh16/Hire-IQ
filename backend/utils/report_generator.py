from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.units import inch
import json
import os
from datetime import datetime
from typing import Dict, List, Any

from database.models import Interview, InterviewQuestion

def generate_pdf_report(interview: Interview, interview_data: Dict[str, Any], output_path: str) -> str:
    """
    Generate a PDF report for the interview
    
    Args:
        interview: Interview object
        interview_data: Dictionary containing interview data (questions, answers, score, etc.)
        output_path: Path to save the PDF file
        
    Returns:
        Path to the generated PDF file
    """
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Create PDF document
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=72
    )
    
    # Get styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        name='Title',
        parent=styles['Title'],
        fontSize=16,
        alignment=1  # Center alignment
    )
    heading_style = ParagraphStyle(
        name='Heading',
        parent=styles['Heading1'],
        fontSize=14
    )
    subheading_style = ParagraphStyle(
        name='Subheading',
        parent=styles['Heading2'],
        fontSize=12
    )
    normal_style = styles['Normal']
    
    # Build document content
    content = []
    
    # Add title
    content.append(Paragraph(f"Interview Report - {interview.job_role}", title_style))
    content.append(Spacer(1, 0.25*inch))
    
    # Add interview details
    content.append(Paragraph("Interview Details", heading_style))
    content.append(Spacer(1, 0.1*inch))
    
    details_data = [
        ["Candidate Name", interview.candidate_name],
        ["Job Role", interview.job_role],
        ["Interview Date", interview.scheduled_date.strftime('%Y-%m-%d %H:%M')],
        ["Duration", f"{interview.duration} minutes"],
        ["Difficulty", interview.difficulty],
    ]
    
    details_table = Table(details_data, colWidths=[2*inch, 4*inch])
    details_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('PADDING', (0, 0), (-1, -1), 6),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    
    content.append(details_table)
    content.append(Spacer(1, 0.25*inch))
    
    # Add interview score and decision
    content.append(Paragraph("Interview Results", heading_style))
    content.append(Spacer(1, 0.1*inch))
    
    score = interview_data.get("score", 0)
    decision = interview_data.get("decision", "Not Fit")
    
    results_data = [
        ["Score", f"{score}/100"],
        ["Decision", decision]
    ]
    
    results_table = Table(results_data, colWidths=[2*inch, 4*inch])
    results_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('PADDING', (0, 0), (-1, -1), 6),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BACKGROUND', (1, 1), (1, 1), colors.green if decision == "Fit" else colors.red),
        ('TEXTCOLOR', (1, 1), (1, 1), colors.white),
    ]))
    
    content.append(results_table)
    content.append(Spacer(1, 0.25*inch))
    
    # Add questions and answers
    content.append(Paragraph("Questions and Answers", heading_style))
    content.append(Spacer(1, 0.1*inch))
    
    questions = interview_data.get("questions", [])
    
    for i, qa in enumerate(questions):
        q_num = i + 1
        question = qa.get("question", "")
        answer = qa.get("answer", "")
        follow_up = qa.get("is_follow_up", False)
        
        if follow_up:
            q_prefix = "Follow-up"
        else:
            q_prefix = f"Q{q_num}"
        
        content.append(Paragraph(f"{q_prefix}: {question}", subheading_style))
        content.append(Spacer(1, 0.05*inch))
        content.append(Paragraph(f"A: {answer}", normal_style))
        content.append(Spacer(1, 0.1*inch))
    
    # Add detailed feedback
    if "detailed_feedback" in interview_data:
        content.append(Paragraph("Detailed Feedback", heading_style))
        content.append(Spacer(1, 0.1*inch))
        
        feedback = interview_data.get("detailed_feedback", "")
        content.append(Paragraph(feedback, normal_style))
        content.append(Spacer(1, 0.25*inch))
    
    # Add strengths and weaknesses if available
    if "strengths" in interview_data or "weaknesses" in interview_data:
        content.append(Paragraph("Strengths and Areas for Improvement", heading_style))
        content.append(Spacer(1, 0.1*inch))
        
        strengths = interview_data.get("strengths", [])
        weaknesses = interview_data.get("weaknesses", [])
        
        if strengths:
            content.append(Paragraph("Strengths:", subheading_style))
            for strength in strengths:
                content.append(Paragraph(f"• {strength}", normal_style))
            content.append(Spacer(1, 0.1*inch))
        
        if weaknesses:
            content.append(Paragraph("Areas for Improvement:", subheading_style))
            for weakness in weaknesses:
                content.append(Paragraph(f"• {weakness}", normal_style))
            content.append(Spacer(1, 0.1*inch))
    
    if "strengths" not in interview_data or "weaknesses" not in interview_data:
        detailed_feedback = interview_data.get("detailed_feedback", "")
        
        # Simple extraction logic - can be enhanced with more sophisticated parsing
        strengths = []
        weaknesses = []
        
        lines = detailed_feedback.split("\n")
        current_section = None
        
        for line in lines:
            line = line.strip()
            if "strength" in line.lower() or "positive" in line.lower():
                current_section = "strengths"
                continue
            elif "weakness" in line.lower() or "improvement" in line.lower() or "limitation" in line.lower():
                current_section = "weaknesses"
                continue
            
            if current_section and line and line.startswith(("- ", "• ", "* ")):
                item = line.replace("- ", "").replace("• ", "").replace("* ", "")
                if current_section == "strengths":
                    strengths.append(item)
                else:
                    weaknesses.append(item)
        
        interview_data["strengths"] = strengths
        interview_data["weaknesses"] = weaknesses
    
    # Add timestamp and footer
    content.append(Spacer(1, 0.5*inch))
    content.append(Paragraph(f"Report generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", normal_style))
    content.append(Paragraph("Generated by HireIQ", normal_style))
    
    # Build PDF
    doc.build(content)
    
    return output_path