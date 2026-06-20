"""Generate Technical_Architecture_Review.pdf for SPB project."""

import os
from fpdf import FPDF

OUT = os.path.join(os.path.dirname(__file__), "Technical_Architecture_Review.pdf")


class ArchPDF(FPDF):
    def __init__(self):
        super().__init__(orientation="P", unit="mm", format="A4")
        self.set_auto_page_break(auto=True, margin=20)
        self.section_number = 0

    def header(self):
        if self.page_no() > 1:
            self.set_font("Helvetica", "I", 8)
            self.set_text_color(120, 120, 120)
            self.cell(0, 8, "SPB - Technical Architecture Review", align="L")
            self.cell(0, 8, f"Page {self.page_no()}", align="R", new_x="LMARGIN", new_y="NEXT")
            self.line(10, 14, 200, 14)
            self.ln(4)

    def footer(self):
        if self.page_no() > 1:
            self.set_y(-15)
            self.set_font("Helvetica", "I", 7)
            self.set_text_color(150, 150, 150)
            self.cell(0, 10, f"Confidential - SPB Project 2026", align="C")

    def section_title(self, num, title):
        self.section_number = num
        self.set_font("Helvetica", "B", 16)
        self.set_text_color(20, 60, 120)
        self.ln(4)
        self.cell(0, 10, f"SECTION {num}: {title}", new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(20, 60, 120)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(4)

    def sub_title(self, text):
        self.set_font("Helvetica", "B", 12)
        self.set_text_color(40, 40, 40)
        self.cell(0, 8, text, new_x="LMARGIN", new_y="NEXT")
        self.ln(1)

    def sub_sub_title(self, text):
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(60, 60, 60)
        self.cell(0, 7, text, new_x="LMARGIN", new_y="NEXT")
        self.ln(1)

    def body_text(self, text):
        self.set_font("Helvetica", "", 9)
        self.set_text_color(30, 30, 30)
        self.multi_cell(0, 5, text)
        self.ln(2)

    def mono_block(self, text, size=7.5):
        self.set_font("Courier", "", size)
        self.set_text_color(20, 20, 20)
        lines = text.split("\n")
        for line in lines:
            if self.get_y() > 265:
                self.add_page()
            self.set_x(12)
            self.cell(0, 3.8, line, new_x="LMARGIN", new_y="NEXT")
        self.ln(2)

    def table(self, headers, rows, col_widths=None):
        if col_widths is None:
            col_widths = [190 / len(headers)] * len(headers)
        self.set_font("Helvetica", "B", 8)
        self.set_fill_color(20, 60, 120)
        self.set_text_color(255, 255, 255)
        for i, h in enumerate(headers):
            self.cell(col_widths[i], 7, h, border=1, fill=True, align="C")
        self.ln()
        self.set_font("Helvetica", "", 7.5)
        self.set_text_color(30, 30, 30)
        fill = False
        for row in rows:
            if self.get_y() > 260:
                self.add_page()
            if fill:
                self.set_fill_color(235, 240, 250)
            else:
                self.set_fill_color(255, 255, 255)
            max_h = 7
            for i, cell in enumerate(row):
                lines = self.multi_cell(col_widths[i], 7, str(cell), dry_run=True, output="LINES")
                h = len(lines) * 7
                if h > max_h:
                    max_h = h
            y_start = self.get_y()
            x_start = self.get_x()
            for i, cell in enumerate(row):
                self.set_xy(x_start + sum(col_widths[:i]), y_start)
                self.multi_cell(col_widths[i], 7, str(cell), border=1, fill=fill, max_line_height=7)
            self.set_y(max(self.get_y(), y_start + max_h))
            fill = not fill
        self.ln(3)


def build():
    pdf = ArchPDF()
    pdf.set_margins(10, 15, 10)

    # ════════════════════════════════════════════════════════════════
    # SECTION 1 - TITLE PAGE
    # ════════════════════════════════════════════════════════════════
    print("[1/9] Generating Title Page...")
    pdf.add_page()
    pdf.ln(50)
    pdf.set_font("Helvetica", "B", 32)
    pdf.set_text_color(20, 60, 120)
    pdf.cell(0, 14, "SPB - Student Placement Bridge", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(6)
    pdf.set_font("Helvetica", "", 18)
    pdf.set_text_color(80, 80, 80)
    pdf.cell(0, 10, "Technical Architecture Review Document", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(20)
    pdf.set_draw_color(20, 60, 120)
    pdf.line(60, pdf.get_y(), 150, pdf.get_y())
    pdf.ln(20)
    pdf.set_font("Helvetica", "", 12)
    pdf.set_text_color(60, 60, 60)
    pdf.cell(0, 8, "Version 1.0.0  |  June 2026", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)
    pdf.cell(0, 8, "SPB Project - Final Year Capstone", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(30)
    pdf.set_font("Helvetica", "I", 10)
    pdf.set_text_color(120, 120, 120)
    pdf.multi_cell(0, 6,
        "This document provides a comprehensive technical architecture review of the Student Placement Bridge (SPB) "
        "system, covering the Android application architecture, Python backend services, database schema, AI pipeline, "
        "security model, and deployment strategy.",
        align="C")

    # ════════════════════════════════════════════════════════════════
    # SECTION 2 - SYSTEM ARCHITECTURE OVERVIEW
    # ════════════════════════════════════════════════════════════════
    print("[2/9] Generating System Architecture Overview...")
    pdf.add_page()
    pdf.section_title(2, "System Architecture Overview")
    pdf.body_text(
        "The SPB system follows a client-server architecture with three primary tiers: an Android frontend "
        "built with Kotlin and Jetpack Compose following MVVM patterns, a Firebase backend providing "
        "authentication and real-time database services, and a Python FastAPI backend that hosts the AI/ML "
        "pipeline including CV parsing, semantic matching, interview scoring, and job recommendations.")

    arch_diagram = r"""
  ANDROID APP (Kotlin / Jetpack Compose / MVVM)
  +------------------------------------------------------------------+
  |  +----------+  +----------+  +----------+  +------------------+  |
  |  | Auth UI  |  | Job UI   |  | CV UI    |  | Interview UI     |  |
  |  +----+-----+  +----+-----+  +----+-----+  +--------+---------+  |
  |       |             |              |                  |           |
  |  +----v-------------v--------------v------------------v---------+ |
  |  |                     ViewModels (9 total)                      | |
  |  |  AuthVM | JobVM | CompanyVM | AppVM | DashboardVM | ...      | |
  |  +----+-------------+--------------+----------------+---------+ |
  |       |             |              |                  |           |
  |  +----v-------------v--------------v------------------v---------+ |
  |  |         Repositories (6) + AI Service Layer                   | |
  |  |  AuthRepo|JobRepo|AppRepo|NotifRepo|AIService|CVParser       | |
  |  +--+----------+----------+----------+------------------------+ |
  |     |          |          |          |                            |
  |     |     +----v----+ +---v---+ +----v-----+                      |
  |     |     |Firestore| |Storage| | Retrofit |                      |
  |     |     |  SDK    | |  SDK  | | (Backend)|                      |
  |     |     +----+----+ +---+---+ +----+-----+                      |
  +-----+----------+----------+----------+----------------------------+
        |          |          |          |
  +-----v----------v----------v----------v----------------------------+
  |                      NETWORK LAYER                                 |
  |    Firebase Auth  |  Firestore  |  Storage  |  HTTP (REST API)    |
  +------------------------------------------------------------------+
        |                            |                    |
  +-----v----------+          +-----v------+      +------v-------------+
  |  FIREBASE      |          |  FIREBASE  |      |  PYTHON BACKEND    |
  |  Auth          |          |  Firestore |      |  FastAPI @8000     |
  |  (Identity)    |          |  (NoSQL DB)|      |  +---------------+ |
  +----------------+          +------------+      |  | Gemini AI     | |
                                                  |  | (Primary)     | |
                                                  |  +---------------+ |
                                                  |  | spaCy NER     | |
                                                  |  | (Fallback)    | |
                                                  |  +---------------+ |
                                                  |  | BERT Matcher  | |
                                                  |  | (Embeddings)  | |
                                                  |  +---------------+ |
                                                  +-------------------+
"""
    pdf.mono_block(arch_diagram, size=6.5)
    pdf.body_text(
        "The architecture separates concerns into clear layers: Presentation (UI/Compose screens), "
        "Application (ViewModels with StateFlow), Data (Repositories accessing Firebase/FastAPI), "
        "and AI (Gemini/spaCy/BERT pipeline). The Python backend acts as a dedicated AI microservice, "
        "while Firebase serves as the primary data and auth layer for the Android app.")

    # ════════════════════════════════════════════════════════════════
    # SECTION 3 - ANDROID APP ARCHITECTURE
    # ════════════════════════════════════════════════════════════════
    print("[3/9] Generating Android App Architecture section...")
    pdf.add_page()
    pdf.section_title(3, "Android App Architecture (MVVM)")
    pdf.sub_title("Package Structure")
    pdf.body_text(
        "The Android app follows the MVVM (Model-View-ViewModel) architecture with a clean package "
        "structure separating concerns into UI, data, and domain layers. The app uses Kotlin, Jetpack "
        "Compose for declarative UI, Navigation Compose for routing, and Retrofit for network calls.")

    packages = [
        ("com.spb.app.ui.auth", "Authentication screens (Login, Register, ForgotPassword)"),
        ("com.spb.app.ui.job", "Job listing, details, and posting screens"),
        ("com.spb.app.ui.cv", "CV upload, parsing results, and management screens"),
        ("com.spb.app.ui.interview", "Interview scheduling, Q&A, and scoring screens"),
        ("com.spb.app.ui.company", "Company profile, dashboard, and management screens"),
        ("com.spb.app.ui.student", "Student profile, dashboard, and settings screens"),
        ("com.spb.app.ui.application", "Application tracking and status screens"),
        ("com.spb.app.ui.notification", "Notification list and preferences screens"),
        ("com.spb.app.ui.dashboard", "Main dashboard and analytics screens"),
        ("com.spb.app.viewmodel", "All ViewModels with StateFlow state management"),
        ("com.spb.app.repository", "Data repositories (Auth, Job, App, Notification, AI)"),
        ("com.spb.app.network", "Retrofit API service interface and interceptors"),
        ("com.spb.app.data.model", "Data classes matching Firestore document structures"),
        ("com.spb.app.data.firebase", "Firebase SDK wrappers for Auth, Firestore, Storage"),
        ("com.spb.app.ai", "AI service layer for Gemini integration via backend"),
        ("com.spb.app.util", "Utility classes, extensions, constants"),
        ("com.spb.app.navigation", "Navigation graph and route definitions"),
    ]
    pdf.table(["Package", "Description"], packages, [80, 110])

    pdf.sub_title("9 ViewModels")
    vms = [
        ("AuthViewModel", "AuthUiState", "login, register, forgotPassword, logout"),
        ("JobViewModel", "JobUiState", "fetchJobs, postJob, getJobDetails, searchJobs"),
        ("CompanyViewModel", "CompanyUiState", "getProfile, updateProfile, getDashboard"),
        ("ApplicationViewModel", "ApplicationUiState", "apply, getApplications, updateStatus"),
        ("DashboardViewModel", "DashboardUiState", "getStats, getRecentActivity"),
        ("CVViewModel", "CVUiState", "uploadCV, parseCV, getParsingResults"),
        ("InterviewViewModel", "InterviewUiState", "schedule, submitAnswer, getScore"),
        ("NotificationViewModel", "NotificationUiState", "fetchNotifs, markRead, getUnreadCount"),
        ("SkillViewModel", "SkillUiState", "matchSkills, analyzeSkills, getRecommendations"),
    ]
    pdf.table(["ViewModel", "State Class", "Key Functions"], vms, [35, 40, 115])

    pdf.sub_title("24 Navigation Screens")
    screens = [
        ("/splash", "SplashScreen", "App entry / loading"),
        ("/auth/login", "LoginScreen", "User login"),
        ("/auth/register", "RegisterScreen", "New user registration"),
        ("/auth/forgot-password", "ForgotPasswordScreen", "Password reset"),
        ("/student/dashboard", "StudentDashboardScreen", "Student main dashboard"),
        ("/student/jobs", "JobListScreen", "Browse available jobs"),
        ("/student/job/{id}", "JobDetailScreen", "Job details & apply"),
        ("/student/cv", "CVScreen", "CV upload & parsing"),
        ("/student/cv/result", "CVResultScreen", "Parsed CV details"),
        ("/student/interview", "InterviewListScreen", "Upcoming interviews"),
        ("/student/interview/{id}", "InterviewRoomScreen", "Live Q&A session"),
        ("/student/applications", "ApplicationListScreen", "Application statuses"),
        ("/student/recommendations", "RecommendationsScreen", "Job recommendations"),
        ("/student/skills", "SkillAnalysisScreen", "Skill gap analysis"),
        ("/student/profile", "StudentProfileScreen", "Profile management"),
        ("/company/dashboard", "CompanyDashboardScreen", "Company main dashboard"),
        ("/company/jobs", "CompanyJobListScreen", "Manage posted jobs"),
        ("/company/jobs/post", "PostJobScreen", "Post new job"),
        ("/company/job/{id}", "CompanyJobDetailScreen", "View applicants"),
        ("/company/applicant/{id}", "ApplicantDetailScreen", "Candidate details"),
        ("/company/interview/schedule", "ScheduleInterviewScreen", "Schedule interview"),
        ("/company/analytics", "CompanyAnalyticsScreen", "Hiring analytics"),
        ("/company/profile", "CompanyProfileScreen", "Company profile"),
        ("/notifications", "NotificationListScreen", "Notification center"),
    ]
    pdf.table(["Route", "Screen Composable", "Description"], screens, [50, 55, 85])

    pdf.add_page()
    pdf.sub_title("Network Layer - Retrofit API Endpoints (17 Endpoints)")
    pdf.body_text(
        "The Android app communicates with the Python backend via Retrofit over HTTP. All AI-heavy "
        "operations are routed through the backend API to keep the Gemini API key server-side.")

    endpoints = [
        ("POST", "/api/cv/parse", "Parse CV text via NLP"),
        ("POST", "/api/cv/parse-file", "Parse uploaded CV file"),
        ("POST", "/api/cv/match", "Match CV to job description"),
        ("POST", "/api/interview/score", "Score interview answers"),
        ("POST", "/api/interview/questions", "Generate interview questions"),
        ("POST", "/api/interview/sentiment", "Sentiment analysis on answers"),
        ("POST", "/api/interview/predict", "Predict hiring probability"),
        ("POST", "/api/skill/match", "Match skills to job requirements"),
        ("POST", "/api/skill/batch-match", "Batch match multiple students"),
        ("POST", "/api/skill/analyze", "Full skill analysis"),
        ("POST", "/api/skill/mcq/generate", "Generate MCQs for job"),
        ("POST", "/api/skill/mcq/parse", "Parse MCQ text to structured"),
        ("POST", "/api/recommendations/jobs", "Get job recommendations"),
        ("POST", "/api/recommendations/learning", "Get learning recommendations"),
        ("POST", "/api/recommendations/resume-analysis", "Resume quality analysis"),
        ("POST", "/api/cover-letter/generate", "Generate cover letter"),
        ("GET", "/health", "Backend health check"),
    ]
    pdf.table(["Method", "Route", "Description"], endpoints, [20, 70, 100])

    # ════════════════════════════════════════════════════════════════
    # SECTION 4 - PYTHON BACKEND ARCHITECTURE
    # ════════════════════════════════════════════════════════════════
    print("[4/9] Generating Python Backend Architecture section...")
    pdf.add_page()
    pdf.section_title(4, "Python Backend Architecture")
    pdf.sub_title("Complete File Structure")
    tree = r"""
  python_backend/
  |-- main.py                          # FastAPI app entry point
  |-- requirements.txt                 # Python dependency manifest
  |-- .env                             # Environment variables (API keys)
  |-- start_server.bat                 # Windows batch launcher
  |-- start_server.ps1                 # PowerShell launcher
  |
  |-- core/
  |   |-- config.py                    # Server config (host, port, CORS)
  |   |-- gemini.py                    # GeminiClient wrapper class
  |
  |-- api/
  |   |-- cv.py                        # CV parsing & matching routes
  |   |-- interview.py                 # Interview scoring & questions
  |   |-- skill_match.py               # Skill analysis & MCQ generation
  |   |-- recommendations.py           # Job & learning recommendations
  |   |-- cover_letter.py              # Cover letter generation
  |
  |-- spb_nlp/
  |   |-- __init__.py                  # Module version & exports
  |   |-- cv_parser.py                 # CVParser (regex) + SpacyNerParser
  |   |-- semantic_matcher.py          # BERT SemanticMatcher + n-gram fallback
  |   |-- shortlister.py               # Threshold filtering & ranking
  |   |-- recommender.py               # JobRecommender hybrid scoring
  |   |-- models.py                    # Pydantic models (CVParseResult, Job)
  |   |-- utils.py                     # extract_skills, gpa, edu helpers
  |   |-- evaluate.py                  # Evaluation & benchmarking
  |   |-- demo.py                      # CLI demo pipeline
  |
  |-- data/
  |   |-- uploads/                     # Uploaded CV files
  |
  |-- tests/
  |   |-- test_cv_parser.py            # CVParser unit tests
  |   |-- test_ner_parser.py           # SpacyNerParser tests
  |   |-- test_matcher.py              # SemanticMatcher tests
  |   |-- test_shortlister.py          # Shortlister tests
  |   |-- test_recommender.py          # Recommender tests
"""
    pdf.mono_block(tree, size=6.5)

    pdf.sub_title("18 API Routes")
    routes = [
        ("GET", "/", "Root info / endpoint listing", "No"),
        ("GET", "/health", "Server health + Gemini/NLP status", "No"),
        ("POST", "/api/cv/parse", "Parse CV text (NLP)", "No (NLP)"),
        ("POST", "/api/cv/parse-file", "Parse uploaded CV file", "No (NLP)"),
        ("POST", "/api/cv/match", "Match CV to job (Gemini+NLP)", "Optional"),
        ("POST", "/api/interview/score", "Score interview Q&A", "Yes"),
        ("POST", "/api/interview/questions", "Generate questions", "Yes"),
        ("POST", "/api/interview/sentiment", "Sentiment analysis", "Yes"),
        ("POST", "/api/interview/predict", "Hiring prediction", "Yes"),
        ("POST", "/api/skill/match", "Match skills (Gemini+NLP+basic)", "Optional"),
        ("POST", "/api/skill/batch-match", "Batch match students", "Optional"),
        ("POST", "/api/skill/analyze", "Full skill analysis", "Yes"),
        ("POST", "/api/skill/mcq/generate", "Generate MCQs", "Yes"),
        ("POST", "/api/skill/mcq/parse", "Parse MCQs from text", "Yes"),
        ("POST", "/api/recommendations/jobs", "Job recommendations", "Yes"),
        ("POST", "/api/recommendations/learning", "Learning recommendations", "Yes"),
        ("POST", "/api/recommendations/resume-analysis", "Resume analysis", "Yes"),
        ("POST", "/api/cover-letter/generate", "Generate cover letter", "Yes"),
    ]
    pdf.table(["Method", "Route", "Description", "AI Dep"], routes, [16, 72, 68, 34])

    pdf.sub_title("Core Configuration (core/config.py)")
    pdf.body_text(
        "Configuration is loaded from a .env file via python-dotenv. Key settings include "
        "GEMINI_API_KEY for Gemini AI access, GEMINI_MODEL (default: gemini-flash-lite-latest), "
        "SERVER_HOST and SERVER_PORT for the uvicorn server, and DEFAULT_MATCH_THRESHOLD (50.0). "
        "CORS is configured to allow all origins for development flexibility.")

    pdf.sub_title("Gemini Integration Pattern (core/gemini.py)")
    pdf.body_text(
        "The GeminiClient class wraps the google-genai SDK with three generation methods: "
        "generate() for plain text output, generate_json() for structured JSON responses, and "
        "generate_with_images() for multimodal inputs. The client is lazy-initialized and checks "
        "API key availability via is_available(). All AI API routes check this flag and return "
        "HTTP 503 if Gemini is not configured. JSON responses are cleaned of markdown fences "
        "before parsing to handle varied model outputs.")

    # ════════════════════════════════════════════════════════════════
    # SECTION 5 - DATABASE SCHEMA
    # ════════════════════════════════════════════════════════════════
    print("[5/9] Generating Database Schema section...")
    pdf.add_page()
    pdf.section_title(5, "Database Schema (Firestore)")
    pdf.body_text(
        "Firestore is used as the primary NoSQL database with 6 collections. All collections "
        "use auto-generated document IDs generated by Firestore. The schema is designed for "
        "denormalized reads to minimize joins, with some data duplication for performance.")

    pdf.sub_title("1. students (18 fields)")
    s_fields = [
        ("studentId", "string", "Unique student identifier (Firebase UID)"),
        ("name", "string", "Full name of the student"),
        ("email", "string", "University email address"),
        ("phone", "string", "Contact phone number"),
        ("password", "string", "Hashed password (Firebase Auth managed)"),
        ("major", "string", "Academic major/department"),
        ("cgpa", "number", "Cumulative GPA (0.0 - 4.0)"),
        ("skills", "array<string>", "List of skills (parsed from CV)"),
        ("experience", "string", "Work experience summary text"),
        ("education", "string", "Education history text"),
        ("certifications", "array<string>", "Professional certifications"),
        ("projects", "array<string>", "Academic/personal projects"),
        ("resumeUrl", "string", "Firebase Storage URL for CV file"),
        ("profileImageUrl", "string", "Profile photo URL"),
        ("fcmToken", "string", "Firebase Cloud Messaging token"),
        ("createdAt", "timestamp", "Account creation timestamp"),
        ("updatedAt", "timestamp", "Last profile update timestamp"),
        ("notificationPreferences", "map", "Push notification preferences"),
    ]
    pdf.table(["Field", "Type", "Description"], s_fields, [40, 30, 120])

    pdf.add_page()
    pdf.sub_title("2. companies (14 fields + nested ContactPerson)")
    c_fields = [
        ("companyId", "string", "Unique company identifier (Firebase UID)"),
        ("companyName", "string", "Registered company name"),
        ("email", "string", "Company contact email"),
        ("phone", "string", "Company phone number"),
        ("password", "string", "Hashed password (Firebase Auth managed)"),
        ("industry", "string", "Industry sector (e.g. IT, Finance)"),
        ("description", "string", "Company description / about us"),
        ("website", "string", "Company website URL"),
        ("location", "string", "Office/campus location"),
        ("logoUrl", "string", "Company logo image URL"),
        ("fcmToken", "string", "FCM push notification token"),
        ("createdAt", "timestamp", "Account creation timestamp"),
        ("updatedAt", "timestamp", "Last profile update"),
        ("isVerified", "boolean", "Verification status"),
        ("contactPerson", "map", "Nested object:"),
        ("  .name", "string", "Contact person name"),
        ("  .designation", "string", "Contact person job title"),
        ("  .phone", "string", "Contact person phone"),
        ("  .email", "string", "Contact person email"),
    ]
    pdf.table(["Field", "Type", "Description"], c_fields, [40, 30, 120])

    pdf.ln(2)
    pdf.sub_title("3. jobs (22+ fields, nested MCQ)")
    j_fields = [
        ("jobId", "string", "Unique job identifier (auto-ID)"),
        ("companyId", "string", "Reference to companies collection"),
        ("companyName", "string", "Company display name (denormalized)"),
        ("title", "string", "Job title / position name"),
        ("description", "string", "Detailed job description"),
        ("requiredSkills", "array<string>", "Required skill keywords"),
        ("preferredSkills", "array<string>", "Nice-to-have skills"),
        ("requiredEducation", "string", "Minimum education requirement"),
        ("minimumGpa", "number", "Minimum GPA threshold"),
        ("experienceRequired", "string", "Years/level of experience"),
        ("jobType", "string", "Full-time / Part-time / Internship"),
        ("workMode", "string", "On-site / Remote / Hybrid"),
        ("location", "string", "Job location"),
        ("salaryRange", "string", "Salary range string"),
        ("vacancies", "number", "Number of open positions"),
        ("applicationDeadline", "timestamp", "Last date to apply"),
        ("status", "string", "Active / Closed / Draft"),
        ("mcq", "map", "Nested MCQ object:"),
        ("  .question", "string", "MCQ question text"),
        ("  .options", "array<string>", "MCQ answer choices"),
        ("  .correctAnswerIndex", "number", "Index of correct answer"),
        ("  .answer", "string", "Correct answer text"),
        ("createdAt", "timestamp", "Job posting timestamp"),
        ("updatedAt", "timestamp", "Last update timestamp"),
    ]
    pdf.table(["Field", "Type", "Description"], j_fields, [40, 30, 120])

    pdf.add_page()
    pdf.sub_title("4. applications (28+ fields, nested InterviewData & ActivityLog)")
    a_fields = [
        ("applicationId", "string", "Unique application ID (auto-ID)"),
        ("studentId", "string", "Reference to students collection"),
        ("studentName", "string", "Applicant name (denormalized)"),
        ("jobId", "string", "Reference to jobs collection"),
        ("jobTitle", "string", "Job title applied for (denormalized)"),
        ("companyId", "string", "Reference to companies collection"),
        ("companyName", "string", "Company name (denormalized)"),
        ("status", "string", "Pending / Shortlisted / Accepted / Rejected"),
        ("matchScore", "number", "Semantic match score (0-100)"),
        ("coverLetter", "string", "Applicant's cover letter text"),
        ("appliedAt", "timestamp", "Application submission timestamp"),
        ("updatedAt", "timestamp", "Status update timestamp"),
        ("notes", "string", "Company's internal notes"),
        ("interviewData", "map", "Nested interview object:"),
        ("  .scheduledAt", "timestamp", "Interview schedule time"),
        ("  .interviewType", "string", "Technical / HR / Behavioral"),
        ("  .status", "string", "Scheduled / Completed / Cancelled"),
        ("  .questions", "array<string>", "Interview questions asked"),
        ("  .answers", "array<string>", "Candidate's answers"),
        ("  .score", "number", "Interview score (0-100)"),
        ("  .feedback", "string", "Interviewer feedback text"),
        ("  .meetLink", "string", "Google Meet / Zoom link"),
        ("  .sentimentScore", "number", "Sentiment analysis score"),
        ("  .isAIGenerated", "boolean", "Was AI used for scoring?"),
        ("activityLog", "array<map>", "Array of activity entries:"),
        ("  [].action", "string", "Action performed"),
        ("  [].timestamp", "timestamp", "When action occurred"),
        ("  [].details", "string", "Action details/notes"),
    ]
    pdf.table(["Field", "Type", "Description"], a_fields, [40, 30, 120])

    pdf.ln(2)
    pdf.sub_title("5. notifications (15 fields)")
    n_fields = [
        ("notificationId", "string", "Unique notification ID"),
        ("userId", "string", "Target user (student or company)"),
        ("userRole", "string", "student / company"),
        ("type", "string", "application_update / interview / system"),
        ("title", "string", "Notification title"),
        ("message", "string", "Notification body text"),
        ("data", "map", "Additional payload data"),
        ("relatedJobId", "string", "Optional job reference"),
        ("relatedApplicationId", "string", "Optional application reference"),
        ("isRead", "boolean", "Read/unread status"),
        ("createdAt", "timestamp", "Notification creation time"),
        ("readAt", "timestamp", "When user read the notification"),
        ("priority", "string", "high / normal / low"),
        ("imageUrl", "string", "Optional image URL"),
        ("deepLink", "string", "App navigation deep link"),
    ]
    pdf.table(["Field", "Type", "Description"], n_fields, [40, 30, 120])

    pdf.ln(2)
    pdf.sub_title("6. pending_notifications (3 fields)")
    pn_fields = [
        ("notificationId", "string", "Unique notification ID"),
        ("userId", "string", "Target user ID"),
        ("data", "map", "Full notification data payload"),
    ]
    pdf.table(["Field", "Type", "Description"], pn_fields, [40, 30, 120])

    pdf.body_text(
        "Relationships: students.applications -> jobs (via studentId/jobId). "
        "companies.jobs -> companies (via companyId). "
        "applications.jobId -> jobs.jobId. "
        "applications.studentId -> students.studentId. "
        "notifications.userId -> students.studentId OR companies.companyId. "
        "pending_notifications is a staging collection for FCM delivery tracking.")

    # ════════════════════════════════════════════════════════════════
    # SECTION 6 - DATA FLOW DIAGRAMS
    # ════════════════════════════════════════════════════════════════
    print("[6/9] Generating Data Flow Diagrams...")
    pdf.add_page()
    pdf.section_title(6, "Data Flow Diagrams")

    pdf.sub_title("Flow 1: CV Upload -> Parse -> Match")
    f1 = r"""
  +----------+     +-----------+     +----------+     +----------+
  | Student  |     | Firebase  |     | Python   |     | Firestore |
  | (Android)|     | Storage   |     | Backend  |     | (Results)|
  +----+-----+     +-----+-----+     +----+-----+     +-----+----+
       |                 |                 |                 |
       | 1. Upload PDF   |                 |                 |
       |---------------->|                 |                 |
       |                 | 2. Store file   |                 |
       |                 |<----------------|                 |
       | 3. Return URL   |                 |                 |
       |<----------------|                 |                 |
       |                 |                 |                 |
       | 4. POST /api/cv/parse (text)      |                 |
       |---------------------------------->|                 |
       |                 |                 |                 |
       |                 |           5. Parse with:          |
       |                 |           - Geminin (if avail)    |
       |                 |           OR spaCy NER            |
       |                 |           OR Regex fallback       |
       |                 |                 |                 |
       | 6. Return parsed data             |                 |
       |<----------------------------------|                 |
       |                 |                 |                 |
       | 7. POST /api/cv/match             |                 |
       |---------------------------------->|                 |
       |                 |           8. Match with:          |
       |                 |           - BERT embeddings       |
       |                 |           OR n-gram similarity    |
       |                 |                 |                 |
       | 9. Return match score + skills    |                 |
       |<----------------------------------|                 |
       |                 |                 |                 |
       | 10. Save to Firestore             |                 |
       |--------------------------------------------------->|
       |                 |                 |                 |
       | 11. Show match results to user    |                 |
       |< (Realtime listener)              |                 |
"""
    pdf.mono_block(f1, size=5.8)

    pdf.sub_title("Flow 2: Interview Flow (Question -> Answer -> Score)")
    f2 = r"""
  +----------+     +----------+     +----------+
  | Student  |     | FastAPI  |     | Gemini   |
  | (Android)|     | Backend  |     | AI       |
  +----+-----+     +----+-----+     +----+-----+
       |                 |                 |
       | 1. POST /api/interview/questions  |
       |---------------->|                 |
       |                 | 2. Generate Qs  |
       |                 |---------------->|
       |                 | 3. Questions    |
       |                 |<----------------|
       | 4. Return Qs    |                 |
       |<----------------|                 |
       |                 |                 |
       | 5. Student answers (text)         |
       |                                   |
       | 6. POST /api/interview/score      |
       |---------------->|                 |
       |                 | 7. Evaluate     |
       |                 |---------------->|
       |                 | 8. Score+feedback|
       |                 |<----------------|
       | 9. Return score, strengths,       |
       |    improvements, tone, clarity    |
       |<----------------|                 |
       |                 |                 |
       | 10. POST /api/interview/predict   |
       |---------------->|                 |
       |                 | 11. Predict     |
       |                 |---------------->|
       |                 | 12. Probability |
       |                 |<----------------|
       | 13. Show hiring prediction        |
       |<----------------|                 |
"""
    pdf.mono_block(f2, size=5.8)

    pdf.add_page()
    pdf.sub_title("Flow 3: Job Posting -> Batch Matching -> Notification")
    f3 = r"""
  +----------+     +----------+     +----------+     +----------+
  | Company  |     | FastAPI  |     | Firestore|     | FCM      |
  | (Android)|     | Backend  |     |          |     |          |
  +----+-----+     +----+-----+     +----+-----+     +----+-----+
       |                 |                 |                 |
       | 1. Post job     |                 |                 |
       |---------------->|                 |                 |
       |                 | 2. Save job     |                 |
       |                 |---------------->|                 |
       |                 | 3. Confirm      |                 |
       |                 |<----------------|                 |
       | 4. Job created  |                 |                 |
       |<----------------|                 |                 |
       |                 |                 |                 |
       | 5. POST /api/skill/batch-match    |                 |
       |---------------->|                 |                 |
       |                 | 6. Fetch all students            |
       |                 |---------------->|                 |
       |                 | 7. Student list |                 |
       |                 |<----------------|                 |
       |                 |                 |                 |
       |           8. For each student: compute              |
       |           match score using SemanticMatcher         |
       |                 |                 |                 |
       | 9. Ranked results with scores     |                 |
       |<----------------|                 |                 |
       |                 |                 |                 |
       | 10. Notify shortlisted students   |                 |
       |                 |                 |---------------->|
       |                 |                 | 11. Push notif  |
       |                 |                 |                 |
"""
    pdf.mono_block(f3, size=5.8)

    pdf.sub_title("Flow 4: Authentication Flow")
    f4 = r"""
  +----------+     +----------+     +----------+
  | Android  |     | Firebase |     | Firestore|
  | App      |     | Auth     |     | (User DB)|
  +----+-----+     +----+-----+     +----+-----+
       |                 |                 |
       | 1. Email+Password                  |
       |---------------->|                 |
       |                 | 2. Auth check   |
       |                 | (signInWithEmailAndPassword) |
       |                 |                 |
       | 3. Firebase User + ID Token        |
       |<----------------|                 |
       |                 |                 |
       | 4. Fetch user profile              |
       |---------------------------------->|
       | 5. Return {role, name, ...}       |
       |<----------------------------------|
       |                 |                 |
       | 6. Navigate to role-based          |
       |    dashboard                      |
       |                 |                 |
       | 7. Token refresh (auto)           |
       |<----------------|                 |
       |                 |                 |
       | 8. Token attached to API calls    |
       |    via Retrofit interceptor       |
       |                 |                 |
       | For registration:                 |
       | 1. FirebaseAuth.createUser()      |
       | 2. Firestore document created     |
       |    in students or companies       |
       |    collection                     |
"""
    pdf.mono_block(f4, size=5.8)

    # ════════════════════════════════════════════════════════════════
    # SECTION 7 - AI ARCHITECTURE
    # ════════════════════════════════════════════════════════════════
    print("[7/9] Generating AI Architecture section...")
    pdf.add_page()
    pdf.section_title(7, "AI Architecture & Fallback Chain")
    pdf.body_text(
        "The SPB system implements a multi-tier AI architecture designed for resilience. The primary AI "
        "provider is Google Gemini API, with automatic fallback through spaCy NER, BERT embeddings, "
        "and finally regex-based parsers. This ensures the system continues to function even when "
        "external API services are unavailable.")

    pdf.sub_title("Tier 1: Gemini API (google-genai SDK)")
    pdf.body_text(
        "Model: gemini-flash-lite-latest (configurable via GEMINI_MODEL env var). "
        "Used for CV parsing (structured JSON extraction), interview scoring and feedback, "
        "skill analysis with career recommendations, MCQ generation and parsing, "
        "job recommendations with ranking, sentiment analysis, and cover letter generation. "
        "Requires GEMINI_API_KEY in .env file. Returns HTTP 503 if unavailable.")

    pdf.sub_title("Tier 2: spaCy NER (SpacyNerParser)")
    pdf.body_text(
        "Model: en_core_web_lg. Used as fallback for CV parsing when Gemini is unavailable or "
        "for offline operation. Extracts entities: PERSON (candidate name), ORG (organizations), "
        "PRODUCT (skills/tools). Also extracts structured fields including email (regex), "
        "phone (regex), skills (NER + keyword list), education, experience, GPA, certifications, "
        "and projects. Falls back to regex-based CVParser if spaCy model not loaded.")

    pdf.sub_title("Tier 3: Regex-based Parser (CVParser)")
    pdf.body_text(
        "Zero-dependency CV parser that uses regex patterns and a dictionary of 172 skill keywords. "
        "Extracts candidate name (line-based heuristics), email, phone, GPA, education, experience, "
        "projects, and certifications. Always available regardless of external dependencies.")

    pdf.sub_title("Semantic Matching Pipeline")
    pdf.body_text(
        "Primary: sentence-transformers (all-MiniLM-L6-v2) producing 384-dimensional embeddings. "
        "Cosine similarity is computed between CV and job description embeddings. The match score "
        "combines: skill keyword overlap (0-60%), semantic similarity (0-10%), experience score "
        "(0-15%), education score (0-10%), and extra bonus (0-5%) for a total of 0-100.")

    pdf.sub_title("Fallback: Character n-gram Similarity")
    pdf.body_text(
        "When BERT embeddings cannot be computed (e.g., model not downloaded), the system falls back "
        "to character n-gram cosine similarity (bigrams + trigrams). This is a zero-dependency approach "
        "using pure Python collections.Counter and math operations. Used by the SemanticMatcher class.")

    pdf.sub_title("AI Tier by Endpoint")
    tiers = [
        ("POST /api/cv/parse", "NLP (SpacyNerParser -> CVParser)"),
        ("POST /api/cv/parse-file", "NLP (SpacyNerParser -> CVParser)"),
        ("POST /api/cv/match", "NLP SemanticMatcher -> Basic n-gram"),
        ("POST /api/interview/score", "Gemini (required)"),
        ("POST /api/interview/questions", "Gemini (required)"),
        ("POST /api/interview/sentiment", "Gemini (required)"),
        ("POST /api/interview/predict", "Gemini (required)"),
        ("POST /api/skill/match", "SemanticMatcher -> Gemini -> Basic"),
        ("POST /api/skill/batch-match", "SemanticMatcher -> Basic overlap"),
        ("POST /api/skill/analyze", "Gemini (required)"),
        ("POST /api/skill/mcq/generate", "Gemini (required)"),
        ("POST /api/skill/mcq/parse", "Gemini (required)"),
        ("POST /api/recommendations/jobs", "Gemini (required)"),
        ("POST /api/recommendations/learning", "Gemini (required)"),
        ("POST /api/recommendations/resume-analysis", "Gemini (required)"),
        ("POST /api/cover-letter/generate", "Gemini (required)"),
    ]
    pdf.table(["Endpoint", "AI Tier (Primary -> Fallback)"], tiers, [55, 135])

    # ════════════════════════════════════════════════════════════════
    # SECTION 8 - SECURITY ARCHITECTURE
    # ════════════════════════════════════════════════════════════════
    print("[8/9] Generating Security Architecture section...")
    pdf.add_page()
    pdf.section_title(8, "Security Architecture")

    pdf.sub_title("API Key Management")
    pdf.body_text(
        "The Gemini API key is stored exclusively in the .env file on the backend server. It is NEVER "
        "embedded in the Android app code or APK. The Android app communicates with Gemini indirectly "
        "through the Python FastAPI backend, ensuring the API key remains server-side only.")

    pdf.sub_title("Firebase Security Rules")
    rules = r"""
  // students collection
  match /students/{userId} {
    allow read, write: if request.auth != null
      && request.auth.uid == userId;
  }

  // companies collection
  match /companies/{companyId} {
    allow read, write: if request.auth != null
      && request.auth.uid == companyId;
  }

  // jobs collection - public read, company write
  match /jobs/{jobId} {
    allow read: if request.auth != null;
    allow create: if request.auth != null
      && request.auth.token.role == "company";
    allow update, delete: if request.auth != null
      && resource.data.companyId == request.auth.uid;
  }

  // applications - student sees own, company sees own jobs
  match /applications/{appId} {
    allow read: if request.auth != null
      && (request.auth.uid == resource.data.studentId
      || request.auth.uid == resource.data.companyId);
    allow create: if request.auth != null;
    allow update: if request.auth != null
      && request.auth.uid == resource.data.companyId;
  }

  // notifications - user sees own
  match /notifications/{notifId} {
    allow read, write: if request.auth != null
      && request.auth.uid == resource.data.userId;
  }
"""
    pdf.mono_block(rules, size=6.5)

    pdf.sub_title("Network Security Config (Android)")
    pdf.body_text(
        "The Android app uses a network security config that permits cleartext HTTP traffic to "
        "local network IPs (192.168.x.x) for development purposes only. In production, all traffic "
        "is HTTPS. The backend CORS is configured to allow all origins for development, with "
        "production deployment restricting to the Android app's origin.")

    pdf.sub_title("Additional Security Measures")
    pdf.body_text(
        "1. No direct Gemini calls from Android - API key stays server-side.\n"
        "2. Firebase Auth manages all user authentication with email/password.\n"
        "3. Firestore security rules enforce document-level access control.\n"
        "4. Retrofit interceptor attaches Firebase ID token to every API request.\n"
        "5. Backend validates and sanitizes all user inputs before processing.\n"
        "6. File uploads restricted to PDF format for CV files.\n"
        "7. Environment variables (.env) excluded from version control.\n"
        "8. CORS middleware allows configurable origins.")

    # ════════════════════════════════════════════════════════════════
    # SECTION 9 - DEPLOYMENT ARCHITECTURE
    # ════════════════════════════════════════════════════════════════
    print("[9/9] Generating Deployment Architecture section...")
    pdf.add_page()
    pdf.section_title(9, "Deployment Architecture")

    pdf.sub_title("Development Environment")
    dev = r"""
  +------------------+       +------------------+       +------------------+
  | Android Device   |       | Local Network    |       | Python Backend   |
  | (USB/Wi-Fi)      |------>| 192.168.x.x      |------>| FastAPI + Uvicorn|
  | - Kotlin/Compose |       |                  |       | Port 8000        |
  | - Direct install  |       |                  |       | --reload enabled |
  | - FCM via Firebase|       |                  |       | .env with API key|
  +------------------+       +------------------+       +--------+---------+
                                                                  |
                                                                  v
                                                         +------------------+
                                                         | Gemini API       |
                                                         | (Cloud - Google) |
                                                         +------------------+
    """
    pdf.mono_block(dev, size=6.5)

    pdf.sub_title("Production Environment")
    prod = r"""
  +------------------+       +------------------+       +------------------+
  | Android Device   |       | Internet         |       | Cloud Server     |
  | (Play Store)     |------>| (HTTPS/TLS)      |------>| FastAPI + Gunicorn|
  | - Signed APK     |       |                  |       | - Auto-scaling   |
  | - SSL pinning    |       |                  |       | - SSL cert       |
  | - Production FCM |       |                  |       | - Rate limiting  |
  +------------------+       +------------------+       +--------+---------+
                                                                  |
                                                         +--------+---------+
                                                         | Firestore (Cloud)|
                                                         | + Firebase Auth  |
                                                         | + Storage        |
                                                         | + FCM            |
                                                         +------------------+
    """
    pdf.mono_block(prod, size=6.5)

    pdf.sub_title("Server Startup (Development)")
    pdf.body_text(
        "The Python backend is started using uvicorn with the --reload flag for hot reload during "
        "development. The server binds to the configured SERVER_HOST (default: 192.168.0.114) "
        "and SERVER_PORT (default: 8000). The CORS middleware allows all origins for development. "
        "Startup scripts are provided as start_server.bat and start_server.ps1 for Windows.")

    startup = r"""
  # From python_backend/ directory:
  uvicorn main:app --host 192.168.0.114 --port 8000 --reload

  # Or using the startup scripts:
  .\start_server.bat    # Windows batch
  .\start_server.ps1    # PowerShell
  """
    pdf.mono_block(startup, size=6.5)

    pdf.sub_title("Environment Configuration (.env)")
    env_example = r"""
  GEMINI_API_KEY=your_gemini_api_key_here
  GEMINI_MODEL=gemini-flash-lite-latest
  SERVER_HOST=192.168.0.114
  SERVER_PORT=8000
  """
    pdf.mono_block(env_example, size=6.5)

    # ── Save ───────────────────────────────────────────────────────
    pdf.output(OUT)
    print(f"\n{'='*60}")
    print(f" PDF generated successfully!")
    print(f" Location: {OUT}")
    print(f" Pages:    {pdf.page_no()}")
    print(f"{'='*60}")


if __name__ == "__main__":
    build()
