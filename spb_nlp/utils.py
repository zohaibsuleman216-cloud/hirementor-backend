"""Text preprocessing utilities for NLP pipeline."""

import re
from typing import List, Set


SKILL_KEYWORDS: Set[str] = {
    # Programming Languages
    "programming", "coding", "software development", "software engineering",
    "python", "java", "kotlin", "javascript", "typescript", "c++", "c#", "c",
    "golang", "go", "rust", "swift", "php", "ruby", "scala", "r", "matlab",
    "dart", "html", "css", "sass", "less",
    # Web Frameworks
    "react", "angular", "vue", "django", "flask", "fastapi", "spring boot",
    "express", "node.js", "next.js", "nuxt.js", "svelte", "jquery",
    "bootstrap", "tailwind", "jsp", "servlets", "asp.net",
    # Mobile
    "android", "ios", "flutter", "react native", "xamarin", "swiftui",
    "jetpack compose", "kotlin multiplatform",
    # Databases
    "sql", "mysql", "postgresql", "mongodb", "oracle", "sqlite", "redis",
    "cassandra", "dynamodb", "firebase", "supabase", "mariadb", "couchdb",
    # Cloud & DevOps
    "aws", "azure", "gcp", "google cloud", "docker", "kubernetes", "jenkins",
    "terraform", "ansible", "ci/cd", "github actions", "gitlab ci",
    "circleci", "nginx", "apache", "linux", "bash", "powershell",
    "data center", "data centre", "data center management",
    "server administration", "network administration", "virtualization",
    "vmware", "disaster recovery", "system administration",
    # Data Science & AI
    "machine learning", "deep learning", "nlp", "natural language processing",
    "computer vision", "tensorflow", "pytorch", "keras", "scikit-learn",
    "pandas", "numpy", "data science", "data analysis", "data engineering",
    "artificial intelligence", "llm", "langchain", "rag", "generative ai",
    "opencv", "tableau", "power bi", "spark", "hadoop", "airflow",
    # Tools & Platforms
    "git", "github", "gitlab", "bitbucket", "jira", "confluence",
    "postman", "swagger", "graphql", "rest api", "grpc", "kafka",
    "rabbitmq", "elasticsearch", "logstash", "kibana",
    # Soft Skills
    "communication", "leadership", "teamwork", "problem solving",
    "critical thinking", "creativity", "adaptability", "time management",
    "collaboration", "presentation", "negotiation", "project management",
    "analytical", "strategic", "interpersonal", "decision making",
    # Certifications
    "pmp", "aws certified", "scrum master", "cissp", "ceh",
    "comptia", "itil", "google cloud certified", "azure certified",
    # Other Technical
    "blockchain", "cybersecurity", "ethical hacking", "penetration testing",
    "game development", "unity", "unreal engine", "embedded systems",
    "iot", "robotics", "ar/vr", "augmented reality", "virtual reality",
    "microservices", "serverless", "web3", "solidity", "smart contracts",
    "ui/ux", "ui design", "ux design", "figma", "sketch", "adobe xd",
    "photoshop", "illustrator", "after effects",

    # ---- Non-technical / other professional fields ---- #
    # Sales & Business Development
    "sales", "cold calling", "b2b sales", "b2c sales", "account management",
    "client relations", "customer relations", "lead generation", "crm",
    "salesforce", "hubspot", "sales forecasting", "quota attainment",
    "territory management", "upselling", "cross-selling", "closing deals",
    "business development", "prospecting", "sales pipeline", "retail sales",
    "merchandising", "point of sale", "pos systems",
    # Marketing & Public Relations
    "digital marketing", "social media marketing", "content marketing",
    "email marketing", "seo", "sem", "google analytics", "google ads",
    "facebook ads", "brand management", "market research", "copywriting",
    "public relations", "media relations", "press releases", "campaign management",
    "influencer marketing", "marketing strategy", "advertising",
    # HR & Recruitment
    "recruitment", "talent acquisition", "onboarding", "employee relations",
    "performance management", "hr policies", "compensation and benefits",
    "payroll", "hris", "workday", "labor relations", "employee engagement",
    "training and development", "succession planning", "diversity and inclusion",
    "conflict resolution", "workforce planning", "hr compliance",
    # Finance & Accounting
    "accounting", "bookkeeping", "financial analysis", "financial modeling",
    "accounts payable", "accounts receivable", "general ledger", "gaap",
    "budgeting", "forecasting", "tax preparation", "auditing", "quickbooks",
    "sap", "financial reporting", "reconciliation", "cost accounting",
    "cpa", "cfa", "investment analysis", "risk management", "underwriting",
    "banking", "loan processing", "credit analysis", "portfolio management",
    # Healthcare & Nursing
    "patient care", "clinical", "nursing", "cpr", "bls", "acls", "phlebotomy",
    "medical terminology", "ehr", "emr", "epic", "cerner", "hipaa",
    "vital signs", "medication administration", "triage", "patient advocacy",
    "healthcare administration", "medical billing", "medical coding", "icd-10",
    # Education & Teaching
    "teaching", "curriculum development", "lesson planning", "classroom management",
    "differentiated instruction", "student assessment", "iep", "special education",
    "tutoring", "instructional design", "e-learning", "educational technology",
    "childcare", "early childhood education",
    # Culinary & Hospitality
    "culinary", "menu planning", "food safety", "food preparation",
    "kitchen management", "inventory management", "cost control",
    "banquet", "catering", "baking", "pastry", "line cook", "sous chef",
    "haccp", "servsafe", "hospitality", "guest services", "housekeeping",
    "front desk", "reservations", "event planning",
    # Legal
    "legal research", "litigation", "contract drafting", "compliance",
    "paralegal", "legal writing", "case management", "due diligence",
    "intellectual property", "corporate law", "regulatory compliance",
    # Construction & Engineering (non-software)
    "blueprint reading", "autocad", "solidworks", "project scheduling",
    "civil engineering", "mechanical engineering", "electrical engineering",
    "structural engineering", "osha", "quality control", "quality assurance",
    "six sigma", "lean manufacturing", "cad", "hvac", "welding", "plumbing",
    "carpentry", "site supervision", "safety compliance",
    # Aviation & Automotive
    "aircraft maintenance", "faa regulations", "flight operations",
    "ground support", "logistics", "supply chain", "fleet management",
    "automotive repair", "diagnostics", "asian mechanic", "vehicle inspection",
    # Agriculture
    "crop management", "livestock management", "irrigation", "agronomy",
    "sustainable farming", "gis",
    # Fitness & Personal Training
    "personal training", "fitness assessment", "nutrition counseling",
    "group fitness", "exercise physiology", "wellness coaching",
    # Arts, Design & Media
    "graphic design", "video editing", "photography", "adobe premiere",
    "creative direction", "storyboarding", "animation", "journalism",
    "editing", "proofreading", "content writing", "scriptwriting",
    # Consulting & Business
    "business analysis", "process improvement", "stakeholder management",
    "strategic planning", "kpi", "management consulting", "change management",
    # Customer Service / BPO
    "customer service", "call center", "technical support", "help desk",
    "ticketing systems", "zendesk", "customer satisfaction", "escalation handling",
}

# Curated professional skill families. Membership in the same cluster is a
# strong, auditable relatedness signal (e.g. "kotlin" <-> "android development")
# that generic short-phrase BERT similarity is often too noisy to capture
# reliably on its own — see SemanticMatcher, which combines this with embeddings.
SKILL_CLUSTERS: List[Set[str]] = [
    {"python", "django", "flask", "fastapi", "backend development", "python development"},
    {"java", "kotlin", "spring boot", "jsp", "servlets", "backend development"},
    {"javascript", "typescript", "react", "angular", "vue", "node.js", "next.js",
     "nuxt.js", "svelte", "jquery", "frontend development", "web development", "html", "css"},
    {"android", "kotlin", "java", "jetpack compose", "kotlin multiplatform",
     "android development", "mobile development"},
    {"ios", "swift", "swiftui", "xcode", "ios development", "mobile development"},
    {"flutter", "dart", "react native", "xamarin", "mobile development"},
    {"sql", "mysql", "postgresql", "mongodb", "oracle", "sqlite", "redis",
     "cassandra", "dynamodb", "mariadb", "couchdb", "database", "database management"},
    {"aws", "azure", "gcp", "google cloud", "docker", "kubernetes", "jenkins",
     "terraform", "ansible", "ci/cd", "devops", "cloud computing",
     "data center", "data centre", "data center management",
     "server administration", "network administration", "virtualization",
     "vmware", "disaster recovery", "system administration"},
    {"machine learning", "deep learning", "nlp", "natural language processing",
     "computer vision", "tensorflow", "pytorch", "keras", "scikit-learn",
     "pandas", "numpy", "data science", "data analysis", "data engineering",
     "artificial intelligence", "statistics"},
    {"ui/ux", "ui design", "ux design", "figma", "sketch", "adobe xd",
     "photoshop", "illustrator", "after effects", "graphic design",
     "visual design", "branding"},
    {"digital marketing", "seo", "social media marketing", "content marketing",
     "google analytics", "marketing", "email marketing"},
    {"cybersecurity", "ethical hacking", "penetration testing",
     "network security", "firewall configuration", "information security"},
    {"financial analysis", "excel", "accounting", "financial modeling",
     "bookkeeping", "data analysis"},

    # ---- Non-technical clusters ---- #
    {"sales", "cold calling", "b2b sales", "b2c sales", "account management",
     "lead generation", "crm", "salesforce", "hubspot", "sales pipeline",
     "business development", "prospecting", "closing deals", "quota attainment"},
    {"digital marketing", "social media marketing", "content marketing",
     "seo", "sem", "google ads", "facebook ads", "brand management",
     "marketing strategy", "advertising", "market research", "public relations",
     "media relations", "campaign management"},
    {"recruitment", "talent acquisition", "onboarding", "employee relations",
     "performance management", "hr policies", "compensation and benefits",
     "hris", "workday", "employee engagement", "training and development",
     "workforce planning", "hr compliance"},
    {"accounting", "bookkeeping", "accounts payable", "accounts receivable",
     "general ledger", "gaap", "financial reporting", "reconciliation",
     "quickbooks", "sap", "cost accounting", "cpa", "auditing"},
    {"financial analysis", "financial modeling", "investment analysis",
     "risk management", "portfolio management", "banking", "underwriting",
     "credit analysis", "cfa"},
    {"patient care", "clinical", "nursing", "cpr", "bls", "acls", "phlebotomy",
     "medical terminology", "vital signs", "medication administration",
     "triage", "ehr", "emr", "epic", "cerner", "healthcare administration"},
    {"medical billing", "medical coding", "icd-10", "healthcare administration",
     "hipaa", "ehr", "emr"},
    {"teaching", "curriculum development", "lesson planning", "classroom management",
     "differentiated instruction", "student assessment", "iep",
     "special education", "instructional design", "educational technology",
     "tutoring", "early childhood education"},
    {"culinary", "menu planning", "food preparation", "kitchen management",
     "baking", "pastry", "line cook", "sous chef", "haccp", "servsafe",
     "food safety", "catering", "banquet"},
    {"hospitality", "guest services", "housekeeping", "front desk",
     "reservations", "event planning", "catering", "banquet"},
    {"legal research", "litigation", "contract drafting", "paralegal",
     "legal writing", "case management", "due diligence",
     "intellectual property", "corporate law", "regulatory compliance"},
    {"blueprint reading", "autocad", "solidworks", "cad", "civil engineering",
     "mechanical engineering", "electrical engineering", "structural engineering",
     "construction", "site supervision"},
    {"osha", "quality control", "quality assurance", "six sigma",
     "lean manufacturing", "safety compliance"},
    {"customer service", "call center", "technical support", "help desk",
     "ticketing systems", "zendesk", "customer satisfaction",
     "escalation handling", "bpo"},
    {"business analysis", "process improvement", "stakeholder management",
     "strategic planning", "kpi", "management consulting", "change management",
     "consulting"},
    {"graphic design", "video editing", "photography", "adobe premiere",
     "creative direction", "animation", "visual design"},
    {"journalism", "editing", "proofreading", "content writing",
     "copywriting", "scriptwriting", "public relations"},
]


def skills_in_same_cluster(skill_a: str, skill_b: str) -> bool:
    """Whole-word/phrase check: do these two skills share a curated cluster?"""
    def _contains(term: str, skill: str) -> bool:
        if term == skill:
            return True
        pattern = r'(?<!\w)' + re.escape(term) + r'(?!\w)'
        return bool(re.search(pattern, skill)) or bool(re.search(r'(?<!\w)' + re.escape(skill) + r'(?!\w)', term))

    for cluster in SKILL_CLUSTERS:
        a_in = any(_contains(term, skill_a) for term in cluster)
        b_in = any(_contains(term, skill_b) for term in cluster)
        if a_in and b_in:
            return True
    return False


EDUCATION_KEYWORDS: Set[str] = {
    "bachelor", "master", "phd", "doctorate", "associate", "diploma",
    "b.s.", "b.a.", "m.s.", "m.a.", "ph.d.", "bs", "ba", "ms", "ma", "phd",
    "b.tech", "m.tech", "b.e.", "m.e.", "bcom", "mcom", "bba", "mba",
    "high school", "intermediate", "a-level", "o-level", "matriculation",
}

EXPERIENCE_INDICATORS: Set[str] = {
    "experience", "work history", "employment", "professional background",
    "career", "job", "position", "role", "internship", "worked at",
    "employed", "worked as", "responsible for", "developed", "designed",
    "implemented", "managed", "led", "created", "built", "achieved",
}


def clean_text(text: str) -> str:
    """Normalize whitespace while preserving paragraph structure."""
    text = re.sub(r'\r\n', '\n', text)
    text = re.sub(r'[ \t]+', ' ', text)  # collapse horizontal whitespace only
    text = re.sub(r'\n\s*\n', '\n', text)  # collapse multiple blank lines
    text = re.sub(r'[•●▪►➢→▪■□◆◇○●▶]', '-', text)
    return text.strip()


def extract_emails(text: str) -> List[str]:
    return re.findall(r'[\w.+-]+@[\w-]+\.[\w.-]+', text.lower())


def extract_phones(text: str) -> List[str]:
    patterns = [
        r'\+\d{1,3}[-.\s]?\(?\d{1,4}\)?[-.\s]?\d{1,4}[-.\s]?\d{1,9}',
        r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',
    ]
    phones = []
    for p in patterns:
        phones.extend(re.findall(p, text))
    return phones


def extract_skills(text: str) -> List[str]:
    """Extract known skill keywords using word-boundary matching."""
    text_lower = text.lower()
    found = set()
    for skill in sorted(SKILL_KEYWORDS, key=len, reverse=True):
        pattern = r'(?<!\w)' + re.escape(skill) + r'(?!\w)'
        if re.search(pattern, text_lower):
            found.add(skill)
    return sorted(found)


def extract_education(text: str) -> str:
    """Extract education section from resume text."""
    lines = text.split('\n')
    edu_lines = []
    in_edu = False
    section_headers = ['education', 'academic background', 'academic qualifications']
    for line in lines:
        line_lower = line.lower().strip()
        header_hit = next((kw for kw in section_headers if kw in line_lower), None)
        if header_hit:
            in_edu = True
            # Single-paragraph resumes (pasted text, or a PDF that didn't
            # preserve line breaks) put the degree on the *same* line as the
            # "Education:" label — capture that remainder too, not just
            # whatever comes on later lines.
            remainder = line[line_lower.index(header_hit) + len(header_hit):].strip(" :-\t")
            if remainder:
                edu_lines.append(remainder)
            continue
        if in_edu:
            if any(kw in line_lower for kw in ['experience', 'skills',
                                                 'projects', 'certifications',
                                                 'work history', 'employment']):
                break
            if line.strip():
                edu_lines.append(line.strip())
    if edu_lines:
        return ' '.join(edu_lines)

    # No "Education" section header found at all (or it was empty) — fall
    # back to scanning the raw text directly for a degree phrase, so resumes
    # that mention a degree without a formal section header still register.
    degree_pattern = (
        r'((?:bachelor|master|ph\.?d\.?|doctorate|b\.?s\.?c?\.?|b\.?a\.?|'
        r'b\.?tech|b\.?e\.?|m\.?s\.?c?\.?|m\.?a\.?|m\.?tech|mba)[^.,;\n]{0,60})'
    )
    match = re.search(degree_pattern, text, re.IGNORECASE)
    return match.group(1).strip() if match else ""


def extract_experience(text: str) -> str:
    """Extract experience section, with date-based fallback for unstructured CVs."""
    lines = text.split('\n')
    exp_lines = []
    in_exp = False
    section_headers = [
        'experience', 'work history', 'employment', 'professional background',
        'professional experience', 'work experience', 'career history',
        'employment history', 'job experience', 'relevant experience',
        'work background', 'professional history', 'career background',
    ]
    section_end = [
        'education', 'skills', 'certifications', 'projects', 'academic',
        'training', 'qualifications', 'references', 'summary',
    ]
    for line in lines:
        line_lower = line.lower().strip()
        if any(kw in line_lower for kw in section_headers):
            in_exp = True
            continue
        if in_exp:
            if any(kw in line_lower for kw in section_end):
                break
            if line.strip():
                exp_lines.append(line.strip())
    result = ' '.join(exp_lines) if exp_lines else ""
    # Fallback: if section parsing found nothing, look for date patterns
    if not result:
        date_lines = set()
        # Month-name based: "Jan 2020 - Feb 2021"
        month = r'(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)'
        p1 = re.compile(month + r'\s*\d{4}\s*(?:-|–|to)\s*', re.I)
        # Numeric year range: "2015 - 2018" or "2015-2018" at start of line
        p2 = re.compile(r'^\s*(?:19|20)\d{2}\s*(?:-|–)\s*(?:(?:19|20)\d{2}|Present|Current)', re.I)
        # Month-year to Month-year: "Jan 2020 - Present"
        p3 = re.compile(month + r'\s*\d{4}\s*(?:-|–|to)\s*(?:' + month + r'\s*\d{4}|Present|Current)', re.I)
        for l in lines:
            stripped = l.strip()
            if not stripped:
                continue
            if p1.search(stripped) or p2.search(stripped) or p3.search(stripped):
                date_lines.add(stripped)
        if date_lines:
            result = ' '.join(sorted(date_lines))
    return result


def extract_name(text: str) -> str:
    """Heuristic: first non-empty line at top of resume is usually the name."""
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    if not lines:
        return ""
    candidate = lines[0]
    if len(candidate.split()) in [2, 3, 4] and not any(
            kw in candidate.lower() for kw in ['resume', 'cv', 'curriculum',
                                                'vitae', 'summary']):
        return candidate
    return candidate


_WORD_TO_NUM = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
}


def estimate_years_of_experience(text: str) -> float:
    text_lower = text.lower()
    patterns = [
        # "3-5 years" / "3 to 5 years" — take the lower bound, which is what
        # a stated range's *minimum* actually means for a requirement.
        r'(\d+)\s*(?:-|to)\s*\d+\+?\s*(?:years?|yrs?)',
        r'(\d+)\+?\s*(?:years?|yrs?)\s*(?:of\s+)?experience',
        r'experience\s*(?:of\s+)?(\d+)\+?\s*(?:years?|yrs?)',
        r'(\d+)\+?\s*(?:years?|yrs?)\s+experience',
        # Covers "N years of <adjective> experience" too (e.g. "2 years of
        # relevant experience") since it doesn't require "experience" to
        # immediately follow — just one of these connector words.
        r'(\d+)\+?\s*(?:years?|yrs?)\s+(?:building|working|in|as|of)',
        r'(\d+)\+?\s*(?:years?|yrs?)[\'’]?\s+experience',
    ]
    years = []
    for p in patterns:
        years.extend([float(m) for m in re.findall(p, text_lower)])

    # Word-number fallback: "two years of experience", "minimum three years".
    word_pattern = r'\b(' + '|'.join(_WORD_TO_NUM.keys()) + r')\s*(?:years?|yrs?)\b'
    years.extend([float(_WORD_TO_NUM[w]) for w in re.findall(word_pattern, text_lower)])

    if years:
        return max(years)
    # Fallback: estimate from year ranges (prefer non-education lines)
    lines = text.lower().split('\n')
    edu_kw = ['education', 'degree', 'bachelor', 'master', 'b.tech', 'm.tech',
              'b.s.', 'm.s.', 'phd', 'doctorate', 'diploma', 'university', 'college']
    all_years, non_edu_years = set(), set()
    for line in lines:
        found = re.findall(r'\b(19[5-9]\d|20[0-2]\d)\b', line)
        if not found:
            continue
        for y in found:
            all_years.add(int(y))
            if not any(kw in line for kw in edu_kw):
                non_edu_years.add(int(y))
    source = non_edu_years if len(non_edu_years) >= 2 else (all_years if len(all_years) >= 2 else set())
    if len(source) >= 2:
        span = max(source) - min(source)
        if 1 <= span <= 40:
            return float(span)
    return 0.0


def extract_gpa(text: str) -> float:
    patterns = [
        r'(?:gpa|cgpa|g\.p\.a\.)\s*:?\s*(\d+\.?\d*)',
        r'(\d+\.\d+)\s*/\s*4\.?0',
        r'(\d+\.\d+)\s*out\s*of\s*4',
    ]
    for p in patterns:
        matches = re.findall(p, text.lower())
        if matches:
            val = float(matches[0])
            if val <= 4.0:
                return val
    return 0.0


def extract_certifications(text: str) -> List[str]:
    cert_keywords = [
        "certified", "certification", "certificate", "pmp", "aws certified",
        "scrum master", "cissp", "ceh", "comptia", "itil", "cfa", "cpa",
        "google certified", "microsoft certified", "oracle certified",
    ]
    lines = text.lower().split('\n')
    certs = []
    in_cert_section = False
    for line in lines:
        if any(kw in line for kw in ['certifications', 'certificates', 'licenses']):
            in_cert_section = True
            continue
        if in_cert_section:
            if any(kw in line for kw in ['experience', 'education', 'skills',
                                           'projects', 'references']):
                break
            if line.strip() and not line.startswith('-'):
                certs.append(line.strip())
    if not certs:
        for line in lines:
            if any(kw in line for kw in cert_keywords):
                certs.append(line.strip())
    return list(set(certs))[:10]


def extract_projects(text: str) -> List[str]:
    lines = text.split('\n')
    projects = []
    in_proj = False
    for line in lines:
        if line.lower().strip() in ['projects', 'project', 'academic projects',
                                     'personal projects', 'key projects']:
            in_proj = True
            continue
        if in_proj:
            if any(kw in line.lower() for kw in ['experience', 'education',
                                                   'skills', 'certifications',
                                                   'work history']):
                break
            if line.strip():
                projects.append(line.strip())
    return projects[:10]


def preprocess_for_embedding(text: str) -> str:
    """Clean and normalize text for embedding generation."""
    text = clean_text(text)
    text = re.sub(r'[^a-zA-Z0-9\s.,;:!?\'\"-]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text
