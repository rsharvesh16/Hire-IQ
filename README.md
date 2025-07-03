# Hire-IQ

**HireIQ** is an AI-powered technical interview management system built using **FastAPI**. It enhances the recruitment experience for HR professionals and candidates by automating interview scheduling, AI-generated questioning, real-time audio processing, and performance evaluation with detailed PDF reports.

---

## 📌 Features

### 👩‍💼 For HR Managers:

* Secure registration and login
* Schedule interviews with job descriptions and resumes
* Customize or auto-generate questions
* View and download AI-evaluated interview reports

### 👨‍💻 For Candidates:

* Login via secure form or session-based auth
* Participate in AI-driven interviews
* Answer questions through typed or spoken responses
* Upload audio/video and receive real-time transcriptions

---

## 🧠 Technologies Used

| Category             | Tech Stack / Tools                                        |
| -------------------- | --------------------------------------------------------- |
| **Backend**          | FastAPI (Python), Starlette                               |
| **Database**         | SQLAlchemy ORM + SQLite/PostgreSQL                        |
| **Authentication**   | OAuth2, Session & Cookie-based auth                       |
| **AI/LLM**           | Custom LLM Agent (e.g., OpenAI or AWS Bedrock)            |
| **Audio Processing** | Nova Sonic (AWS Bedrock) for speech-to-text               |
| **PDF Reporting**    | Auto-generated interview feedback reports in PDF format   |
| **Resume Parsing**   | PDF-based resume analysis using custom parser             |
| **Web Templating**   | Jinja2 for dynamic HTML generation                        |
| **File Handling**    | Secure upload and storage of resumes, audio, and video    |
| **CORS/Security**    | FastAPI Middleware + HTTPOnly cookies + SessionMiddleware |

---

## 🧰 Core Functionalities

* 🔐 User authentication via session and cookie-based mechanisms
* 📄 Resume upload and automatic parsing before interview
* 🤖 Adaptive question flow using a language model (LLM)
* 🎙️ Audio transcription from candidate answers in real-time
* 📊 AI-based scoring, feedback, and recommendation
* 📥 PDF report generation summarizing interview performance

---

## 🧠 Use Cases

* **Tech Hiring:** Automate and scale technical interviews for candidates.
* **Campus Placements:** Conduct and evaluate multiple student interviews efficiently.
* **Mock Interviews:** Provide AI-based feedback to students or job seekers.
* **Remote Recruitment:** Replace live panels with intelligent question-answer workflows.
* **Skill Benchmarking:** Evaluate candidate skills uniformly using AI.

---

## 🔐 Authentication Highlights

* OAuth2 Password Grant and form-based login
* Session tracking using `SessionMiddleware`
* Secure cookie (`auth_token`) support for browser clients
* Redirect based on user role (`HR` or `Candidate`)

---


## 🙌 Why HireIQ?

HireIQ bridges the gap between automation and human-like interview evaluation. It saves time for recruiters, ensures fairness for candidates, and leverages AI to improve hiring accuracy.

