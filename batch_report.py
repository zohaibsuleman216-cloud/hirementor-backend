"""
Batch Report - Process 100+ CVs from dataset and show summary statistics.
Supervisor ko dikhane ke liye ke pipeline kesay kaam karta hai.

Usage:
    python batch_report.py [--count N] [--category CAT] [--threshold T]

    --count N         Kitne CV process karne hain (default: 100)
    --category CAT    Sirf ek category (e.g., INFORMATION-TECHNOLOGY)
    --threshold T     Matching threshold percentage (default: 50)
    --output FILE     Results CSV file save karne ke liye

Examples:
    python batch_report.py
    python batch_report.py --category INFORMATION-TECHNOLOGY --count 50
    python batch_report.py --count 200 --output results.csv
"""

import os, sys, re, math, csv, argparse, random, time
from statistics import mean, median, stdev
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from spb_nlp.utils import (
    clean_text, extract_emails, extract_phones, extract_skills,
    extract_education, extract_experience, extract_name,
    estimate_years_of_experience, extract_gpa, extract_certifications,
    extract_projects, preprocess_for_embedding,
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(BASE_DIR, "Resume.csv")

SEP = "=" * 72

DATASET_JOBS = {
    "INFORMATION-TECHNOLOGY": {
        "title": "Software Engineer",
        "company": "TechCorp",
        "description": "Develop and maintain software applications using modern frameworks.",
        "required_skills": ["python", "java", "javascript", "react", "django", "aws", "docker", "sql", "git", "typescript"],
        "requirements": ["BS in CS", "3+ years"],
        "qualifications": ["Problem-solving", "Teamwork"],
        "matching_threshold": 50.0,
        "minimum_gpa": 2.5,
        "required_education": "Bachelor",
    },
    "ENGINEERING": {
        "title": "Mechanical Engineer",
        "company": "BuildCorp",
        "description": "Design and analyze mechanical systems.",
        "required_skills": ["autocad", "solidworks", "matlab", "python", "project management", "excel", "simulation"],
        "requirements": ["BS in ME", "2+ years"],
        "qualifications": ["Analytical", "CAD"],
        "matching_threshold": 45.0,
        "minimum_gpa": 2.5,
        "required_education": "Bachelor",
    },
    "FINANCE": {
        "title": "Financial Analyst",
        "company": "FinanceHub",
        "description": "Analyze financial data and create models.",
        "required_skills": ["excel", "python", "sql", "financial modeling", "data analysis", "tableau", "accounting"],
        "requirements": ["BS in Finance", "CFA pref."],
        "qualifications": ["Analytical", "Detail-oriented"],
        "matching_threshold": 50.0,
        "minimum_gpa": 3.0,
        "required_education": "Bachelor",
    },
    "HEALTHCARE": {
        "title": "Healthcare Admin",
        "company": "MediCare",
        "description": "Manage healthcare facility operations.",
        "required_skills": ["healthcare management", "communication", "project management", "data analysis", "leadership", "excel"],
        "requirements": ["BS in HCA", "3+ years"],
        "qualifications": ["Leadership", "Organizational"],
        "matching_threshold": 45.0,
        "minimum_gpa": 2.5,
        "required_education": "Bachelor",
    },
    "SALES": {
        "title": "Sales Manager",
        "company": "SalesPro",
        "description": "Lead sales team and drive revenue.",
        "required_skills": ["communication", "leadership", "negotiation", "crm", "excel", "presentation", "marketing"],
        "requirements": ["BS in Business", "3+ years"],
        "qualifications": ["Persuasive", "Goal-oriented"],
        "matching_threshold": 40.0,
        "minimum_gpa": 2.0,
        "required_education": "Bachelor",
    },
    "HR": {
        "title": "HR Manager",
        "company": "PeopleFirst",
        "description": "Oversee recruitment and employee relations.",
        "required_skills": ["communication", "recruitment", "leadership", "hr policies", "conflict resolution", "excel", "interviewing"],
        "requirements": ["BS in HR", "3+ years"],
        "qualifications": ["Interpersonal", "Ethical"],
        "matching_threshold": 40.0,
        "minimum_gpa": 2.5,
        "required_education": "Bachelor",
    },
    "DESIGNER": {
        "title": "UI/UX Designer",
        "company": "DesignStudio",
        "description": "Create user-centered designs.",
        "required_skills": ["figma", "ui/ux", "photoshop", "illustrator", "html", "css", "javascript", "prototyping"],
        "requirements": ["BS in Design", "2+ years"],
        "qualifications": ["Creative", "Detail-oriented"],
        "matching_threshold": 40.0,
        "minimum_gpa": 2.5,
        "required_education": "Bachelor",
    },
    "TEACHER": {
        "title": "High School Teacher",
        "company": "EduStar",
        "description": "Teach and mentor students.",
        "required_skills": ["communication", "lesson planning", "classroom management", "curriculum development", "leadership", "public speaking"],
        "requirements": ["BS in Education", "Certification"],
        "qualifications": ["Patient", "Inspirational"],
        "matching_threshold": 40.0,
        "minimum_gpa": 2.5,
        "required_education": "Bachelor",
    },
    "ACCOUNTANT": {
        "title": "Accountant",
        "company": "AuditFirst",
        "description": "Manage financial records and tax preparation.",
        "required_skills": ["accounting", "excel", "quickbooks", "tax preparation", "financial reporting", "auditing", "data analysis"],
        "requirements": ["BS in Accounting", "CPA pref."],
        "qualifications": ["Analytical", "Ethical"],
        "matching_threshold": 50.0,
        "minimum_gpa": 3.0,
        "required_education": "Bachelor",
    },
}


def process_cv(text, job):
    """Run full pipeline on one CV. Returns dict of all results."""
    cleaned = clean_text(text)

    # Extract entities
    name = extract_name(cleaned)
    emails = extract_emails(cleaned)
    phones = extract_phones(cleaned)
    skills = extract_skills(cleaned)
    education = extract_education(cleaned)
    experience = extract_experience(cleaned)
    years_exp = estimate_years_of_experience(cleaned)
    gpa = extract_gpa(cleaned)
    certs = extract_certifications(cleaned)
    projects = extract_projects(cleaned)

    # Score calculation
    cv_skills = {s.lower().strip() for s in skills}
    job_skills = {s.lower().strip() for s in job["required_skills"]}
    matching_skills = list(cv_skills & job_skills)
    missing_skills = list(job_skills - cv_skills)
    skill_ratio = len(matching_skills) / len(job_skills) if job_skills else 0.0
    skill_score = skill_ratio * 60.0

    # n-gram fallback similarity (BERT nahi hai)
    cv_t = preprocess_for_embedding(" ".join([
        f"Skills: {', '.join(skills)}",
        f"Experience: {experience[:500]}",
        f"Education: {education[:300]}",
    ]))
    job_t = preprocess_for_embedding(" ".join([
        f"Title: {job['title']}",
        f"Description: {job['description']}",
        f"Required Skills: {', '.join(job['required_skills'])}",
    ]))
    def _ngrams(t, n):
        d = {}
        for i in range(len(t) - n + 1):
            g = t[i:i+n]
            d[g] = d.get(g, 0) + 1
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
    bi_cv, bi_job = _ngrams(cv_t.lower(), 2), _ngrams(job_t.lower(), 2)
    tri_cv, tri_job = _ngrams(cv_t.lower(), 3), _ngrams(job_t.lower(), 3)
    cos_sim = _cosine(bi_cv, bi_job) * 0.4 + _cosine(tri_cv, tri_job) * 0.6

    bert_score = cos_sim * 10.0
    if skill_ratio < 0.3 and cos_sim > 0.3:
        bert_score *= 0.4

    if years_exp >= 5.0:
        exp_score = 15.0
    elif years_exp >= 2.0:
        exp_score = 12.0
    elif years_exp >= 1.0:
        exp_score = 8.0
    elif years_exp > 0:
        exp_score = 4.0
    else:
        exp_score = 0.0

    edu_lower = education.lower()
    if "phd" in edu_lower or "doctorate" in edu_lower:
        edu_score = 10.0
    elif "master" in edu_lower or "m.s." in edu_lower:
        edu_score = 8.0
    elif "bachelor" in edu_lower or "b.s." in edu_lower or "b.tech" in edu_lower:
        edu_score = 6.0
    elif edu_lower:
        edu_score = 4.0
    else:
        edu_score = 0.0

    gpa_bonus = 1.5 if gpa >= 3.5 else (1.0 if gpa >= 2.5 else 0.0)
    cert_bonus = min(len(certs) * 1.0, 2.0)
    proj_bonus = min(len(projects) * 0.5, 1.5)
    extra = gpa_bonus + cert_bonus + proj_bonus

    total = min(max(skill_score + bert_score + exp_score + edu_score + extra, 0.0), 100.0)
    threshold = job.get("matching_threshold", 50.0)
    passed = total >= threshold

    return {
        "name": name[:60] if name else "(unknown)",
        "email": emails[0] if emails else "",
        "skills_count": len(skills),
        "skills_matched": len(matching_skills),
        "skills_missing": len(missing_skills),
        "skill_score": round(skill_score, 1),
        "bert_score": round(bert_score, 1),
        "exp_score": round(exp_score, 1),
        "edu_score": round(edu_score, 1),
        "extra_score": round(extra, 1),
        "total_score": round(total, 1),
        "years_exp": years_exp,
        "gpa": gpa,
        "has_education": bool(education),
        "has_certs": len(certs) > 0,
        "has_projects": len(projects) > 0,
        "passed": passed,
        "matching": ", ".join(matching_skills[:5]),
        "missing": ", ".join(missing_skills[:5]),
    }


def main():
    parser = argparse.ArgumentParser(description="Batch CV processing report")
    parser.add_argument("--count", type=int, default=100, help="Number of CVs to process (default: 100)")
    parser.add_argument("--category", type=str, default=None, help="Filter by category")
    parser.add_argument("--threshold", type=float, default=None, help="Override threshold")
    parser.add_argument("--output", type=str, default=None, help="Save results to CSV")
    args = parser.parse_args()

    print(f"\n{SEP}")
    print("  BATCH CV PIPELINE REPORT")
    print("  Supervisor ke liye - 100+ CVs ka pipeline output")
    print(f"{SEP}")

    # Load all CVs from dataset
    all_cvs = []
    with open(CSV_PATH, encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader)
        for row in reader:
            if len(row) >= 4:
                rid, text, html, cat = row[0], row[1], row[2], row[3].strip().upper()
                if args.category and cat != args.category.upper():
                    continue
                all_cvs.append((rid, text, cat))

    total_available = len(all_cvs)
    count = min(args.count, total_available)
    selected = random.sample(all_cvs, count)

    print(f"\n  Total CVs available: {total_available}")
    print(f"  Processing:          {count} CVs")
    if args.category:
        print(f"  Category filter:     {args.category.upper()}")
    else:
        cats = set(c for _, _, c in selected)
        print(f"  Categories:          {', '.join(sorted(cats)[:8])}{'...' if len(cats) > 8 else ''}")

    # Count categories
    cat_counter = Counter(c for _, _, c in selected)
    print(f"\n  Category breakdown:")
    for cat, n in sorted(cat_counter.items(), key=lambda x: -x[1]):
        bar = "#" * int(n / count * 40)
        print(f"    {cat:30s} {n:4d} ({n*100//count:2d}%)  {bar}")

    print(f"\n{SEP}")
    print("  PROCESSING CVs...")
    print(f"{SEP}")

    # Process each CV
    results = []
    start = time.time()
    for i, (rid, text, cat) in enumerate(selected):
        job = DATASET_JOBS.get(cat)
        if not job:
            # Pick the closest category
            fallback_cats = ["INFORMATION-TECHNOLOGY", "ENGINEERING", "FINANCE", "SALES", "HR"]
            for fc in fallback_cats:
                if fc in cat or cat in fc:
                    job = DATASET_JOBS.get(fc)
                    break
            if not job:
                job = DATASET_JOBS["INFORMATION-TECHNOLOGY"]

        if args.threshold is not None:
            job = {**job, "matching_threshold": args.threshold}

        r = process_cv(text, job)
        r["id"] = rid
        r["category"] = cat
        r["job_title"] = job["title"]
        r["threshold"] = job["matching_threshold"]
        results.append(r)

        if (i + 1) % 25 == 0 or i == 0:
            elapsed = time.time() - start
            print(f"    [{i+1:4d}/{count}] {elapsed:.1f}s elapsed")

    elapsed = time.time() - start
    avg_time = elapsed / count

    # ================================================================
    # SUMMARY STATISTICS
    # ================================================================
    passed_count = sum(1 for r in results if r["passed"])
    failed_count = count - passed_count

    scores = [r["total_score"] for r in results]
    skill_scores = [r["skill_score"] for r in results]
    bert_scores = [r["bert_score"] for r in results]
    exp_scores = [r["exp_score"] for r in results]
    edu_scores = [r["edu_score"] for r in results]
    extra_scores = [r["extra_score"] for r in results]
    years_list = [r["years_exp"] for r in results]
    gpa_list = [r["gpa"] for r in results if r["gpa"] > 0]

    print(f"\n{SEP}")
    print("  REPORT: PIPELINE SUMMARY")
    print(f"{SEP}")

    print(f"""
  Processing Time
    Total:      {elapsed:.1f}s
    Per CV:     {avg_time:.3f}s ({count/elapsed:.1f} CVs/sec)

  Pass/Fail
    Passed:     {passed_count:4d}  ({passed_count*100//count:2d}%)
    Failed:     {failed_count:4d}  ({failed_count*100//count:2d}%)
    Threshold:  {results[0]['threshold'] if results else 50:.0f}%

  Score Distribution (out of 100)
    Mean:       {mean(scores):.1f}
    Median:     {median(scores):.1f}
    Std Dev:    {stdev(scores):.1f}
    Min:        {min(scores):.1f}
    Max:        {max(scores):.1f}

  Component Scores (mean)
    Skills:     {mean(skill_scores):.1f}/60  ({mean(skill_scores)/60*100:.0f}%)
    BERT:       {mean(bert_scores):.1f}/10
    Experience: {mean(exp_scores):.1f}/15
    Education:  {mean(edu_scores):.1f}/10
    Extra:      {mean(extra_scores):.1f}/5

  Experience
    Mean yrs:   {mean(years_list):.1f}
    Median yrs: {median(years_list):.1f}
    0 yrs:      {sum(1 for y in years_list if y == 0)} CVs
    1-2 yrs:    {sum(1 for y in years_list if 0 < y <= 2)} CVs
    3-5 yrs:    {sum(1 for y in years_list if 2 < y <= 5)} CVs
    5+ yrs:     {sum(1 for y in years_list if y > 5)} CVs

  GPA
    With GPA:   {len(gpa_list)} CVs
    Mean GPA:   {mean(gpa_list):.2f}/{len(gpa_list)} found
    >= 3.0:     {sum(1 for g in gpa_list if g >= 3.0)} CVs
    >= 3.5:     {sum(1 for g in gpa_list if g >= 3.5)} CVs

  Data Quality
    Has email:  {sum(1 for r in results if r['email'])} CVs
    Has edu:    {sum(1 for r in results if r['has_education'])} CVs
    Has certs:  {sum(1 for r in results if r['has_certs'])} CVs
    Has projs:  {sum(1 for r in results if r['has_projects'])} CVs
""")

    # ================================================================
    # SCORE BANDS
    # ================================================================
    print(f"  Score Distribution (bands):")
    bands = [(0, 20), (20, 40), (40, 60), (60, 80), (80, 100)]
    for lo, hi in bands:
        n = sum(1 for s in scores if lo <= s < hi)
        bar = "#" * n
        print(f"    {lo:3d}-{hi:3d}: {n:4d} CVs  {bar}")
    n100 = sum(1 for s in scores if s == 100)
    print(f"    100   : {n100:4d} CVs")

    # ================================================================
    # INDIVIDUAL RESULTS TABLE
    # ================================================================
    print(f"\n{SEP}")
    print("  INDIVIDUAL CV RESULTS (sorted by score)")
    print(f"{SEP}")

    sorted_results = sorted(results, key=lambda r: -r["total_score"])
    header = f"  {'ID':>8s} {'Category':22s} {'Name':30s} {'Score':>6s} {'Skills':>7s} {'Match':>7s} {'Exp':>5s} {'GPA':>5s} {'Result':>8s}"
    print(header)
    print(f"  {'-'*100}")

    for r in sorted_results:
        result_str = "PASS [OK]" if r["passed"] else "FAIL"
        # Truncate name
        name_short = r["name"][:30] if len(r["name"]) > 30 else r["name"]
        print(f"  {r['id']:>8s} {r['category'][:22]:22s} {name_short:30s} "
              f"{r['total_score']:6.1f} {r['skills_count']:7d} {r['skills_matched']:7d} "
              f"{r['years_exp']:5.1f} {r['gpa']:5.2f} {result_str:>8s}")

    # ================================================================
    # CATEGORY-WISE BREAKDOWN
    # ================================================================
    print(f"\n{SEP}")
    print("  CATEGORY-WISE BREAKDOWN")
    print(f"{SEP}")

    cat_results = {}
    for r in results:
        cat_results.setdefault(r["category"], []).append(r)

    header2 = f"  {'Category':25s} {'Count':>5s} {'Pass':>5s} {'Pass%':>6s} {'Avg Score':>9s} {'Avg Skills':>10s}"
    print(header2)
    print(f"  {'-'*65}")

    for cat in sorted(cat_results.keys()):
        cr = cat_results[cat]
        n = len(cr)
        p = sum(1 for r in cr if r["passed"])
        avg_s = mean(r["total_score"] for r in cr)
        avg_sk = mean(r["skills_count"] for r in cr)
        print(f"  {cat[:25]:25s} {n:5d} {p:5d} {p*100//n:5d}% {avg_s:8.1f} {avg_sk:9.1f}")

    # ================================================================
    # SAVE TO CSV
    # ================================================================
    if args.output:
        with open(args.output, "w", newline="", encoding="utf-8") as f:
            fieldnames = ["id", "category", "name", "email", "total_score", "passed",
                          "skills_count", "skills_matched", "skills_missing",
                          "skill_score", "bert_score", "exp_score", "edu_score", "extra_score",
                          "years_exp", "gpa", "has_education", "has_certs", "has_projects",
                          "matching", "missing", "job_title", "threshold"]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(results)
        print(f"\n  Results saved to: {args.output}")

    print(f"\n{SEP}")
    print("  REPORT COMPLETE")
    print(f"{SEP}")
    print(f"  {count} CVs processed in {elapsed:.1f}s")
    print(f"  Pass rate: {passed_count}/{count} ({passed_count*100//count}%)")
    print(f"  Average score: {mean(scores):.1f}/100")
    print()


if __name__ == "__main__":
    main()
