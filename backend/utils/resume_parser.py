# backend/utils/resume_parser.py
import pdfplumber
import re
import spacy
import json
import os
import logging
from typing import Dict, List, Any, Set
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

# Load spaCy model for NER
try:
    nlp = spacy.load("en_core_web_sm")
except:
    # Download the model if not available
    import subprocess
    subprocess.call(["python", "-m", "spacy", "download", "en_core_web_sm"])
    nlp = spacy.load("en_core_web_sm")

# Common skills dictionary
COMMON_SKILLS = {
    # Programming Languages
    "python", "java", "javascript", "typescript", "c++", "c#", "ruby", "php", "go", 
    "rust", "swift", "kotlin", "scala", "perl", "r", "matlab", "sql",
    
    # Web Development
    "html", "css", "react", "angular", "vue", "node.js", "express", "django", 
    "flask", "spring", "asp.net", "ruby on rails", "bootstrap", "jquery",
    
    # Data Science & Machine Learning
    "machine learning", "deep learning", "tensorflow", "pytorch", "keras", 
    "scikit-learn", "pandas", "numpy", "data analysis", "statistics", "ai",
    "nlp", "natural language processing", "computer vision", "data mining",
    
    # DevOps & Cloud
    "aws", "azure", "gcp", "docker", "kubernetes", "jenkins", "git", "ci/cd",
    "terraform", "ansible", "devops", "cloud computing", "linux", "unix",
    
    # Databases
    "mysql", "postgresql", "mongodb", "sqlite", "oracle", "sql server", "nosql",
    "redis", "elasticsearch", "cassandra", "dynamodb",
    
    # Soft Skills
    "leadership", "teamwork", "communication", "problem solving", "time management",
    "project management", "agile", "scrum", "critical thinking", "creativity",
    
    # Mobile Development
    "android", "ios", "flutter", "react native", "xamarin", "swift ui", "jetpack compose",
    
    # Other Technical Skills
    "restful api", "graphql", "microservices", "serverless", "blockchain", "cybersecurity",
    "networking", "testing", "qa", "ui/ux", "frontend", "backend", "fullstack"
}

def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract text from PDF file"""
    try:
        text = ""
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                text += page.extract_text() + "\n"
        return text
    except Exception as e:
        logger.error(f"Error extracting text from PDF: {e}")
        return ""

def extract_contact_info(text: str) -> Dict[str, str]:
    """Extract contact information from text"""
    contact_info = {
        "email": None,
        "phone": None,
        "linkedin": None
    }
    
    # Email pattern
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    email_matches = re.findall(email_pattern, text)
    if email_matches:
        contact_info["email"] = email_matches[0]
    
    # Phone pattern (various formats)
    phone_pattern = r'(?:\+\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
    phone_matches = re.findall(phone_pattern, text)
    if phone_matches:
        contact_info["phone"] = phone_matches[0]
    
    # LinkedIn pattern
    linkedin_pattern = r'linkedin\.com/in/[A-Za-z0-9_-]+'
    linkedin_matches = re.findall(linkedin_pattern, text)
    if linkedin_matches:
        contact_info["linkedin"] = linkedin_matches[0]
    
    return contact_info

def extract_education(text: str) -> List[Dict[str, str]]:
    """Extract education details from text"""
    education = []
    
    # Common degree patterns
    degree_patterns = [
        r'(?:B\.?S\.?|Bachelor of Science|Bachelor\'s|Bachelor|BSc)',
        r'(?:B\.?A\.?|Bachelor of Arts|BA)',
        r'(?:M\.?S\.?|Master of Science|Master\'s|Master|MSc)',
        r'(?:M\.?B\.?A\.?|Master of Business Administration)',
        r'(?:Ph\.?D\.?|Doctor of Philosophy|Doctorate)',
        r'(?:Associate\'s|Associate|A\.?S\.?|A\.?A\.?)'
    ]
    
    # Common university indicators
    uni_indicators = ['university', 'college', 'institute', 'school']
    
    # Extract education sections
    education_pattern = r'(?:EDUCATION|Education|ACADEMIC|Academic)(?:.*?)(?:EXPERIENCE|Experience|SKILLS|Skills|PROJECTS|Projects)'
    education_sections = re.findall(education_pattern, text, re.DOTALL)
    
    if not education_sections:
        # Try extracting paragraphs containing education keywords
        lines = text.split('\n')
        for i, line in enumerate(lines):
            for degree in degree_patterns:
                if re.search(degree, line, re.IGNORECASE):
                    # Look around this line for university name
                    start = max(0, i-3)
                    end = min(len(lines), i+4)
                    context = ' '.join(lines[start:end])
                    
                    degree_match = re.search(degree, line, re.IGNORECASE)
                    degree_text = degree_match.group(0) if degree_match else ""
                    
                    # Try to find university name
                    uni_name = ""
                    for indicator in uni_indicators:
                        uni_pattern = rf'(?:[A-Z][a-z]+ )+{indicator}|(?:[A-Z][a-z]+ )+(?:[A-Z][a-z]+ )*{indicator}'
                        uni_match = re.search(uni_pattern, context, re.IGNORECASE)
                        if uni_match:
                            uni_name = uni_match.group(0)
                            break
                    
                    # Try to find graduation year
                    year_pattern = r'(?:19|20)\d{2}'
                    year_match = re.search(year_pattern, context)
                    year = year_match.group(0) if year_match else ""
                    
                    if uni_name:
                        education.append({
                            "degree": degree_text,
                            "university": uni_name,
                            "year": year
                        })
    else:
        # Process identified education sections
        for section in education_sections:
            lines = section.split('\n')
            current_education = {}
            
            for line in lines:
                # Check for degree
                for degree in degree_patterns:
                    if re.search(degree, line, re.IGNORECASE):
                        if current_education:
                            education.append(current_education)
                            current_education = {}
                        
                        degree_match = re.search(degree, line, re.IGNORECASE)
                        current_education["degree"] = degree_match.group(0)
                        
                        # Check for university in the same line
                        for indicator in uni_indicators:
                            uni_pattern = rf'(?:[A-Z][a-z]+ )+{indicator}|(?:[A-Z][a-z]+ )+(?:[A-Z][a-z]+ )*{indicator}'
                            uni_match = re.search(uni_pattern, line, re.IGNORECASE)
                            if uni_match:
                                current_education["university"] = uni_match.group(0)
                                break
                        
                        # Check for year
                        year_pattern = r'(?:19|20)\d{2}'
                        year_match = re.search(year_pattern, line)
                        if year_match:
                            current_education["year"] = year_match.group(0)
                        break
            
            if current_education:
                education.append(current_education)
    
    return education

def extract_experience(text: str) -> List[Dict[str, Any]]:
    """Extract work experience details from text"""
    experiences = []
    
    # Try to find experience section
    experience_pattern = r'(?:EXPERIENCE|Experience|WORK|Work|EMPLOYMENT|Employment)(?:.*?)(?:EDUCATION|Education|SKILLS|Skills|PROJECTS|Projects|$)'
    experience_sections = re.findall(experience_pattern, text, re.DOTALL)
    
    if experience_sections:
        exp_text = experience_sections[0]
        
        # Split into potential job entries (look for company or title at beginning of line)
        job_entries = re.split(r'\n(?=[A-Z][a-z]+(?: [A-Z][a-z]+)*(?:,| at | -| \|| \|))', exp_text)
        
        for entry in job_entries:
            if len(entry.strip()) < 20:  # Skip very short entries
                continue
                
            experience = {
                "company": None,
                "title": None,
                "duration": None,
                "description": []
            }
            
            lines = entry.split('\n')
            first_line = lines[0] if lines else ""
            
            # Try to extract company and title from first line
            company_title_match = re.search(r'(.*?)(?:,| at | -| \|| \|) *(.*)', first_line)
            if company_title_match:
                part1, part2 = company_title_match.groups()
                # Determine which is company and which is title
                if any(word.lower() in part1.lower() for word in ["engineer", "developer", "analyst", "manager", "director", "specialist"]):
                    experience["title"] = part1
                    experience["company"] = part2
                else:
                    experience["company"] = part1
                    experience["title"] = part2
            
            # Try to extract dates/duration
            date_pattern = r'(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|January|February|March|April|May|June|July|August|September|October|November|December)[\s\.\,]*\d{4}[\s\-\–\—]*(?:(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|January|February|March|April|May|June|July|August|September|October|November|December)[\s\.\,]*\d{4}|Present|Current|Now)'
            date_match = re.search(date_pattern, entry, re.IGNORECASE)
            if date_match:
                experience["duration"] = date_match.group(0)
            
            # Extract description (bullet points or paragraphs)
            desc_lines = []
            for line in lines[1:]:
                line = line.strip()
                if line and not re.match(date_pattern, line, re.IGNORECASE) and len(line) > 5:
                    # Remove bullet points
                    clean_line = re.sub(r'^[\•\-\*\■\▪\●\⦿\⦾\⦿\►\➢\➤\➥\➧\➨\➲\➻\➼][\s]*', '', line)
                    if clean_line:
                        desc_lines.append(clean_line)
            
            experience["description"] = desc_lines
            
            if experience["company"] or experience["title"]:
                experiences.append(experience)
    
    return experiences

def extract_skills(text: str) -> List[str]:
    """Extract skills from text"""
    skills = set()
    
    # Try to find skills section
    skills_pattern = r'(?:SKILLS|Skills|TECHNICAL SKILLS|Technical Skills|TECHNOLOGIES|Technologies)(?:.*?)(?:EXPERIENCE|Experience|EDUCATION|Education|PROJECTS|Projects|$)'
    skills_sections = re.findall(skills_pattern, text, re.DOTALL)
    
    if skills_sections:
        skills_text = skills_sections[0]
        
        # Check for each skill in the common skills list
        for skill in COMMON_SKILLS:
            if re.search(r'\b' + re.escape(skill) + r'\b', skills_text, re.IGNORECASE):
                skills.add(skill.lower())
    
    # Also look for skills throughout the entire text
    for skill in COMMON_SKILLS:
        if re.search(r'\b' + re.escape(skill) + r'\b', text, re.IGNORECASE):
            skills.add(skill.lower())
    
    return list(skills)

def extract_skills_from_resume(text: str) -> List[str]:
    """Extract skills from text - alias for extract_skills for backward compatibility"""
    return extract_skills(text)

def extract_projects(text: str) -> List[Dict[str, Any]]:
    """Extract project details from text"""
    projects = []
    
    # Try to find projects section
    projects_pattern = r'(?:PROJECTS|Projects|PERSONAL PROJECTS|Personal Projects)(?:.*?)(?:EXPERIENCE|Experience|EDUCATION|Education|SKILLS|Skills|$)'
    project_sections = re.findall(projects_pattern, text, re.DOTALL)
    
    if project_sections:
        proj_text = project_sections[0]
        
        # Split into potential project entries (look for title at beginning of line)
        project_entries = re.split(r'\n(?=[A-Z][a-z]+(?: [A-Z][a-z]+)*)', proj_text)
        
        for entry in project_entries:
            if len(entry.strip()) < 20:  # Skip very short entries
                continue
                
            project = {
                "name": None,
                "technologies": [],
                "description": []
            }
            
            lines = entry.split('\n')
            if lines:
                # First line is likely the project name
                project["name"] = lines[0].strip()
                
                # Extract technologies (usually in parentheses or after a dash)
                tech_match = re.search(r'[\(\[\-\|] *(.*?)(?: *[\)\]\|]|$)', lines[0])
                if tech_match:
                    techs = tech_match.group(1).split(',')
                    project["technologies"] = [t.strip().lower() for t in techs if t.strip()]
                
                # Extract description
                desc_lines = []
                for line in lines[1:]:
                    line = line.strip()
                    if line and len(line) > 5:
                        # Remove bullet points
                        clean_line = re.sub(r'^[\•\-\*\■\▪\●\⦿\➢\➤\➥\➧\➨\➲\➻\➼][\s]*', '', line)
                        if clean_line:
                            desc_lines.append(clean_line)
                
                project["description"] = desc_lines
                
                # Check for technologies in description
                if not project["technologies"]:
                    for skill in COMMON_SKILLS:
                        for desc in desc_lines:
                            if re.search(r'\b' + re.escape(skill) + r'\b', desc, re.IGNORECASE):
                                project["technologies"].append(skill.lower())
            
            if project["name"]:
                projects.append(project)
    
    return projects

def extract_summary(text: str) -> str:
    """Extract professional summary from text"""
    # Try to find summary section
    summary_pattern = r'(?:SUMMARY|Summary|PROFESSIONAL SUMMARY|Professional Summary|OBJECTIVE|Objective|PROFILE|Profile)(?:.*?)(?:EXPERIENCE|Experience|EDUCATION|Education|SKILLS|Skills|PROJECTS|Projects)'
    summary_sections = re.findall(summary_pattern, text, re.DOTALL)
    
    if summary_sections:
        summary = summary_sections[0].strip()
        # Remove the heading
        summary = re.sub(r'^(?:SUMMARY|Summary|PROFESSIONAL SUMMARY|Professional Summary|OBJECTIVE|Objective|PROFILE|Profile)[:\s]*', '', summary)
        return summary.strip()
    
    # If no summary section found, try to extract first paragraph
    paragraphs = text.split('\n\n')
    for para in paragraphs:
        if len(para.strip()) > 50 and not re.match(r'(?:EXPERIENCE|Experience|EDUCATION|Education|SKILLS|Skills|PROJECTS|Projects)', para.strip()):
            return para.strip()
    
    return ""

def extract_keywords(text: str, job_description: str = None) -> List[str]:
    """Extract important keywords from text, optionally matching with a job description"""
    keywords = set()
    
    # Process text with spaCy
    doc = nlp(text)
    
    # Extract named entities
    for ent in doc.ents:
        if ent.label_ in ["ORG", "PRODUCT", "WORK_OF_ART", "GPE", "LOC"]:
            keywords.add(ent.text.lower())
    
    # Extract noun phrases
    for chunk in doc.noun_chunks:
        if len(chunk.text.split()) <= 3:  # Limit to phrases of 3 words or less
            keywords.add(chunk.text.lower())
    
    # If job description is provided, find matching keywords
    if job_description:
        job_doc = nlp(job_description)
        job_keywords = set()
        
        # Extract named entities and noun phrases from job description
        for ent in job_doc.ents:
            if ent.label_ in ["ORG", "PRODUCT", "WORK_OF_ART", "GPE", "LOC"]:
                job_keywords.add(ent.text.lower())
        
        for chunk in job_doc.noun_chunks:
            if len(chunk.text.split()) <= 3:
                job_keywords.add(chunk.text.lower())
        
        # Find intersection
        matching_keywords = keywords.intersection(job_keywords)
        return list(matching_keywords)
    
    return list(keywords)

def parse_resume(pdf_path: str, job_description: str = None) -> Dict[str, Any]:
    """
    Parse a resume PDF and extract structured information
    
    Args:
        pdf_path: Path to the PDF resume
        job_description: Optional job description text to match against
        
    Returns:
        Dictionary containing structured resume data
    """
    try:
        # Extract text from PDF
        text = extract_text_from_pdf(pdf_path)
        if not text:
            logger.error(f"Could not extract text from PDF: {pdf_path}")
            return {}
        
        # Build structured resume data
        resume_data = {
            "contact_info": extract_contact_info(text),
            "summary": extract_summary(text),
            "education": extract_education(text),
            "experience": extract_experience(text),
            "skills": extract_skills(text),  # Use the new function name
            "projects": extract_projects(text)
        }
        
        # Add matching keywords if job description provided
        if job_description:
            resume_data["matching_keywords"] = extract_keywords(text, job_description)
        
        # Cache the parsed data
        cache_dir = "uploads/parsed_resumes"
        os.makedirs(cache_dir, exist_ok=True)
        
        filename = os.path.basename(pdf_path)
        cache_path = os.path.join(cache_dir, f"{os.path.splitext(filename)[0]}.json")
        
        with open(cache_path, 'w') as f:
            json.dump(resume_data, f, indent=2)
        
        return resume_data
        
    except Exception as e:
        logger.error(f"Error parsing resume: {e}")
        return {}