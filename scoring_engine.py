"""
engines/scoring_engine.py - Resume Match Scoring Engine

Computes a 0–100 match score for each job listing against the resume profile.

Score Breakdown:
  - Role Match      (30 pts): How well the job title matches target roles
  - Skill Match     (30 pts): Overlap between job requirements and resume skills
  - Tool Match      (20 pts): Design tools mentioned in job vs resume tools
  - Experience Match(10 pts): Years of experience alignment
  - Domain Match    (10 pts): Industry/domain overlap

Final score is weighted sum, clamped to [0, 100].
"""

import re
import logging
from typing import Dict, List, Tuple
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import (
    RESUME_PROFILE,
    ALL_RESUME_KEYWORDS,
    HIGH_WEIGHT_KEYWORDS,
    MEDIUM_WEIGHT_KEYWORDS,
)

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# SCORING WEIGHTS
# ─────────────────────────────────────────────────────────────────────────────
WEIGHTS = {
    "role_match": 0.30,
    "skill_match": 0.30,
    "tool_match": 0.20,
    "experience_match": 0.10,
    "domain_match": 0.10,
}

# Role keywords with their match strength
ROLE_KEYWORDS = {
    # Exact / near-exact matches → high score
    "high": [
        "ui/ux designer", "ui ux designer", "uiux designer",
        "ux designer", "ui designer", "product designer",
        "senior ux designer", "senior ui designer", "senior ui/ux",
        "lead ux designer", "lead ui designer",
        "interaction designer", "experience designer",
        "user experience designer", "user interface designer",
    ],
    # Good matches
    "medium": [
        "ux researcher", "ui researcher", "ux consultant",
        "visual designer", "web designer", "digital designer",
        "design lead", "design system designer", "ux strategist",
        "mobile app designer", "responsive web designer",
        "product experience designer", "human-centered designer",
        "user experience specialist", "user interface specialist",
        "design consultant", "creative designer",
    ],
    # Partial matches
    "low": [
        "designer", "ux", "ui", "product design", "design",
        "creative", "visual", "interface", "experience",
    ],
}

# Experience level keywords
EXPERIENCE_KEYWORDS = {
    "senior": ["senior", "sr.", "lead", "principal", "staff", "head of"],
    "mid": ["mid", "mid-level", "intermediate", "associate"],
    "junior": ["junior", "jr.", "entry", "fresher", "trainee", "intern"],
}


# ─────────────────────────────────────────────────────────────────────────────
# SCORING ENGINE CLASS
# ─────────────────────────────────────────────────────────────────────────────
class ScoringEngine:
    """
    Computes resume match scores for job listings.
    All scoring methods return values in [0, 100].
    """

    def __init__(self):
        self.resume = RESUME_PROFILE
        self.years_exp = self.resume.get("years_of_experience", 4)
        self._build_keyword_sets()
        logger.debug("ScoringEngine initialized.")

    def _build_keyword_sets(self):
        """Pre-build lowercase keyword sets for fast matching."""
        self.skill_keywords = set(
            kw.lower() for kw in (
                self.resume.get("core_skills", [])
                + self.resume.get("research_methods", [])
                + self.resume.get("standards", [])
                + self.resume.get("industry_keywords", [])
            )
        )
        self.tool_keywords = set(
            kw.lower() for kw in (
                self.resume.get("design_tools", [])
                + self.resume.get("ai_tools", [])
                + self.resume.get("frontend_skills", [])
            )
        )
        self.domain_keywords = set(
            kw.lower() for kw in self.resume.get("domains", [])
        )
        self.target_roles = set(
            kw.lower() for kw in self.resume.get("target_role_keywords", [])
        )

    # ── Text Normalization ────────────────────────────────────────────────────

    @staticmethod
    def _normalize(text: str) -> str:
        """Lowercase, remove special chars, normalize whitespace."""
        if not text:
            return ""
        text = text.lower()
        text = re.sub(r"[^\w\s/]", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        return text

    @staticmethod
    def _tokenize(text: str) -> List[str]:
        """Split text into tokens (words and bigrams)."""
        words = text.lower().split()
        tokens = list(words)
        # Add bigrams
        for i in range(len(words) - 1):
            tokens.append(f"{words[i]} {words[i+1]}")
        # Add trigrams for role matching
        for i in range(len(words) - 2):
            tokens.append(f"{words[i]} {words[i+1]} {words[i+2]}")
        return tokens

    # ── Component Scores ──────────────────────────────────────────────────────

    def _score_role_match(self, title: str, description: str = "") -> float:
        """
        Score how well the job title matches target roles.
        Returns 0–100.
        """
        if not title:
            return 0.0

        title_norm = self._normalize(title)
        desc_norm = self._normalize(description or "")
        combined = title_norm + " " + desc_norm[:500]  # Use first 500 chars of desc

        score = 0.0

        # Check high-value role matches in title (most important)
        for role in ROLE_KEYWORDS["high"]:
            if role in title_norm:
                score = max(score, 95.0)
                break

        # Check medium role matches in title
        if score < 80:
            for role in ROLE_KEYWORDS["medium"]:
                if role in title_norm:
                    score = max(score, 75.0)
                    break

        # Check low-value matches in title
        if score < 60:
            for role in ROLE_KEYWORDS["low"]:
                if role in title_norm:
                    score = max(score, 55.0)
                    break

        # Boost if role keywords appear in description too
        if score > 0 and desc_norm:
            for role in ROLE_KEYWORDS["high"]:
                if role in desc_norm:
                    score = min(100.0, score + 5.0)
                    break

        # Penalty for clearly wrong roles
        wrong_roles = [
            "software engineer", "data scientist", "backend developer",
            "frontend developer", "devops", "qa engineer", "project manager",
            "business analyst", "marketing manager", "sales",
        ]
        for wrong in wrong_roles:
            if wrong in title_norm:
                score = max(0.0, score - 30.0)
                break

        return min(100.0, score)

    def _score_skill_match(self, description: str) -> float:
        """
        Score skill overlap between job description and resume skills.
        Returns 0–100.
        """
        if not description:
            return 50.0  # Neutral if no description

        desc_norm = self._normalize(description)
        tokens = set(self._tokenize(desc_norm))

        # Count high-weight keyword matches
        high_matches = sum(
            1 for kw in HIGH_WEIGHT_KEYWORDS if kw in desc_norm
        )
        # Count medium-weight keyword matches
        medium_matches = sum(
            1 for kw in MEDIUM_WEIGHT_KEYWORDS if kw in desc_norm
        )
        # Count general skill matches
        skill_matches = sum(
            1 for kw in self.skill_keywords
            if kw in desc_norm and len(kw) > 3
        )

        # Weighted scoring
        # High: 4 pts each (max ~40), Medium: 2 pts each (max ~20), General: 1 pt each
        raw_score = (high_matches * 4) + (medium_matches * 2) + (skill_matches * 1)

        # Normalize to 0–100 (cap at 100)
        # Assume 20 high matches = perfect score
        normalized = min(100.0, (raw_score / 80.0) * 100.0)

        # Minimum score if any design-related keywords found
        if high_matches >= 1:
            normalized = max(normalized, 40.0)
        if high_matches >= 3:
            normalized = max(normalized, 60.0)
        if high_matches >= 5:
            normalized = max(normalized, 75.0)

        return normalized

    def _score_tool_match(self, description: str) -> float:
        """
        Score design tool overlap between job and resume.
        Returns 0–100.
        """
        if not description:
            return 50.0

        desc_norm = self._normalize(description)

        # Primary tools (Figma is most important)
        primary_tools = ["figma", "adobe xd", "sketch", "invision", "zeplin"]
        secondary_tools = ["miro", "balsamiq", "maze", "photoshop", "illustrator",
                           "indesign", "usertesting", "stitch", "figma ai", "relume"]

        primary_matches = sum(1 for t in primary_tools if t in desc_norm)
        secondary_matches = sum(1 for t in secondary_tools if t in desc_norm)

        # Figma is the most critical tool
        figma_bonus = 20.0 if "figma" in desc_norm else 0.0

        raw_score = figma_bonus + (primary_matches * 15) + (secondary_matches * 5)
        return min(100.0, raw_score)

    def _score_experience_match(self, title: str, description: str) -> float:
        """
        Score experience level alignment.
        Candidate has 4 years — best fit for mid/senior roles.
        Returns 0–100.
        """
        combined = self._normalize(f"{title} {description[:300]}")

        # Check for experience requirements in description
        exp_patterns = [
            (r"(\d+)\+?\s*years?\s+(?:of\s+)?experience", 1),
            (r"(\d+)\s*-\s*(\d+)\s*years?", 2),
        ]

        required_years = None
        for pattern, group_count in exp_patterns:
            match = re.search(pattern, combined)
            if match:
                try:
                    if group_count == 1:
                        required_years = int(match.group(1))
                    else:
                        # Take the lower bound of range
                        required_years = int(match.group(1))
                    break
                except (ValueError, IndexError):
                    pass

        if required_years is not None:
            diff = abs(self.years_exp - required_years)
            if diff == 0:
                return 100.0
            elif diff == 1:
                return 85.0
            elif diff == 2:
                return 70.0
            elif diff <= 4:
                return 50.0
            else:
                return 20.0

        # Check seniority level keywords
        for level, keywords in EXPERIENCE_KEYWORDS.items():
            for kw in keywords:
                if kw in combined:
                    if level == "senior" and self.years_exp >= 3:
                        return 85.0
                    elif level == "mid" and 2 <= self.years_exp <= 5:
                        return 90.0
                    elif level == "junior" and self.years_exp <= 2:
                        return 90.0
                    elif level == "junior" and self.years_exp > 2:
                        return 40.0  # Overqualified
                    elif level == "senior" and self.years_exp < 3:
                        return 50.0  # Under-qualified

        # No experience info found — neutral score
        return 75.0

    def _score_domain_match(self, description: str) -> float:
        """
        Score domain/industry overlap.
        Returns 0–100.
        """
        if not description:
            return 50.0

        desc_norm = self._normalize(description)

        # High-value domain matches for this candidate
        high_domains = [
            "healthtech", "health tech", "healthcare", "ehr", "electronic health",
            "hrms", "hr management", "fintech", "fin tech", "saas", "b2b",
            "enterprise", "edtech", "e-commerce", "ecommerce",
        ]
        medium_domains = [
            "startup", "product", "mobile", "web", "digital", "platform",
            "application", "software", "technology", "tech",
        ]

        high_matches = sum(1 for d in high_domains if d in desc_norm)
        medium_matches = sum(1 for d in medium_domains if d in desc_norm)

        raw_score = (high_matches * 20) + (medium_matches * 5)
        return min(100.0, max(40.0, raw_score))  # Minimum 40 (domain-agnostic roles are fine)

    # ── Main Scoring Method ───────────────────────────────────────────────────

    def compute_score(self, job: Dict) -> Dict:
        """
        Compute the full match score for a job listing.

        Args:
            job: Dict with keys: title, company, description, location

        Returns:
            job dict updated with:
                match_score: float (0–100)
                role_match: float
                skill_match: float
                tool_match: float
                experience_match: float
                domain_match: float
                score_breakdown: str
        """
        title = job.get("title", "")
        description = job.get("description", "")
        location = job.get("location", "")

        # Compute component scores
        role_score = self._score_role_match(title, description)
        skill_score = self._score_skill_match(description)
        tool_score = self._score_tool_match(description)
        exp_score = self._score_experience_match(title, description)
        domain_score = self._score_domain_match(description)

        # Location bonus
        location_bonus = 0.0
        if location:
            loc_lower = location.lower()
            for preferred_loc in ["hyderabad", "bangalore", "remote", "bengaluru"]:
                if preferred_loc in loc_lower:
                    location_bonus = 3.0
                    break

        # Weighted final score
        weighted_score = (
            role_score * WEIGHTS["role_match"]
            + skill_score * WEIGHTS["skill_match"]
            + tool_score * WEIGHTS["tool_match"]
            + exp_score * WEIGHTS["experience_match"]
            + domain_score * WEIGHTS["domain_match"]
        )

        final_score = min(100.0, weighted_score + location_bonus)

        # Round to 1 decimal
        final_score = round(final_score, 1)
        role_score = round(role_score, 1)
        skill_score = round(skill_score, 1)
        tool_score = round(tool_score, 1)
        exp_score = round(exp_score, 1)
        domain_score = round(domain_score, 1)

        result = dict(job)
        result.update({
            "match_score": final_score,
            "role_match": role_score,
            "skill_match": skill_score,
            "tool_match": tool_score,
            "experience_match": exp_score,
            "domain_match": domain_score,
            "score_breakdown": (
                f"Role:{role_score} Skill:{skill_score} "
                f"Tool:{tool_score} Exp:{exp_score} Domain:{domain_score}"
            ),
        })

        logger.debug(
            f"Score for '{title}' @ '{job.get('company', '')}': "
            f"{final_score}% [{result['score_breakdown']}]"
        )
        return result

    def score_batch(self, jobs: List[Dict]) -> List[Dict]:
        """Score a list of jobs and return sorted by match_score DESC."""
        scored = []
        for job in jobs:
            try:
                scored.append(self.compute_score(job))
            except Exception as e:
                logger.error(f"Scoring error for job '{job.get('title', '?')}': {e}")
                job["match_score"] = 0.0
                scored.append(job)

        # Sort by match_score descending
        scored.sort(key=lambda j: j.get("match_score", 0), reverse=True)
        return scored

    def get_score_color(self, score: float) -> str:
        """Return CSS color class based on score."""
        if score >= 90:
            return "score-green"
        elif score >= 80:
            return "score-blue"
        elif score >= 70:
            return "score-orange"
        else:
            return "score-hidden"

    def get_score_label(self, score: float) -> str:
        """Return human-readable score label."""
        if score >= 90:
            return "Excellent Match"
        elif score >= 80:
            return "Strong Match"
        elif score >= 70:
            return "Good Match"
        else:
            return "Weak Match"
