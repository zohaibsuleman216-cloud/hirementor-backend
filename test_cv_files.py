"""
Test CV files (PDF ya text) against HireMentor parser.
Put your CV files in data/test_cvs/ folder.

Usage:
    python test_cv_files.py
"""

import sys, os, glob
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from spb_nlp.cv_parser import CVParser, SpacyNerParser
from spb_nlp.semantic_matcher import SemanticMatcher
from spb_nlp.models import Job

CV_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "test_cvs")

SAMPLE_JOBS = [
    Job(job_id="j1", title="Android Developer",
        company_name="TechCorp",
        description="Build Android apps with Kotlin and Jetpack Compose",
        required_skills=["kotlin", "android", "jetpack compose", "firebase", "git"],
        matching_threshold=40.0),
    Job(job_id="j2", title="Python Backend Developer",
        company_name="DataAI",
        description="Develop Python microservices with Django",
        required_skills=["python", "django", "postgresql", "docker", "aws"],
        matching_threshold=40.0),
    Job(job_id="j3", title="Data Scientist",
        company_name="ML Solutions",
        description="ML and NLP solutions using Python",
        required_skills=["python", "machine learning", "tensorflow", "sql", "nlp"],
        matching_threshold=50.0),
]

def main():
    if not os.path.isdir(CV_FOLDER):
        print(f"\n❌ Folder nahi mila: {CV_FOLDER}")
        print("   Isme CV files (PDF ya .txt) rakhein.\n")
        os.makedirs(CV_FOLDER, exist_ok=True)
        print(f"✅ Folder bana diya: {CV_FOLDER}")
        print("   Ab apne CV files wahan copy karein aur dobara run karein.\n")
        return

    files = []
    for ext in ("*.pdf", "*.txt", "*.doc", "*.docx"):
        files.extend(glob.glob(os.path.join(CV_FOLDER, ext)))

    if not files:
        print(f"\n❌ {CV_FOLDER} mein koi PDF ya TXT file nahi mili.")
        print("   Wahan apni CV files copy karein aur dobara run karein.\n")
        return

    parser = CVParser()
    spacy_parser = SpacyNerParser()
    matcher = SemanticMatcher()

    print(f"\n{'='*70}")
    print(f"  Testing {len(files)} CV file(s) in: {CV_FOLDER}")
    print(f"  Model: spaCy NER={'✓' if spacy_parser.is_using_spacy else '✗ (fallback)'}"
          f" | BERT={'✓' if matcher.using_bert else '✗ (fallback)'}")
    print(f"{'='*70}")

    for fpath in sorted(files):
        fname = os.path.basename(fpath)
        print(f"\n{'─'*70}")
        print(f"  FILE: {fname}")
        print(f"{'─'*70}")

        try:
            if fname.lower().endswith(".pdf"):
                cv = parser.parse_pdf(fpath)
            else:
                with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                    cv = parser.parse_text(f.read())

            print(f"  Name:       {cv.candidate_name or '❌ Not found'}")
            print(f"  Email:      {cv.email or '❌ Not found'}")
            print(f"  Phone:      {cv.phone or '❌ Not found'}")
            print(f"  Skills:     {', '.join(cv.skills[:10]) or '❌ None'}")
            print(f"  Education:  {cv.education[:80] or '❌ None'}")
            print(f"  GPA:        {cv.gpa if cv.gpa > 0 else '❌ Not found'}")
            print(f"  Experience: {cv.years_of_experience:.1f} years")
            print(f"  Certs:      {', '.join(cv.certifications[:5]) or 'None'}")
            print(f"  Projects:   {', '.join(cv.projects[:3]) or 'None'}")

            print(f"\n  ── Job Matching Results ──")
            for job in SAMPLE_JOBS:
                match = matcher.match_cv_to_job(cv, job)
                status = "✅ SHORTLISTED" if match.meets_threshold else "❌ REJECTED"
                print(f"  {job.title:30s} Score: {match.match_score:5.1f}  {status}")
                if match.matching_skills:
                    print(f"  {'':30s}  ✓ {', '.join(match.matching_skills[:4])}")
                if match.missing_skills:
                    print(f"  {'':30s}  ✗ Missing: {', '.join(match.missing_skills[:4])}")

        except Exception as e:
            print(f"  ❌ Error: {e}")

    print(f"\n{'='*70}")
    print("  Done!")
    print(f"{'='*70}\n")

if __name__ == "__main__":
    main()
