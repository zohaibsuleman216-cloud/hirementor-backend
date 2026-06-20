"""
Match Score Comparison Table
Demonstrates how the Android app's CV-matching algorithm scores different
candidates for the SAME job posting (Backend Developer).

Formula (UNIFIED with Python backend as of 2026-06-06):
  Skills Overlap:   60%  (matched / required * 60)
  Semantic Match:   10%  (8 normally, 5 if skill_ratio < 0.3 to penalize domain mismatch)
  Experience:       15%  (>=5yr=15, >=2yr=12, >=1yr=8, >0=4, none=0)
  Education:        10%  (PhD=10, Master=8, Bachelor=6, Other=4, none=0)
  Extra:             5%  (GPA 0-1.5 + Certs 0-2 + Projects 0-1.5)
  Total:             0-100

Threshold default: 50% (set by company per job)
"""

JOB = {
    "title": "Backend Developer",
    "required_skills": ["python", "django", "postgresql", "docker", "aws"],
    "min_experience_years": 3,
    "min_education": "Bachelor",
}

THRESHOLD = 50  # Company-set threshold for this job


def score_candidate(name, skills, exp_years, education, gpa, projects, certs, scenario=""):
    job_skills = JOB["required_skills"]
    skills_lower = [s.lower() for s in skills]
    matched = [s for s in job_skills if s in skills_lower]
    missing = [s for s in job_skills if s not in skills_lower]

    # 1. Skill Overlap (60 max)
    skill_score = (len(matched) / len(job_skills)) * 60.0

    # 2. Semantic Match (10 max) - cap at 5/10 if low skill overlap
    skill_ratio = len(matched) / len(job_skills) if job_skills else 0.0
    semantic_score = 5.0 if skill_ratio < 0.3 else 8.0

    # 3. Experience (15 max)
    if exp_years >= 5:
        exp_score = 15.0
    elif exp_years >= 2:
        exp_score = 12.0
    elif exp_years >= 1:
        exp_score = 8.0
    elif exp_years > 0:
        exp_score = 4.0
    else:
        exp_score = 0.0

    # 4. Education (10 max)
    edu_lower = education.lower() if education else ""
    if "phd" in edu_lower or "doctorate" in edu_lower:
        edu_score = 10.0
    elif "master" in edu_lower or "msc" in edu_lower or "m.s." in edu_lower:
        edu_score = 8.0
    elif "bachelor" in edu_lower or "bs" in edu_lower or "b.s." in edu_lower:
        edu_score = 6.0
    elif education:
        edu_score = 4.0
    else:
        edu_score = 0.0

    # 5. Extra (5 max): GPA + Certs + Projects
    gpa_score = (gpa / 4.0 * 1.5) if gpa > 0 else 0.0
    gpa_score = min(gpa_score, 1.5)
    cert_score = min(len(certs), 2)
    proj_score = min(len(projects), 3) * 0.5
    extra_score = min(gpa_score + cert_score + proj_score, 5.0)

    total = skill_score + semantic_score + exp_score + edu_score + extra_score
    total = min(total, 100.0)

    return {
        "name": name,
        "scenario": scenario,
        "matched": matched,
        "missing": missing,
        "skill_score": skill_score,
        "semantic_score": semantic_score,
        "exp_score": exp_score,
        "edu_score": edu_score,
        "extra_score": extra_score,
        "total": total,
        "passes": total >= THRESHOLD,
    }


candidates = [
    {
        "name": "Ali (Perfect Match)",
        "scenario": "Backend developer with full Python stack + projects + certs",
        "skills": ["python", "django", "postgresql", "docker", "aws", "redis", "git"],
        "exp_years": 4,
        "education": "Bachelor",
        "gpa": 3.6,
        "projects": ["E-commerce API", "Payment Gateway", "Auth Service"],
        "certs": ["AWS Certified Developer"],
    },
    {
        "name": "Sara (Python Only - basic)",
        "scenario": "Python developer with limited other skills",
        "skills": ["python", "flask", "mysql"],
        "exp_years": 2,
        "education": "Bachelor",
        "gpa": 3.2,
        "projects": ["Personal blog"],
        "certs": [],
    },
    {
        "name": "Ahmed (Strong Adjacent)",
        "scenario": "Python + 2 missing skills but lots of experience and projects",
        "skills": ["python", "django", "postgresql", "redis", "git", "linux"],
        "exp_years": 5,
        "education": "Master",
        "gpa": 3.8,
        "projects": ["Banking API", "Healthcare System", "ML Pipeline", "Chat Service"],
        "certs": ["AWS Certified", "Google Cloud Associate"],
    },
    {
        "name": "Bilal (Wrong Domain)",
        "scenario": "Java developer - no Python at all",
        "skills": ["java", "spring", "mysql", "kubernetes", "jenkins"],
        "exp_years": 4,
        "education": "Bachelor",
        "gpa": 3.4,
        "projects": ["Banking System"],
        "certs": [],
    },
    {
        "name": "Hina (Junior Python)",
        "scenario": "Fresh Python graduate with 0 experience",
        "skills": ["python", "django"],
        "exp_years": 0,
        "education": "Bachelor",
        "gpa": 3.5,
        "projects": ["University project"],
        "certs": [],
    },
]


print("=" * 110)
print(f"JOB: {JOB['title']}  |  Required: {JOB['required_skills']}  |  Threshold: {THRESHOLD}%")
print("=" * 110)

for c in candidates:
    s = score_candidate(c["name"], c["skills"], c["exp_years"], c["education"],
                         c["gpa"], c["projects"], c["certs"], c["scenario"])
    status = "PASS" if s["passes"] else "FAIL"
    print(f"\n[{status}] {s['name']}  -  Total: {s['total']:.1f}%")
    print(f"   Scenario: {s['scenario']}")
    print(f"   Matched skills: {s['matched']}  |  Missing: {s['missing']}")
    print(f"   Skills: {s['skill_score']:.1f}/60  |  Semantic: {s['semantic_score']:.1f}/10  |  "
          f"Exp: {s['exp_score']:.1f}/15  |  Edu: {s['edu_score']:.1f}/10  |  "
          f"Extra: {s['extra_score']:.1f}/5")

print("\n" + "=" * 110)
print("SUMMARY TABLE")
print("=" * 110)
print(f"{'Candidate':<25} {'Score':<8} {'Status':<8} {'Matched':<8} {'Missing Skills'}")
print("-" * 110)
for c in candidates:
    s = score_candidate(c["name"], c["skills"], c["exp_years"], c["education"],
                         c["gpa"], c["projects"], c["certs"])
    status = "PASS" if s["passes"] else "FAIL"
    print(f"{s['name']:<25} {s['total']:>5.1f}%  {status:<8} {len(s['matched'])}/{len(JOB['required_skills'])}     "
          f"{', '.join(s['missing'])}")
