"""
Tests for SPB NLP Backend modules.
Run:  pytest tests/ -v
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from spb_nlp.cv_parser import CVParser, SpacyNerParser, _HAS_SPACY
from spb_nlp.semantic_matcher import SemanticMatcher, _HAS_EMBEDDINGS
from spb_nlp.shortlister import Shortlister
from spb_nlp.recommender import JobRecommender
from spb_nlp.models import CVParseResult, Job, Student, MatchResult


SAMPLE_RESUME = """
Jane Smith
jane.smith@example.com
+92-300-1234567

SUMMARY
Data scientist with 3+ years of experience in ML and analytics.

SKILLS
Python, R, Machine Learning, SQL, TensorFlow, PyTorch, NLP,
Data Analysis, Statistics, Tableau, Git, AWS

EXPERIENCE
Data Scientist | AnalyticsPro | 2021-2024
- Built ML models for customer churn prediction (95% accuracy)
- Developed NLP pipeline for sentiment analysis
- Created dashboards using Tableau

Junior Data Analyst | DataCorp | 2020-2021
- Performed statistical analysis on sales data
- Automated reporting with Python scripts

EDUCATION
Master of Science in Data Science
Stanford University | GPA: 3.8/4.0 | 2018-2020

CERTIFICATIONS
AWS Certified Machine Learning Specialty
"""


def test_cv_parser_extracts_all_fields():
    parser = CVParser()
    result = parser.parse_text(SAMPLE_RESUME)

    assert result.candidate_name.startswith("Jane")
    assert "jane.smith@example.com" in result.email
    assert result.phone
    assert "python" in [s.lower() for s in result.skills]
    assert "machine learning" in [s.lower() for s in result.skills]
    assert result.education
    assert result.gpa > 0
    assert result.years_of_experience > 0
    assert result.certifications


def test_cv_parser_empty_text_returns_defaults():
    parser = CVParser()
    result = parser.parse_text("")
    assert isinstance(result, CVParseResult)
    assert result.candidate_name == ""


def test_spacy_ner_parser_fallback_or_ner():
    parser = SpacyNerParser()
    result = parser.parse_text(SAMPLE_RESUME)

    # Must always return valid CVParseResult (NER or fallback)
    assert isinstance(result, CVParseResult)
    assert result.candidate_name  # name should be found
    assert "python" in [s.lower() for s in result.skills]
    assert result.email

    # Check model status
    if parser.is_using_spacy:
        assert parser._nlp is not None
        assert parser._model_name == "en_core_web_lg"


def test_spacy_ner_vs_regex_consistency():
    """NER and regex parsers should produce broadly consistent results."""
    regex_parser = CVParser()
    spacy_parser = SpacyNerParser()

    regex_result = regex_parser.parse_text(SAMPLE_RESUME)
    spacy_result = spacy_parser.parse_text(SAMPLE_RESUME)

    # Both should find the same email
    assert regex_result.email == spacy_result.email
    # Both should extract skills
    assert len(regex_result.skills) > 0
    assert len(spacy_result.skills) > 0


def test_semantic_matcher_bert_status():
    matcher = SemanticMatcher(lazy_load=True)
    # Should not crash regardless of BERT availability
    assert hasattr(matcher, "using_bert")
    assert isinstance(matcher.using_bert, bool)


def test_semantic_matcher_returns_match_result():
    matcher = SemanticMatcher()
    cv = CVParser().parse_text(SAMPLE_RESUME)

    job = Job(
        job_id="j1",
        title="Data Scientist",
        company_name="AI Corp",
        description="ML and data science role using Python and TensorFlow",
        required_skills=["python", "machine learning", "tensorflow", "sql"],
        matching_threshold=50.0,
    )

    result = matcher.match_cv_to_job(cv, job)
    assert isinstance(result, MatchResult)
    assert result.match_score >= 0
    assert result.job_id == "j1"
    assert result.cosine_similarity >= 0


def test_semantic_matcher_score_range():
    matcher = SemanticMatcher()
    cv = CVParser().parse_text(SAMPLE_RESUME)

    good_job = Job(
        job_id="j1", title="Data Scientist",
        company_name="X", description="ML Python TensorFlow SQL",
        required_skills=["python", "machine learning", "tensorflow", "sql"],
        matching_threshold=50.0,
    )
    bad_job = Job(
        job_id="j2", title="Chef",
        company_name="X", description="Cooking and kitchen management",
        required_skills=["cooking", "baking", "culinary"],
        matching_threshold=50.0,
    )

    good = matcher.match_cv_to_job(cv, good_job)
    bad = matcher.match_cv_to_job(cv, bad_job)

    assert good.match_score > bad.match_score


def test_shortlister_filters_by_threshold():
    from spb_nlp.models import MatchResult

    matches = [
        MatchResult(job_id="j1", match_score=80.0, meets_threshold=True),
        MatchResult(job_id="j1", match_score=45.0, meets_threshold=False),
        MatchResult(job_id="j1", match_score=60.0, meets_threshold=True),
    ]

    shortlister = Shortlister()
    result = shortlister.shortlist_for_job(matches, threshold=50.0)

    assert len(result.shortlisted) == 2
    assert len(result.rejected) == 1
    assert result.shortlisted[0].match_score == 80.0


def test_shortlister_top_k():
    from spb_nlp.models import MatchResult

    matches = [
        MatchResult(job_id="j1", match_score=90.0),
        MatchResult(job_id="j1", match_score=80.0),
        MatchResult(job_id="j1", match_score=70.0),
    ]
    result = Shortlister().shortlist_for_job(matches, threshold=0, top_k=2)
    assert len(result.shortlisted) == 2


def test_recommender_returns_ranked_list():
    student = Student(
        skills=["python", "machine learning", "sql", "tensorflow"],
        major="Data Science",
        degree="MS",
        cgpa=3.8,
    )
    jobs = [
        Job(job_id="j1", title="Data Scientist", company_name="A",
            required_skills=["python", "machine learning", "sql"],
            description="ML role"),
        Job(job_id="j2", title="Web Developer", company_name="B",
            required_skills=["html", "css", "javascript"],
            description="Frontend role"),
    ]

    recommender = JobRecommender()
    recs = recommender.recommend_for_student(student, jobs, top_k=5)

    assert len(recs) == 2
    assert recs[0].match_score >= recs[1].match_score


def test_recommender_cv_based():
    cv = CVParser().parse_text(SAMPLE_RESUME)
    jobs = [
        Job(job_id="j1", title="Data Scientist", company_name="A",
            required_skills=["python", "machine learning", "sql"],
            description="ML Python TensorFlow"),
    ]

    recommender = JobRecommender()
    recs = recommender.recommend_for_cv(cv, jobs, top_k=5)
    assert len(recs) >= 1
    assert recs[0].match_score > 0


def test_recommender_rerank():
    recs = [
        type("Rec", (object,), {"match_score": 50.0, "matching_skills": ["python"]})(),
    ]
    recommender = JobRecommender()
    # Just ensure it doesn't crash
    recommender.rerank_by_profile_change(recs, ["python"])
    assert recs[0].match_score >= 50.0
