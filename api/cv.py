import json
import logging
import tempfile
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel

from core.gemini import gemini
from core.config import DEFAULT_MATCH_THRESHOLD

try:
    from spb_nlp.cv_parser import CVParser, SpacyNerParser
    from spb_nlp import models as nlp_models
    from spb_nlp.semantic_matcher import SemanticMatcher
    from spb_nlp.utils import extract_skills, extract_education, extract_experience, estimate_years_of_experience, extract_gpa, extract_certifications, extract_projects, clean_text
    NLP_AVAILABLE = True
    _semantic_matcher = SemanticMatcher(lazy_load=True)
except ImportError:
    NLP_AVAILABLE = False
    _semantic_matcher = None

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/cv", tags=["CV Parsing & Matching"])


class CVParseRequest(BaseModel):
    text: str


class CVParseResponse(BaseModel):
    candidate_name: str = ""
    email: str = ""
    phone: str = ""
    skills: list[str] = []
    experience: str = ""
    education: str = ""
    gpa: float = 0.0
    years_of_experience: float = 0.0
    certifications: list[str] = []
    projects: list[str] = []
    summary: str = ""
    parsed_by: str = ""


class MatchRequest(BaseModel):
    cv_text: str = ""
    job_title: str
    job_description: str
    required_skills: list[str] = []
    required_education: str = "Any"
    minimum_gpa: float = 0.0
    matching_threshold: float = DEFAULT_MATCH_THRESHOLD
    candidate_skills: list[str] | None = None
    candidate_years_experience: float | None = None
    candidate_education: str | None = None
    candidate_gpa: float | None = None
    candidate_certifications: list[str] | None = None
    candidate_projects: list[str] | None = None


class MatchResponse(BaseModel):
    match_score: float = 0.0
    meets_threshold: bool = False
    matching_skills: list[str] = []
    missing_skills: list[str] = []
    experience_match: bool = False
    gpa_match: bool = False
    semantic_similarity: float = 0.0
    skill_score: float = 0.0
    experience_score: float = 0.0
    education_score: float = 0.0
    extra_score: float = 0.0
    recommendations: list[str] = []
    detailed_analysis: str = ""


def _parse_cv_with_nlp(text: str) -> CVParseResponse:
    parser = SpacyNerParser()
    result = parser.parse_text(text)

    years_exp = estimate_years_of_experience(text) or result.years_of_experience
    gpa = extract_gpa(text) or result.gpa
    certs = extract_certifications(text) or result.certifications
    projs = extract_projects(text) or result.projects
    skills = result.skills or extract_skills(text)
    edu = result.education or extract_education(text)
    exp = result.experience or extract_experience(text)

    return CVParseResponse(
        candidate_name=result.candidate_name or result.name,
        email=result.email,
        phone=result.phone,
        skills=skills,
        experience=exp,
        education=edu,
        gpa=gpa,
        years_of_experience=years_exp,
        certifications=certs,
        projects=projs,
        summary=result.summary or "",
        parsed_by="nlp",
    )


def _parse_cv_with_gemini(text: str) -> CVParseResponse:
    prompt = f"""You are an expert CV parser. Extract structured data from the following resume text.

Resume:
{text[:8000]}

Return ONLY valid JSON with these fields:
{{
  "candidate_name": "...",
  "email": "...",
  "phone": "...",
  "skills": [...],
  "experience": "...",
  "education": "...",
  "gpa": 0.0,
  "years_of_experience": 0.0,
  "certifications": [...],
  "projects": [...],
  "summary": "..."
}}"""
    data = gemini.generate_json(prompt)
    return CVParseResponse(
        candidate_name=data.get("candidate_name", ""),
        email=data.get("email", ""),
        phone=data.get("phone", ""),
        skills=data.get("skills", []),
        experience=data.get("experience", ""),
        education=data.get("education", ""),
        gpa=float(data.get("gpa", 0) or 0),
        years_of_experience=float(data.get("years_of_experience", 0) or 0),
        certifications=data.get("certifications", []),
        projects=data.get("projects", []),
        summary=data.get("summary", ""),
        parsed_by="gemini",
    )


@router.post("/parse", response_model=CVParseResponse)
def parse_cv(request: CVParseRequest):
    if not request.text.strip():
        raise HTTPException(status_code=400, detail="Empty CV text")

    if NLP_AVAILABLE:
        return _parse_cv_with_nlp(request.text)

    raise HTTPException(status_code=503, detail="CV parsing unavailable")


@router.post("/parse-file", response_model=CVParseResponse)
async def parse_cv_file(file: UploadFile = File(...)):
    contents = await file.read()
    try:
        text = contents.decode("utf-8")
    except UnicodeDecodeError:
        ext = Path(file.filename or "").suffix.lower()
        if ext == ".pdf" and NLP_AVAILABLE:
            parser = SpacyNerParser()
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                tmp.write(contents)
                tmp_path = tmp.name
            try:
                result = parser.parse_pdf(tmp_path)
                text = result.raw_text
            finally:
                Path(tmp_path).unlink(missing_ok=True)
        else:
            raise HTTPException(status_code=400, detail="Unsupported file format")
    return parse_cv(CVParseRequest(text=text))


@router.post("/match", response_model=MatchResponse)
def match_cv_to_job(request: MatchRequest):
    # Use structured candidate data if provided, else fall back to raw text parsing
    if request.candidate_skills is not None:
        candidate_skills = request.candidate_skills
        years_exp = request.candidate_years_experience or 0.0
        edu_text = (request.candidate_education or "").lower()
        gpa = request.candidate_gpa or 0.0
        certs = request.candidate_certifications or []
        projs = request.candidate_projects or []
    else:
        cv_text = request.cv_text.strip()
        if not cv_text:
            raise HTTPException(status_code=400, detail="Empty CV text")
        candidate_skills = extract_skills(cv_text)
        years_exp = estimate_years_of_experience(cv_text)
        edu_text = extract_education(cv_text).lower()
        gpa = extract_gpa(cv_text)
        certs = extract_certifications(cv_text)
        projs = extract_projects(cv_text)

    # Normalize skills for fuzzy matching
    def normalize_skill(s: str) -> str:
        s = s.lower().strip()
        replacements = {
            "machine learning": "ml", "artificial intelligence": "ai",
            "javascript": "js", "typescript": "ts",
            "react native": "reactnative", "c++": "cpp", "c#": "csharp",
            ".net": "dotnet", "node.js": "nodejs", "express.js": "express",
        }
        return replacements.get(s, s)

    required_skills_norm = [normalize_skill(s) for s in request.required_skills]
    candidate_skills_norm = [normalize_skill(s) for s in candidate_skills]

    # Expand: partial matching - "Android" matches "android development"
    expanded = set(candidate_skills_norm)
    for cs in candidate_skills_norm:
        for rs in required_skills_norm:
            if rs in cs or cs in rs:
                expanded.add(rs)

    matching = list(expanded & set(required_skills_norm))
    missing = list(set(required_skills_norm) - expanded)
    skill_ratio = len(matching) / len(required_skills_norm) if required_skills_norm else 0

    # Use SemanticMatcher when NLP is available (handles BERT + composite scoring)
    if NLP_AVAILABLE and _semantic_matcher is not None:
        try:
            cv_result = nlp_models.CVParseResult(
                skills=candidate_skills,
                education=edu_text,
                gpa=gpa,
                years_of_experience=years_exp,
                certifications=certs,
                projects=projs,
            )
            job = nlp_models.Job(
                title=request.job_title,
                description=request.job_description,
                required_skills=request.required_skills,
                matching_threshold=request.matching_threshold,
            )
            result = _semantic_matcher.match_cv_to_job(cv_result, job)

            # Override matching/missing with normalized fuzzy results
            return MatchResponse(
                match_score=round(result.match_score, 1),
                meets_threshold=result.match_score >= request.matching_threshold,
                matching_skills=sorted(matching) if matching else sorted(result.matching_skills),
                missing_skills=sorted(missing) if missing else sorted(result.missing_skills),
                experience_match=years_exp >= 1.0,
                gpa_match=gpa >= request.minimum_gpa,
                semantic_similarity=result.cosine_similarity * 10.0,
                skill_score=result.skill_score,
                experience_score=result.experience_score,
                education_score=result.education_score,
                extra_score=result.extra_score,
                recommendations=result.recommendations or ([f"Consider learning: {', '.join(missing[:3])}"] if missing else []),
                detailed_analysis=result.detailed_analysis,
            )
        except Exception as e:
            logger.warning("SemanticMatcher failed: %s", e)

    # Fallback basic matching
    skill_score = skill_ratio * 60.0
    exp_score = 15.0 if years_exp >= 5 else 12.0 if years_exp >= 2 else 8.0 if years_exp >= 1 else 4.0 if years_exp > 0 else 0.0
    edu_score = 10.0 if "phd" in edu_text else 8.0 if "master" in edu_text else 6.0 if "bachelor" in edu_text else 4.0 if edu_text else 0.0
    semantic = 5.0 if skill_ratio < 0.3 else 8.0
    gpa_extra = (gpa / 4.0 * 1.5) if gpa > 0 else 0.0
    extra = min(gpa_extra + min(len(certs), 2) + min(len(projs), 3) * 0.5, 5.0)
    total = max(0.0, min(skill_score + semantic + exp_score + edu_score + extra, 100.0))

    return MatchResponse(
        match_score=round(total, 1),
        meets_threshold=total >= request.matching_threshold,
        matching_skills=sorted(matching),
        missing_skills=sorted(missing),
        experience_match=years_exp >= 1.0,
        gpa_match=gpa >= request.minimum_gpa,
        semantic_similarity=semantic,
        skill_score=round(skill_score, 1),
        experience_score=exp_score,
        education_score=edu_score,
        extra_score=round(extra, 1),
        recommendations=[f"Consider learning: {', '.join(missing[:3])}"] if missing else [],
        detailed_analysis=f"Basic: Skills {skill_score:.0f}/60 + Semantic {semantic:.0f}/10 + Exp {exp_score:.0f}/15 + Edu {edu_score:.0f}/10 + Extra {extra:.0f}/5",
    )
