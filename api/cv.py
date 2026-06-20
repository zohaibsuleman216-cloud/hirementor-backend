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
    cv_text: str
    job_title: str
    job_description: str
    required_skills: list[str] = []
    required_education: str = "Any"
    minimum_gpa: float = 0.0
    matching_threshold: float = DEFAULT_MATCH_THRESHOLD


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

    raise HTTPException(status_code=503, detail="CV parsing unavailable (NLP module not installed)")


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
                text = result.get("raw_text", "")
            finally:
                Path(tmp_path).unlink(missing_ok=True)
        else:
            raise HTTPException(status_code=400, detail="Unsupported file format")
    return parse_cv(CVParseRequest(text=text))


@router.post("/match", response_model=MatchResponse)
def match_cv_to_job(request: MatchRequest):
    cv_text = request.cv_text.strip()
    if not cv_text:
        raise HTTPException(status_code=400, detail="Empty CV text")

    if NLP_AVAILABLE and _semantic_matcher is not None:
        try:
            parser = SpacyNerParser()
            parsed = parser.parse_text(cv_text)
            cv_result = nlp_models.CVParseResult(
                candidate_name=parsed.candidate_name,
                email=parsed.email,
                phone=parsed.phone,
                skills=parsed.skills or extract_skills(cv_text),
                experience=parsed.experience or extract_experience(cv_text),
                education=parsed.education or extract_education(cv_text),
                gpa=extract_gpa(cv_text) or parsed.gpa,
                years_of_experience=estimate_years_of_experience(cv_text) or parsed.years_of_experience,
                certifications=extract_certifications(cv_text) or parsed.certifications,
                projects=extract_projects(cv_text) or parsed.projects,
                summary=parsed.summary,
            )
            job = nlp_models.Job(
                title=request.job_title,
                description=request.job_description,
                required_skills=request.required_skills,
                matching_threshold=request.matching_threshold,
            )

            result = _semantic_matcher.match_cv_to_job(cv_result, job)

            return MatchResponse(
                match_score=result.match_score,
                meets_threshold=result.meets_threshold,
                matching_skills=sorted(result.matching_skills),
                missing_skills=sorted(result.missing_skills),
                experience_match=result.experience_match,
                gpa_match=result.gpa_match,
                semantic_similarity=result.cosine_similarity * 10.0,
                skill_score=min(result.match_score, 60.0),
                experience_score=15.0 if result.experience_match else 0.0,
                education_score=10.0 if cv_result.education else 0.0,
                extra_score=5.0,
                recommendations=result.recommendations,
                detailed_analysis=result.detailed_analysis,
            )
        except Exception as e:
            logger.warning("SemanticMatcher failed: %s. Falling back to basic match.", e)

    required_skills_lower = {s.lower() for s in request.required_skills}
    candidate_skills_lower = {s.lower() for s in extract_skills(cv_text)}
    matching = list(candidate_skills_lower & required_skills_lower)
    missing = list(required_skills_lower - candidate_skills_lower)
    skill_ratio = len(matching) / len(required_skills_lower) if required_skills_lower else 0
    skill_score = skill_ratio * 60.0

    years_exp = estimate_years_of_experience(cv_text)
    exp_score = 15.0 if years_exp >= 5 else 12.0 if years_exp >= 2 else 8.0 if years_exp >= 1 else 4.0 if years_exp > 0 else 0.0

    edu_text = extract_education(cv_text).lower()
    edu_score = 10.0 if "phd" in edu_text else 8.0 if "master" in edu_text else 6.0 if "bachelor" in edu_text else 4.0 if edu_text else 0.0

    gpa = extract_gpa(cv_text)
    semantic = 5.0 if skill_ratio < 0.3 else 8.0
    gpa_extra = (gpa / 4.0 * 1.5) if gpa > 0 else 0.0
    extra = min(gpa_extra + min(len(extract_certifications(cv_text)), 2) + min(len(extract_projects(cv_text)), 3) * 0.5, 5.0)

    total = max(0.0, min(skill_score + semantic + exp_score + edu_score + extra, 100.0))
    recs = [f"Consider learning: {', '.join(sorted(missing)[:3])}"] if missing else []

    return MatchResponse(
        match_score=round(total, 1),
        meets_threshold=total >= request.matching_threshold,
        matching_skills=sorted(matching),
        missing_skills=sorted(missing),
        experience_match=years_exp >= 1.0,
        gpa_match=gpa >= 2.5,
        semantic_similarity=semantic,
        skill_score=round(skill_score, 1),
        experience_score=exp_score,
        education_score=edu_score,
        extra_score=round(extra, 1),
        recommendations=recs,
        detailed_analysis=(
            f"Basic: Skills {skill_score:.0f}/60 + Semantic {semantic:.0f}/10 + "
            f"Exp {exp_score:.0f}/15 + Edu {edu_score:.0f}/10 + Extra {extra:.0f}/5"
        ),
    )
