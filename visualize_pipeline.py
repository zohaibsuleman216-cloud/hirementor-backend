"""
SPB Backend Pipeline Visualization
====================================
Loads a CV from the Kaggle Resume dataset and shows step-by-step:
  1. Text extraction
  2. Entity extraction (regex / spaCy NER)
  3. BERT embeddings + cosine similarity
  4. Final match score (0-100)
  5. Shortlisting decision

Usage:
    python visualize_pipeline.py [--index N] [--category CAT]

    --index N         CV number from dataset (default: 0 = first one)
    --category CAT    Filter by category (IT, ENGINEERING, FINANCE, etc.)
                      Use --list-categories to see all
    --list-categories Show all available categories and exit
    
    Examples:
      python visualize_pipeline.py
      python visualize_pipeline.py --index 5
      python visualize_pipeline.py --category "INFORMATION-TECHNOLOGY" --index 2
      python visualize_pipeline.py --list-categories
"""

import os, sys, re, math, csv, argparse, random
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from spb_nlp.utils import (
    clean_text, extract_emails, extract_phones, extract_skills,
    extract_education, extract_experience, extract_name,
    estimate_years_of_experience, extract_gpa, extract_certifications,
    extract_projects, preprocess_for_embedding,
)

SEP = "=" * 72
SUB = "-" * 72

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(BASE_DIR, "Resume.csv")
DATA_DIR = os.path.join(BASE_DIR, "data", "data")


# ================================================================
# Load dataset
# ================================================================

def list_categories():
    cats = set()
    with open(CSV_PATH, encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader)  # skip header
        for row in reader:
            if len(row) >= 4:
                cats.add(row[3].strip().upper())
    for c in sorted(cats):
        print(f"  {c}")


def load_cv_from_dataset(category=None, index=0):
    """Load a CV from the dataset. Returns (text, category, resume_id)."""
    candidates = []
    with open(CSV_PATH, encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader)
        for row in reader:
            if len(row) < 4:
                continue
            rid, text, html, cat = row[0], row[1], row[2], row[3].strip().upper()
            if category and cat != category.upper():
                continue
            candidates.append((rid, text, cat))

    if not candidates:
        print(f"  No CVs found" + (f" in category '{category}'" if category else ""))
        sys.exit(1)

    rid, text, cat = candidates[index % len(candidates)]
    print(f"  Loaded CV #{rid} | Category: {cat} | {len(text)} chars")
    return text, cat, rid


# ================================================================
# Jobs matching
# ================================================================

DATASET_JOBS = {
    "INFORMATION-TECHNOLOGY": {
        "title": "Software Engineer",
        "company": "TechCorp",
        "description": "Develop and maintain software applications using modern frameworks and cloud technologies.",
        "required_skills": ["python", "java", "javascript", "react", "django", "aws", "docker", "sql", "git", "typescript"],
        "requirements": ["BS in CS or related", "3+ years experience", "Agile methodology"],
        "qualifications": ["Problem-solving", "Team collaboration", "Communication"],
        "matching_threshold": 50.0,
        "minimum_gpa": 2.5,
        "required_education": "Bachelor",
    },
    "ENGINEERING": {
        "title": "Mechanical Engineer",
        "company": "BuildCorp",
        "description": "Design and analyze mechanical systems, CAD modeling, and project management.",
        "required_skills": ["autocad", "solidworks", "matlab", "python", "project management", "excel", "simulation"],
        "requirements": ["BS in Mechanical Engineering", "2+ years experience", "PE license preferred"],
        "qualifications": ["Analytical", "Detail-oriented", "CAD proficiency"],
        "matching_threshold": 45.0,
        "minimum_gpa": 2.5,
        "required_education": "Bachelor",
    },
    "FINANCE": {
        "title": "Financial Analyst",
        "company": "FinanceHub",
        "description": "Analyze financial data, create models, and support investment decisions.",
        "required_skills": ["excel", "python", "sql", "financial modeling", "data analysis", "tableau", "accounting"],
        "requirements": ["BS in Finance or Economics", "CFA preferred", "2+ years experience"],
        "qualifications": ["Analytical", "Detail-oriented", "Communication"],
        "matching_threshold": 50.0,
        "minimum_gpa": 3.0,
        "required_education": "Bachelor",
    },
    "HEALTHCARE": {
        "title": "Healthcare Administrator",
        "company": "MediCare Group",
        "description": "Manage healthcare facility operations, compliance, and patient services.",
        "required_skills": ["healthcare management", "communication", "project management", "data analysis", "leadership", "excel"],
        "requirements": ["BS in Healthcare Administration", "3+ years experience", "HIPAA knowledge"],
        "qualifications": ["Leadership", "Organizational", "Empathy"],
        "matching_threshold": 45.0,
        "minimum_gpa": 2.5,
        "required_education": "Bachelor",
    },
    "SALES": {
        "title": "Sales Manager",
        "company": "SalesPro Inc.",
        "description": "Lead sales team, develop strategies, and drive revenue growth.",
        "required_skills": ["communication", "leadership", "negotiation", "crm", "excel", "presentation", "marketing"],
        "requirements": ["BS in Business or Marketing", "3+ years sales experience", "CRM expertise"],
        "qualifications": ["Persuasive", "Goal-oriented", "Team player"],
        "matching_threshold": 40.0,
        "minimum_gpa": 2.0,
        "required_education": "Bachelor",
    },
    "HR": {
        "title": "HR Manager",
        "company": "PeopleFirst",
        "description": "Oversee recruitment, employee relations, compliance, and organizational development.",
        "required_skills": ["communication", "recruitment", "leadership", "hr policies", "conflict resolution", "excel", "interviewing"],
        "requirements": ["BS in HR or Psychology", "3+ years experience", "SHRM certification preferred"],
        "qualifications": ["Interpersonal", "Organizational", "Ethical judgment"],
        "matching_threshold": 40.0,
        "minimum_gpa": 2.5,
        "required_education": "Bachelor",
    },
    "DESIGNER": {
        "title": "UI/UX Designer",
        "company": "DesignStudio",
        "description": "Create user-centered designs for web and mobile applications.",
        "required_skills": ["figma", "ui/ux", "photoshop", "illustrator", "html", "css", "javascript", "prototyping"],
        "requirements": ["BS in Design or related", "2+ years experience", "Portfolio required"],
        "qualifications": ["Creative", "User-centric", "Detail-oriented"],
        "matching_threshold": 40.0,
        "minimum_gpa": 2.5,
        "required_education": "Bachelor",
    },
    "TEACHER": {
        "title": "High School Teacher",
        "company": "EduStar Academy",
        "description": "Teach and mentor students, develop lesson plans, and assess learning outcomes.",
        "required_skills": ["communication", "lesson planning", "classroom management", "curriculum development", "leadership", "public speaking"],
        "requirements": ["BS in Education or subject area", "Teaching certification", "1+ year experience"],
        "qualifications": ["Patient", "Inspirational", "Organized"],
        "matching_threshold": 40.0,
        "minimum_gpa": 2.5,
        "required_education": "Bachelor",
    },
    "ACCOUNTANT": {
        "title": "Accountant",
        "company": "AuditFirst",
        "description": "Manage financial records, prepare tax returns, and ensure compliance.",
        "required_skills": ["accounting", "excel", "quickbooks", "tax preparation", "financial reporting", "auditing", "data analysis"],
        "requirements": ["BS in Accounting", "CPA preferred", "2+ years experience"],
        "qualifications": ["Analytical", "Ethical", "Detail-oriented"],
        "matching_threshold": 50.0,
        "minimum_gpa": 3.0,
        "required_education": "Bachelor",
    },
}


def print_step(num, title, content, indent=2):
    pad = " " * indent
    print(f"\n{SUB}")
    print(f"  >>> STEP {num}: {title}")
    print(f"{SUB}")
    if isinstance(content, (list, tuple)):
        for item in content:
            print(f"{pad}  - {item}")
    elif isinstance(content, dict):
        for k, v in content.items():
            print(f"{pad}{k}: {v}")
    else:
        for line in str(content).split("\n"):
            print(f"{pad}{line}")


# ================================================================
# STEP 1: Text display
# ================================================================

def step1_display(cv_text):
    print(f"\n{SEP}")
    print("  PHASE 1: RAW CV TEXT")
    print(f"{SEP}")
    text = clean_text(cv_text)
    lines = text.strip().split("\n")
    # Show first 30 lines
    show = lines[:30]
    print(f"  Total: {len(text)} chars, {len(lines)} lines (showing first 30):")
    print(f"  {'='*50}")
    for line in show:
        print(f"    | {line[:100]}")
    if len(lines) > 30:
        print(f"    | ... ({len(lines)-30} more lines)")
    print(f"  {'='*50}")
    return text


# ================================================================
# STEP 2: Entity extraction
# ================================================================

def step2_entities(cleaned_text):
    print(f"\n{SEP}")
    print("  PHASE 2: ENTITY EXTRACTION (Regex + optional spaCy NER)")
    print(f"{SEP}")

    spacy_active = False
    doc = None
    try:
        import spacy
        nlp = spacy.load("en_core_web_lg")
        doc = nlp(cleaned_text[:100000])
        spacy_active = True
        print("  spaCy NER: ACTIVE (en_core_web_lg)")
    except ImportError:
        print("  spaCy: NOT INSTALLED -> using regex fallback")
    except OSError:
        print("  spaCy model not found -> using regex fallback")

    result = {}

    # --- Name ---
    name = ""
    if spacy_active and doc:
        for ent in doc.ents:
            if ent.label_ == "PERSON" and len(ent.text.split()) in [2, 3, 4]:
                name = ent.text.strip()
                break
    if not name:
        name = extract_name(cleaned_text)
    result["name"] = name
    method = "spaCy NER" if spacy_active and name == (doc and [e.text.strip() for e in doc.ents if e.label_ == "PERSON" and len(e.text.split()) in [2,3,4]][0] if doc and [e for e in doc.ents if e.label_ == "PERSON"] else "") else "Regex"
    print(f"\n  2a. Candidate Name:")
    print(f"       Method: {'spaCy NER' if spacy_active and name else 'Regex (first line)'}")
    print(f"       Value:  {name or '(not found)'}")

    # --- Contact ---
    emails = extract_emails(cleaned_text)
    phones = extract_phones(cleaned_text)
    result["email"] = emails[0] if emails else ""
    result["phone"] = phones[0] if phones else ""
    print(f"\n  2b. Contact:")
    print(f"       Email: {emails[0] if emails else '(not found)'}")
    if len(emails) > 1:
        print(f"       More: {', '.join(emails[1:])}")
    print(f"       Phone: {phones[0] if phones else '(not found)'}")

    # --- Skills ---
    skills = extract_skills(cleaned_text)
    result["skills"] = skills
    print(f"\n  2c. Skills ({len(skills)} found):")
    print(f"       Method: Regex keyword matching (dict of {len(skills)} skills)")
    print(f"       Skills: {', '.join(skills[:15])}")
    if len(skills) > 15:
        print(f"       ... and {len(skills)-15} more")
    print(f"\n  Matching details (sample):")
    for skill in skills[:6]:
        pattern = re.compile(r'(?<!\w)' + re.escape(skill) + r'(?!\w)', re.I)
        for line in cleaned_text.split("\n"):
            if pattern.search(line):
                truncated = line.strip()[:90]
                print(f"       [{skill:20s}] <- \"{truncated}\"")
                break

    # --- Education ---
    education = extract_education(cleaned_text)
    result["education"] = education
    print(f"\n  2d. Education:")
    print(f"       Method: Section-based extraction")
    print(f"       Text: {education[:300] if education else '(not found)'}")

    # --- Experience ---
    experience = extract_experience(cleaned_text)
    years_exp = estimate_years_of_experience(cleaned_text)
    result["experience"] = experience
    result["years_of_experience"] = years_exp
    print(f"\n  2e. Experience:")
    print(f"       Method: Section parsing + date range fallback")
    print(f"       Estimated years: {years_exp}")
    print(f"       Text: {experience[:300] if experience else '(not found - using year-range)'}")
    print(f"\n  Experience estimation:")
    exp_patterns = [
        r'(\d+)\+?\s*years?\s*(?:of\s+)?experience',
        r'experience\s*(?:of\s+)?(\d+)\+?\s*years?',
    ]
    for p in exp_patterns:
        matches = re.findall(p, cleaned_text.lower())
        if matches:
            print(f"       Direct mention: {matches}")
    all_years = set()
    for line in cleaned_text.split("\n"):
        found = re.findall(r'\b(19[5-9]\d|20[0-2]\d)\b', line)
        for y in found:
            all_years.add(int(y))
    if len(all_years) >= 2:
        print(f"       Year range: {min(all_years)}-{max(all_years)} = {max(all_years)-min(all_years)} yrs")

    # --- GPA ---
    gpa = extract_gpa(cleaned_text)
    result["gpa"] = gpa
    print(f"\n  2f. GPA:")
    print(f"       Method: Regex pattern matching")
    print(f"       Value:  {gpa}")
    gpa_patterns = [
        r'(?:gpa|cgpa|g\.p\.a\.)\s*:?\s*(\d+\.?\d*)',
        r'(\d+\.\d+)\s*/\s*4\.?0',
        r'(\d+\.\d+)\s*out\s*of\s*4',
    ]
    for i, p in enumerate(gpa_patterns):
        m = re.findall(p, cleaned_text.lower())
        if m:
            val = float(m[0])
            print(f"       Pattern {i+1} matched: {m[0]}")

    # --- Certifications ---
    certs = extract_certifications(cleaned_text)
    result["certifications"] = certs
    print(f"\n  2g. Certifications ({len(certs)} found):")
    for c in certs:
        print(f"       - {c}")
    if not certs:
        print(f"       (none)")

    # --- Projects ---
    projects = extract_projects(cleaned_text)
    result["projects"] = projects
    print(f"\n  2h. Projects ({len(projects)} found):")
    for p in projects:
        print(f"       - {p}")
    if not projects:
        print(f"       (none)")

    return result


# ================================================================
# STEP 3: Semantic matching (BERT / fallback)
# ================================================================

def step3_semantic(cv_data, job_data):
    print(f"\n{SEP}")
    print("  PHASE 3: SEMANTIC MATCHING (BERT embeddings + Cosine Similarity)")
    print(f"{SEP}")

    cv_text = preprocess_for_embedding(" ".join([
        f"Skills: {', '.join(cv_data['skills'])}",
        f"Experience: {cv_data['experience'][:500]}",
        f"Education: {cv_data['education'][:300]}",
        f"Certifications: {', '.join(cv_data['certifications'])}",
        f"Projects: {', '.join(cv_data['projects'])}",
    ]))
    job_text = preprocess_for_embedding(" ".join([
        f"Title: {job_data['title']}",
        f"Description: {job_data['description']}",
        f"Required Skills: {', '.join(job_data['required_skills'])}",
        f"Requirements: {', '.join(job_data['requirements'])}",
        f"Qualifications: {', '.join(job_data['qualifications'])}",
    ]))

    print(f"\n  3a. Input text for embedding:")
    print(f"       CV:  {cv_text[:150]}...")
    print(f"       Job: {job_text[:150]}...")

    using_bert = False
    try:
        from sentence_transformers import SentenceTransformer
        import numpy as np
        from sklearn.metrics.pairwise import cosine_similarity
        print(f"\n  3b. Loading BERT: all-MiniLM-L6-v2 ...")
        model = SentenceTransformer("all-MiniLM-L6-v2")
        emb_cv = model.encode([cv_text], normalize_embeddings=True)
        emb_job = model.encode([job_text], normalize_embeddings=True)
        cos_sim = float(cosine_similarity(emb_cv, emb_job)[0][0])
        cos_sim = max(0.0, min(1.0, cos_sim))
        using_bert = True
        print(f"  Embedding dim: {emb_cv.shape[1]}")
        print(f"\n  3c. Cosine Similarity = {cos_sim:.4f}")
    except ImportError as e:
        print(f"\n  3b. BERT: NOT AVAILABLE ({e})")
        print(f"       -> Using n-gram fallback")
        def _ngrams(t, n):
            d = {}
            for i in range(len(t) - n + 1):
                gram = t[i:i+n]
                d[gram] = d.get(gram, 0) + 1
            return d
        def _cosine(d1, d2):
            dot = n1 = n2 = 0.0
            for k, v in d1.items():
                n1 += v * v
                if k in d2:
                    dot += v * d2[k]
            for v in d2.values():
                n2 += v * v
            if n1 == 0 or n2 == 0:
                return 0.0
            return dot / (math.sqrt(n1) * math.sqrt(n2))
        bi_cv, bi_job = _ngrams(cv_text.lower(), 2), _ngrams(job_text.lower(), 2)
        tri_cv, tri_job = _ngrams(cv_text.lower(), 3), _ngrams(job_text.lower(), 3)
        bigram_sim = _cosine(bi_cv, bi_job)
        trigram_sim = _cosine(tri_cv, tri_job)
        cos_sim = bigram_sim * 0.4 + trigram_sim * 0.6
        shared_bi = set(bi_cv.keys()) & set(bi_job.keys())
        print(f"\n  3c. n-gram similarity:")
        print(f"       Bigram:  {bigram_sim:.4f} ({len(shared_bi)} shared / {len(bi_cv)+len(bi_job)} total)")
        print(f"       Trigram: {trigram_sim:.4f}")
        print(f"       Weighted (40/60): {cos_sim:.4f}")
        top = sorted(shared_bi, key=lambda g: min(bi_cv.get(g,0), bi_job.get(g,0)), reverse=True)[:10]
        print(f"       Top bigrams: {top}")

    return cos_sim, using_bert


# ================================================================
# STEP 4: Score calculation
# ================================================================

def step4_score(cv_data, job_data, cos_sim):
    print(f"\n{SEP}")
    print("  PHASE 4: FINAL MATCH SCORE (composite 0-100)")
    print(f"{SEP}")
    print("""  Weights:
    Skills overlap:  60 pts  (60%)  <- dominant
    Semantic (BERT):  10 pts  (10%)
    Experience:       15 pts  (15%)
    Education:        10 pts  (10%)
    Extra (GPA/cert/proj):  5 pts (5%)
                           -----
                   Total: 100 pts
  """)

    cv_skills = {s.lower().strip() for s in cv_data["skills"]}
    job_skills = {s.lower().strip() for s in job_data["required_skills"]}
    matching = list(cv_skills & job_skills)
    missing = list(job_skills - cv_skills)
    skill_ratio = len(matching) / len(job_skills) if job_skills else 0.0
    skill_score = skill_ratio * 60.0

    print(f"\n  4a. Skills ({len(matching)}/{len(job_skills)} match):")
    print(f"       Matching: {', '.join(matching[:10]) or '-none-'}")
    print(f"       Missing:  {', '.join(missing[:10]) or '-none-'}")
    print(f"       Score: {skill_score:.1f}/60")

    bert_score = cos_sim * 10.0
    if skill_ratio < 0.3 and cos_sim > 0.3:
        bert_score *= 0.4
        print(f"\n  4b. Semantic: {bert_score:.1f}/10 (cos={cos_sim:.3f}, penalty applied)")
    else:
        print(f"\n  4b. Semantic: {bert_score:.1f}/10 (cos={cos_sim:.3f})")

    yr = cv_data["years_of_experience"]
    if yr >= 5.0:
        exp_score = 15.0
    elif yr >= 2.0:
        exp_score = 12.0
    elif yr >= 1.0:
        exp_score = 8.0
    elif yr > 0:
        exp_score = 4.0
    else:
        exp_score = 0.0
    print(f"\n  4c. Experience ({yr:.1f} yrs): {exp_score:.1f}/15")

    edu_text = cv_data.get("education", "").lower()
    if "phd" in edu_text or "doctorate" in edu_text:
        edu_score = 10.0
    elif "master" in edu_text or "m.s." in edu_text:
        edu_score = 8.0
    elif "bachelor" in edu_text or "b.s." in edu_text or "b.tech" in edu_text:
        edu_score = 6.0
    elif edu_text:
        edu_score = 4.0
    else:
        edu_score = 0.0
    print(f"\n  4d. Education: {edu_score:.1f}/10")

    gpa = cv_data["gpa"]
    gpa_bonus = 1.5 if gpa >= 3.5 else (1.0 if gpa >= 2.5 else 0.0)
    cert_bonus = min(len(cv_data["certifications"]) * 1.0, 2.0)
    proj_bonus = min(len(cv_data["projects"]) * 0.5, 1.5)
    extra = gpa_bonus + cert_bonus + proj_bonus
    print(f"\n  4e. Extra: {extra:.1f}/5")
    print(f"       GPA ({gpa}): {gpa_bonus:.1f}")
    print(f"       Certs ({len(cv_data['certifications'])}): {cert_bonus:.1f}")
    print(f"       Projects ({len(cv_data['projects'])}): {proj_bonus:.1f}")

    total = min(max(skill_score + bert_score + exp_score + edu_score + extra, 0.0), 100.0)

    print(f"\n  {'='*50}")
    print(f"   >>> FINAL MATCH SCORE: {total:.1f} / 100")
    print(f"  {'='*50}")
    print(f"\n  Breakdown:")
    items = [("Skills", skill_score, 60), ("BERT", bert_score, 10),
             ("Experience", exp_score, 15), ("Education", edu_score, 10),
             ("Extra", extra, 5)]
    for label, got, max_ in items:
        bar = "#" * int(got / max_ * 20) if max_ > 0 else ""
        print(f"    {label:12s} {got:5.1f}/{max_:<3.0f} {bar}")

    threshold = job_data.get("matching_threshold", 50.0)
    meets = total >= threshold
    print(f"\n  4f. Threshold: {threshold:.0f}% -> {'PASS [OK]' if meets else 'FAIL'}")
    print(f"\n  4g. Recommendations:")
    recs = []
    if missing:
        recs.append(f"Learn: {', '.join(missing[:3])}")
    if not cv_data["certifications"]:
        recs.append("Add certifications")
    if 0 < gpa < 2.5:
        recs.append(f"GPA below 2.5")
    if cos_sim < 0.3 and skill_ratio < 0.3:
        recs.append("Upskilling needed")
    if not recs:
        recs.append("Strong candidate!")
    for r in recs:
        print(f"       - {r}")

    return total, meets, matching, missing


# ================================================================
# STEP 5: Decision
# ================================================================

def step5_decision(total, meets, cv_data, job_data, matching, missing):
    print(f"\n{SEP}")
    print("  PHASE 5: SHORTLISTING DECISION")
    print(f"{SEP}")
    
    name = cv_data.get("name") or "(not found)"
    print(f"\n  Candidate: {name}")
    print(f"  Job:       {job_data['title']} @ {job_data['company']}")
    print(f"\n  {'='*50}")
    print(f"  VERDICT: {'SHORTLISTED [OK]' if meets else 'REJECTED'}")
    print(f"  {'='*50}")

    if meets:
        print(f"\n  [OK] Score {total:.1f}% >= {job_data['matching_threshold']}%")
        print(f"  [OK] Matching: {', '.join(matching[:5])}")
        print(f"  [OK] Application saved to Firestore")
    else:
        print(f"\n  [FAIL] Score {total:.1f}% < {job_data['matching_threshold']}%")
        if missing:
            print(f"  [FAIL] Missing skills: {', '.join(missing[:3])}")
        if cv_data["gpa"] > 0 and cv_data["gpa"] < job_data.get("minimum_gpa", 0):
            print(f"  [FAIL] GPA {cv_data['gpa']} < min {job_data['minimum_gpa']}")
        print(f"\n  -> Application NOT saved. Student sees rejection toast.")


# ================================================================
# MAIN
# ================================================================

def main():
    parser = argparse.ArgumentParser(description="Visualize SPB backend pipeline with dataset CVs")
    parser.add_argument("--index", type=int, default=0, help="CV index in dataset (default: 0)")
    parser.add_argument("--category", type=str, default=None, help="Filter by category")
    parser.add_argument("--list-categories", action="store_true", help="Show all categories")
    parser.add_argument("--random", action="store_true", help="Pick random CV")
    args = parser.parse_args()

    print(f"\n{SEP}")
    print("  SPB BACKEND PIPELINE - STEP BY STEP")
    print("  HireMentor CV Parsing + Semantic Matching")
    print(f"{SEP}")

    if args.list_categories:
        print("\n  Available categories:\n")
        list_categories()
        print()
        return

    # Load CV
    if args.random:
        idx = random.randint(0, 999)
    else:
        idx = args.index

    cv_text, category, cv_id = load_cv_from_dataset(args.category, idx)

    # Pick job based on category
    if category in DATASET_JOBS:
        job_data = DATASET_JOBS[category]
    else:
        job_data = DATASET_JOBS["INFORMATION-TECHNOLOGY"]
        print(f"  (No specific job for {category}, using IT job)")

    print(f"  Matching Job: {job_data['title']} @ {job_data['company']}")
    print(f"  Required skills: {', '.join(job_data['required_skills'])}")

    # Run pipeline
    cleaned = step1_display(cv_text)
    cv_data = step2_entities(cleaned)
    cos_sim, using_bert = step3_semantic(cv_data, job_data)
    total, meets, matching, missing = step4_score(cv_data, job_data, cos_sim)
    step5_decision(total, meets, cv_data, job_data, matching, missing)

    print(f"\n{SEP}")
    print("  DONE. Pipeline complete.")
    print(f"{SEP}")
    print(f"  Dataset: Resume.csv | CV #{cv_id} | Category: {category}")
    print(f"  BERT: {'[OK]' if using_bert else '[NOT INSTALLED, fallback used]'}")
    print(f"  To get full BERT: pip install sentence-transformers")
    print()


if __name__ == "__main__":
    main()
