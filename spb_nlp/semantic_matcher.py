"""
Semantic Matcher - Embedding-based cosine similarity between
CVs / student profiles and job descriptions.

Uses sentence-transformers for dense embeddings (optional - falls back
to pure-Python skill-based matching if not installed).
"""

import math
import re
from typing import List, Optional, Tuple

from spb_nlp.models import (
    CVParseResult, Job, MatchResult,
)
from spb_nlp.utils import preprocess_for_embedding

# ------------------------------------------------------------------ #
#  Optional dependency: sentence-transformers + numpy + sklearn
# ------------------------------------------------------------------ #
_HAS_EMBEDDINGS = False
try:
    import numpy as np
    from sklearn.metrics.pairwise import cosine_similarity
    _HAS_EMBEDDINGS = True
except ImportError:
    pass


class SemanticMatcher:
    """
    Semantic matching engine.

    When sentence-transformers + numpy + sklearn are installed, uses
    BERT-based dense vector embeddings (all-MiniLM-L6-v2) + cosine similarity
    for deep semantic matching.

    Otherwise falls back to a pure-Python keyword + character n-gram
    similarity (fast, reasonable accuracy).
    """

    _MODEL_NAME = "all-MiniLM-L6-v2"

    def __init__(self, model_name: str = _MODEL_NAME, lazy_load: bool = False):
        self._model_name = model_name
        self._model = None
        self._load_error = None
        if not lazy_load and _HAS_EMBEDDINGS:
            self._load_model()

    # ------------------------------------------------------------------ #
    #  Public API
    # ------------------------------------------------------------------ #

    def match_cv_to_job(
        self,
        cv_result: CVParseResult,
        job: Job,
        threshold: Optional[float] = None,
    ) -> MatchResult:
        """Match parsed CV against a job posting.  See module docstring."""
        threshold = threshold if threshold is not None else job.matching_threshold

        # -- Skill overlap (60% weight — dominant factor) --------------- #
        cv_skills_lower = {s.lower().strip() for s in cv_result.skills}
        job_skills_lower = {s.lower().strip() for s in job.required_skills}

        matching_skills = list(cv_skills_lower & job_skills_lower)
        missing_skills = list(job_skills_lower - cv_skills_lower)

        if job_skills_lower:
            skill_ratio = len(matching_skills) / len(job_skills_lower)
        else:
            skill_ratio = 0.0
        skill_score = skill_ratio * 60.0

        # -- Cosine similarity via BERT (10% weight — minor adjustment) -- #
        cos_sim = self._compute_similarity(cv_result, job)
        bert_score = cos_sim * 10.0

        # Penalty: when skill overlap is very low, BERT shouldn't inflate score
        if skill_ratio < 0.3 and cos_sim > 0.3:
            bert_score *= 0.4

        # -- Experience match (15% weight) ------------------------------ #
        yr = cv_result.years_of_experience
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

        # -- Education (10% weight) ------------------------------------- #
        if cv_result.education:
            edu_lower = cv_result.education.lower()
            if any(kw in edu_lower for kw in ["phd", "ph.d.", "doctorate"]):
                edu_score = 10.0
            elif any(kw in edu_lower for kw in ["master", "m.s.", "m.a.", "m.tech"]):
                edu_score = 8.0
            elif any(kw in edu_lower for kw in ["bachelor", "b.s.", "b.a.", "b.tech", "b.e."]):
                edu_score = 6.0
            else:
                edu_score = 4.0
        else:
            edu_score = 0.0

        # -- Certifications + GPA + Projects (5% weight) --------------- #
        gpa_match_bool = cv_result.gpa >= 2.5
        gpa_bonus = 1.5 if cv_result.gpa >= 3.5 else (1.0 if cv_result.gpa >= 2.5 else 0.0)
        cert_bonus = min(len(cv_result.certifications) * 1.0, 2.0)
        proj_bonus = min(len(cv_result.projects) * 0.5, 1.5)
        extra = gpa_bonus + cert_bonus + proj_bonus

        # -- Final composite (0-100) ------------------------------------ #
        total = skill_score + bert_score + exp_score + edu_score + extra
        total = min(max(total, 0.0), 100.0)

        recs = []
        if missing_skills:
            recs.append(f"Consider learning: {', '.join(missing_skills[:3])}")
        if not cv_result.certifications:
            recs.append("Add relevant certifications")
        if cv_result.gpa > 0 and cv_result.gpa < 2.5:
            recs.append("GPA below 2.5 threshold")
        if cos_sim < 0.3 and skill_ratio < 0.3:
            recs.append("Profile needs significant upskilling for this role")

        return MatchResult(
            job_id=job.job_id,
            job_title=job.title,
            company_name=job.company_name,
            match_score=round(total, 2),
            meets_threshold=total >= threshold,
            matching_skills=matching_skills,
            missing_skills=missing_skills,
            experience_match=cv_result.years_of_experience >= 1.0,
            gpa_match=gpa_match_bool,
            cosine_similarity=round(cos_sim, 4),
            recommendations=recs,
            detailed_analysis=(
                f"Skills: {skill_score:.0f}/60 | BERT: {bert_score:.0f}/10 | "
                f"Exp: {exp_score:.0f}/15 | Edu: {edu_score:.0f}/10 | "
                f"Extra: {extra:.0f}/5"
            ),
        )

    def match_cv_to_jobs(
        self,
        cv_result: CVParseResult,
        jobs: List[Job],
        min_score: float = 0.0,
    ) -> List[MatchResult]:
        """Match a single CV against multiple jobs."""
        results = [self.match_cv_to_job(cv_result, j) for j in jobs]
        results.sort(key=lambda r: r.match_score, reverse=True)
        if min_score > 0:
            results = [r for r in results if r.match_score >= min_score]
        return results

    def batch_match(
        self, cv_results: List[CVParseResult], jobs: List[Job],
        min_score: float = 0.0,
    ) -> List[List[MatchResult]]:
        return [self.match_cv_to_jobs(cv, jobs, min_score) for cv in cv_results]

    # ------------------------------------------------------------------ #
    #  Similarity computation
    # ------------------------------------------------------------------ #

    def _compute_similarity(self, cv: CVParseResult, job: Job) -> float:
        """Cosine similarity between CV and job text."""
        cv_text = self._build_cv_text(cv)
        job_text = self._build_job_text(job)

        if _HAS_EMBEDDINGS and self._model is not None:
            return self._embedding_similarity(cv_text, job_text)
        else:
            return self._fallback_similarity(cv_text, job_text)

    def _build_cv_text(self, cv: CVParseResult) -> str:
        parts = [
            f"Skills: {', '.join(cv.skills)}",
            f"Experience: {cv.experience[:500]}",
            f"Education: {cv.education[:300]}",
            f"Certifications: {', '.join(cv.certifications)}",
            f"Projects: {', '.join(cv.projects)}",
        ]
        return preprocess_for_embedding(" ".join(parts))

    def _build_job_text(self, job: Job) -> str:
        parts = [
            f"Title: {job.title}",
            f"Description: {job.description}",
            f"Required Skills: {', '.join(job.required_skills)}",
            f"Requirements: {', '.join(job.requirements)}",
            f"Qualifications: {', '.join(job.qualifications)}",
        ]
        return preprocess_for_embedding(" ".join(parts))

    # ------------------------------------------------------------------ #
    #  Embedding-based (requires sentence-transformers + numpy + sklearn)
    # ------------------------------------------------------------------ #

    def _embedding_similarity(self, text_a: str, text_b: str) -> float:
        try:
            if self._model is None:
                self._load_model()
            if self._model is None:
                return self._fallback_similarity(text_a, text_b)
            emb_a = self._model.encode([text_a], normalize_embeddings=True)
            emb_b = self._model.encode([text_b], normalize_embeddings=True)
            sim = cosine_similarity(emb_a, emb_b)[0][0]
            return float(np.clip(sim, 0.0, 1.0))
        except Exception:
            return self._fallback_similarity(text_a, text_b)

    @property
    def using_bert(self) -> bool:
        """Whether BERT embeddings (sentence-transformers) are active."""
        return _HAS_EMBEDDINGS and self._model is not None

    def _load_model(self):
        try:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(self._model_name)
        except Exception as e:
            self._load_error = str(e)
            self._model = None

    # ------------------------------------------------------------------ #
    #  Pure-Python fallback (n-gram overlap + keyword overlap)
    # ------------------------------------------------------------------ #

    @staticmethod
    def _fallback_similarity(text_a: str, text_b: str) -> float:
        """
        Character n-gram cosine similarity (no external packages).

        Uses character bigram and trigram overlap as a simple
        semantic proxy.  Fast and dependency-free.
        """
        if not text_a or not text_b:
            return 0.0

        def _ngrams(t: str, n: int) -> dict:
            d = {}
            for i in range(len(t) - n + 1):
                gram = t[i:i + n]
                d[gram] = d.get(gram, 0) + 1
            return d

        def _cosine(d1: dict, d2: dict) -> float:
            dot = 0.0
            n1 = n2 = 0.0
            for k, v in d1.items():
                n1 += v * v
                if k in d2:
                    dot += v * d2[k]
            for v in d2.values():
                n2 += v * v
            if n1 == 0 or n2 == 0:
                return 0.0
            return dot / (math.sqrt(n1) * math.sqrt(n2))

        bigram_sim = _cosine(_ngrams(text_a.lower(), 2),
                             _ngrams(text_b.lower(), 2))
        trigram_sim = _cosine(_ngrams(text_a.lower(), 3),
                              _ngrams(text_b.lower(), 3))

        # Weighted: 40% bigram, 60% trigram
        return bigram_sim * 0.4 + trigram_sim * 0.6
