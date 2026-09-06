"""
test_validation.py - Comprehensive validation & health-check test suite
for the UI/UX Job Search Automation System.

Tests every module for:
  - Import health
  - Class instantiation
  - Core method correctness
  - Edge-case handling
  - Integration between components

Run with:
    python test_validation.py
"""

import sys
import os
import json
import sqlite3
import hashlib
import tempfile
import traceback
from datetime import datetime, timedelta
from typing import List, Dict

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

# ─────────────────────────────────────────────────────────────────────────────
# MINI TEST RUNNER
# ─────────────────────────────────────────────────────────────────────────────

class TestRunner:
    def __init__(self):
        self.results: List[tuple] = []
        self.passed = self.failed = self.errors = 0

    def run(self, name: str, func):
        try:
            func()
            self.results.append(("PASS", name, ""))
            self.passed += 1
        except AssertionError as e:
            self.results.append(("FAIL", name, str(e)))
            self.failed += 1
        except Exception as e:
            tb = traceback.format_exc().strip().splitlines()[-1]
            self.results.append(("ERROR", name, f"{type(e).__name__}: {e}  [{tb}]"))
            self.errors += 1

    def report(self) -> bool:
        print("\n" + "=" * 72)
        print("  UI/UX JOB SEARCH — VALIDATION TEST REPORT")
        print(f"  Run at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 72)

        sections = {}
        for status, name, msg in self.results:
            section = name.split(":")[0].strip()
            sections.setdefault(section, []).append((status, name, msg))

        for section, items in sections.items():
            sec_pass = sum(1 for s, _, _ in items if s == "PASS")
            sec_total = len(items)
            print(f"\n  ── {section} ({sec_pass}/{sec_total}) ──")
            for status, name, msg in items:
                icon = "✅" if status == "PASS" else ("❌" if status == "FAIL" else "💥")
                label = name.split(":", 1)[1].strip() if ":" in name else name
                print(f"    {icon} {label}")
                if msg:
                    print(f"         → {msg}")

        total = self.passed + self.failed + self.errors
        print("\n" + "=" * 72)
        print(f"  TOTAL: {total}  |  ✅ PASSED: {self.passed}  |  "
              f"❌ FAILED: {self.failed}  |  💥 ERRORS: {self.errors}")
        print("=" * 72)
        return self.failed == 0 and self.errors == 0


T = TestRunner()

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 1 — IMPORTS
# ─────────────────────────────────────────────────────────────────────────────

def _test_import_config():
    import config
    for attr in ["DB_PATH", "LOGS_DIR", "DASHBOARD_FILE", "LOG_FILE",
                 "MIN_MATCH_SCORE", "MAX_WORKERS", "REQUEST_TIMEOUT",
                 "MAX_RETRIES", "RETRY_DELAY", "RATE_LIMIT_DELAY",
                 "SEARCH_LOCATIONS", "TARGET_ROLES", "SEARCH_KEYWORDS",
                 "USER_AGENTS", "DEFAULT_HEADERS", "SOURCE_PRIORITY",
                 "SCRAPER_URLS", "COMPANY_CAREER_PAGES",
                 "VALID_HTTP_CODES", "INVALID_HTTP_CODES",
                 "LOGIN_REDIRECT_PATTERNS", "EXPIRED_PATTERNS"]:
        assert hasattr(config, attr), f"config missing attribute: {attr}"
    assert isinstance(config.MIN_MATCH_SCORE, (int, float))
    assert 0 < config.MIN_MATCH_SCORE <= 100
    assert isinstance(config.USER_AGENTS, list) and len(config.USER_AGENTS) > 0

T.run("Imports: config.py", _test_import_config)


def _test_import_resume_data():
    from resume_data import (RESUME_PROFILE, ALL_RESUME_KEYWORDS,
                              HIGH_WEIGHT_KEYWORDS, MEDIUM_WEIGHT_KEYWORDS)
    assert isinstance(RESUME_PROFILE, dict)
    for key in ["name", "title", "years_of_experience", "core_skills",
                "design_tools", "ai_tools", "frontend_skills", "standards",
                "research_methods", "domains", "industry_keywords",
                "target_role_keywords"]:
        assert key in RESUME_PROFILE, f"RESUME_PROFILE missing key: {key}"
    assert isinstance(ALL_RESUME_KEYWORDS, list) and len(ALL_RESUME_KEYWORDS) > 0
    assert isinstance(HIGH_WEIGHT_KEYWORDS, list) and len(HIGH_WEIGHT_KEYWORDS) > 0
    assert isinstance(MEDIUM_WEIGHT_KEYWORDS, list) and len(MEDIUM_WEIGHT_KEYWORDS) > 0
    assert "figma" in HIGH_WEIGHT_KEYWORDS

T.run("Imports: resume_data.py", _test_import_resume_data)


def _test_import_db_manager():
    from database.db_manager import DatabaseManager, SCHEMA_SQL
    assert DatabaseManager is not None
    assert "CREATE TABLE IF NOT EXISTS jobs" in SCHEMA_SQL
    assert "CREATE TABLE IF NOT EXISTS run_history" in SCHEMA_SQL

T.run("Imports: database/db_manager.py", _test_import_db_manager)


def _test_import_link_validator():
    from validators.link_validator import (LinkValidator,
                                            STATUS_VALID, STATUS_INVALID,
                                            STATUS_EXPIRED, STATUS_PENDING)
    assert LinkValidator is not None
    assert STATUS_VALID == "VALID"
    assert STATUS_INVALID == "INVALID"
    assert STATUS_EXPIRED == "EXPIRED"

T.run("Imports: validators/link_validator.py", _test_import_link_validator)


def _test_import_scoring_engine():
    from engines.scoring_engine import ScoringEngine, WEIGHTS, ROLE_KEYWORDS
    assert ScoringEngine is not None
    assert abs(sum(WEIGHTS.values()) - 1.0) < 1e-9, \
        f"Weights must sum to 1.0, got {sum(WEIGHTS.values())}"
    assert "high" in ROLE_KEYWORDS and "medium" in ROLE_KEYWORDS

T.run("Imports: engines/scoring_engine.py", _test_import_scoring_engine)


def _test_import_dashboard_generator():
    from output.dashboard_generator import DashboardGenerator
    assert DashboardGenerator is not None

T.run("Imports: output/dashboard_generator.py", _test_import_dashboard_generator)


def _test_import_base_scraper():
    from scrapers.base_scraper import BaseScraper
    assert BaseScraper is not None

T.run("Imports: scrapers/base_scraper.py", _test_import_base_scraper)


def _test_import_naukri():
    from scrapers.naukri_scraper import NaukriScraper
    assert NaukriScraper.SOURCE_NAME == "Naukri"

T.run("Imports: scrapers/naukri_scraper.py", _test_import_naukri)


def _test_import_linkedin():
    from scrapers.linkedin_scraper import LinkedInScraper
    assert LinkedInScraper.SOURCE_NAME == "LinkedIn"

T.run("Imports: scrapers/linkedin_scraper.py", _test_import_linkedin)


def _test_import_indeed():
    from scrapers.indeed_scraper import IndeedScraper
    assert IndeedScraper.SOURCE_NAME == "Indeed"

T.run("Imports: scrapers/indeed_scraper.py", _test_import_indeed)


def _test_import_foundit():
    from scrapers.foundit_scraper import FounditScraper
    assert FounditScraper.SOURCE_NAME == "Foundit"

T.run("Imports: scrapers/foundit_scraper.py", _test_import_foundit)


def _test_import_glassdoor():
    from scrapers.glassdoor_scraper import GlassdoorScraper
    assert GlassdoorScraper.SOURCE_NAME == "Glassdoor"

T.run("Imports: scrapers/glassdoor_scraper.py", _test_import_glassdoor)


def _test_import_wellfound():
    from scrapers.wellfound_scraper import WellfoundScraper
    assert WellfoundScraper.SOURCE_NAME == "Wellfound"

T.run("Imports: scrapers/wellfound_scraper.py", _test_import_wellfound)


def _test_import_instahyre():
    from scrapers.instahyre_scraper import InstahyreScraper
    assert InstahyreScraper.SOURCE_NAME == "Instahyre"

T.run("Imports: scrapers/instahyre_scraper.py", _test_import_instahyre)


def _test_import_company_pages():
    from scrapers.company_pages_scraper import CompanyPagesScraper, _is_design_job
    assert CompanyPagesScraper.SOURCE_NAME == "Company Career Pages"
    assert _is_design_job("UI/UX Designer") is True
    assert _is_design_job("Software Engineer") is False

T.run("Imports: scrapers/company_pages_scraper.py", _test_import_company_pages)


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 2 — DATABASE MANAGER
# ─────────────────────────────────────────────────────────────────────────────

def _make_tmp_db():
    """Helper: create a temp DB and return (db, tmp_path)."""
    from database.db_manager import DatabaseManager
    fd, tmp_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    os.unlink(tmp_path)          # let DatabaseManager create it fresh
    db = DatabaseManager(db_path=tmp_path)
    return db, tmp_path


def _sample_job(job_id="test_001", title="UX Designer", company="TestCo",
                url="https://example.com/job/001", score=85.0,
                posted_date=None):
    today = posted_date or datetime.now().strftime("%Y-%m-%d")
    return {
        "job_id": job_id, "title": title, "company": company,
        "location": "Hyderabad", "url": url,
        "apply_url": url, "source": "Test",
        "posted_date": today, "posted_date_raw": "today",
        "description": "Figma user research usability testing wireframing",
        "match_score": score, "skill_match": 80.0, "role_match": 90.0,
        "experience_match": 85.0, "tool_match": 75.0, "domain_match": 70.0,
        "score_breakdown": "Role:90 Skill:80 Tool:75 Exp:85 Domain:70",
        "validation_status": "VALID", "http_status_code": 200,
    }


def _test_db_init():
    db, tmp = _make_tmp_db()
    try:
        assert os.path.exists(tmp)
        conn = sqlite3.connect(tmp)
        tables = {r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
        conn.close()
        assert "jobs" in tables
        assert "job_history" in tables
        assert "run_history" in tables
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)

T.run("Database: Schema creation (jobs / job_history / run_history)", _test_db_init)


def _test_db_run_lifecycle():
    db, tmp = _make_tmp_db()
    try:
        run_id = db.start_run()
        assert isinstance(run_id, int) and run_id > 0, \
            f"start_run() should return positive int, got {run_id}"

        stats = {"jobs_crawled": 10, "jobs_validated": 8, "jobs_rejected": 2,
                 "duplicates_removed": 1, "expired_rejected": 0,
                 "new_jobs_added": 7, "errors": 0}
        db.finish_run(run_id, stats)

        last = db.get_last_run_stats()
        assert last is not None, "get_last_run_stats() returned None"
        assert last["jobs_crawled"] == 10
        assert last["status"] == "COMPLETED"
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)

T.run("Database: Run lifecycle (start / finish / get_last_run_stats)", _test_db_run_lifecycle)


def _test_db_insert_and_query():
    db, tmp = _make_tmp_db()
    try:
        run_id = db.start_run()
        job = _sample_job()
        result = db.insert_job(job, run_id)
        assert result is True, "insert_job should return True"

        count = db.get_total_job_count()
        assert count == 1, f"Expected 1 job, got {count}"

        urls = db.get_existing_urls()
        assert "https://example.com/job/001" in urls

        ids = db.get_existing_job_ids()
        assert "test_001" in ids

        jobs = db.get_jobs_for_dashboard(min_score=70.0)
        assert len(jobs) == 1
        assert jobs[0]["title"] == "UX Designer"
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)

T.run("Database: Insert job and query (get_jobs_for_dashboard)", _test_db_insert_and_query)


def _test_db_duplicate_detection():
    db, tmp = _make_tmp_db()
    try:
        run_id = db.start_run()
        job = _sample_job()
        db.insert_job(job, run_id)

        # is_duplicate by job_id
        assert db.is_duplicate("test_001", "https://other.com") is True
        # is_duplicate by URL
        assert db.is_duplicate("other_id", "https://example.com/job/001") is True
        # not a duplicate
        assert db.is_duplicate("other_id", "https://other.com") is False

        # INSERT OR IGNORE — second insert should not raise
        result2 = db.insert_job(job, run_id)
        assert result2 is True          # no exception
        assert db.get_total_job_count() == 1  # still only 1 row
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)

T.run("Database: Duplicate detection (job_id and URL)", _test_db_duplicate_detection)


def _test_db_mark_old_jobs():
    db, tmp = _make_tmp_db()
    try:
        run_id1 = db.start_run()
        db.insert_job(_sample_job("j1", url="https://example.com/1"), run_id1)

        run_id2 = db.start_run()
        db.insert_job(_sample_job("j2", url="https://example.com/2"), run_id2)

        db.mark_old_jobs_not_new(run_id2)

        conn = sqlite3.connect(tmp)
        rows = {r[0]: r[1] for r in conn.execute(
            "SELECT job_id, is_new FROM jobs").fetchall()}
        conn.close()
        assert rows["j1"] == 0, "j1 from run1 should be marked not-new"
        assert rows["j2"] == 1, "j2 from run2 should still be new"
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)

T.run("Database: mark_old_jobs_not_new", _test_db_mark_old_jobs)


def _test_db_cleanup():
    db, tmp = _make_tmp_db()
    try:
        run_id = db.start_run()
        old_date = (datetime.now() - timedelta(days=35)).strftime("%Y-%m-%d")
        db.insert_job(_sample_job("old_j", url="https://example.com/old",
                                  posted_date=old_date), run_id)
        assert db.get_total_job_count() == 1

        db.cleanup_old_jobs(days=30)
        assert db.get_total_job_count() == 0, "Old job should be removed"
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)

T.run("Database: cleanup_old_jobs (removes jobs > N days)", _test_db_cleanup)


def _test_db_get_run_statistics():
    db, tmp = _make_tmp_db()
    try:
        run_id = db.start_run()
        stats = {"jobs_crawled": 5, "jobs_validated": 4, "jobs_rejected": 1,
                 "duplicates_removed": 0, "expired_rejected": 0,
                 "new_jobs_added": 4, "errors": 0}
        db.finish_run(run_id, stats)
        run_stats = db.get_run_statistics(run_id)
        assert run_stats["jobs_crawled"] == 5
        assert run_stats["status"] == "COMPLETED"
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)

T.run("Database: get_run_statistics by run_id", _test_db_get_run_statistics)


def _test_db_get_jobs_by_date_range():
    db, tmp = _make_tmp_db()
    try:
        run_id = db.start_run()
        today = datetime.now().strftime("%Y-%m-%d")
        old = (datetime.now() - timedelta(days=10)).strftime("%Y-%m-%d")
        db.insert_job(_sample_job("j_today", url="https://example.com/t",
                                  posted_date=today), run_id)
        db.insert_job(_sample_job("j_old", url="https://example.com/o",
                                  posted_date=old), run_id)
        jobs = db.get_jobs_by_date_range(days=7)
        assert len(jobs) == 1
        assert jobs[0]["job_id"] == "j_today"
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)

T.run("Database: get_jobs_by_date_range filters correctly", _test_db_get_jobs_by_date_range)


def _test_db_get_top_match_jobs():
    db, tmp = _make_tmp_db()
    try:
        run_id = db.start_run()
        db.insert_job(_sample_job("j_high", url="https://example.com/h", score=95.0), run_id)
        db.insert_job(_sample_job("j_low", url="https://example.com/l", score=72.0), run_id)
        top = db.get_top_match_jobs(min_score=90.0)
        assert len(top) == 1
        assert top[0]["job_id"] == "j_high"
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)

T.run("Database: get_top_match_jobs (min_score filter)", _test_db_get_top_match_jobs)


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 3 — SCORING ENGINE
# ─────────────────────────────────────────────────────────────────────────────

def _test_scoring_init():
    from engines.scoring_engine import ScoringEngine
    import config
    s = ScoringEngine()
    assert s.years_exp == config.RESUME_PROFILE.get("years_of_experience", 13)
    assert len(s.skill_keywords) > 0
    assert len(s.tool_keywords) > 0
    assert len(s.domain_keywords) > 0
    assert "figma" in s.tool_keywords

T.run("ScoringEngine: Initialization and keyword sets", _test_scoring_init)


def _test_scoring_role_match():
    from engines.scoring_engine import ScoringEngine
    s = ScoringEngine()

    # Exact high-value match
    score = s._score_role_match("Senior UI/UX Designer", "")
    assert score >= 90, f"'Senior UI/UX Designer' → expected ≥90, got {score}"

    # Medium match
    score = s._score_role_match("Visual Designer", "")
    assert score >= 70, f"'Visual Designer' → expected ≥70, got {score}"

    # Low match
    score = s._score_role_match("Designer", "")
    assert score >= 40, f"'Designer' → expected ≥40, got {score}"

    # Wrong role — penalty
    score = s._score_role_match("Software Engineer", "")
    assert score < 30, f"'Software Engineer' → expected <30, got {score}"

    # Empty title
    score = s._score_role_match("", "")
    assert score == 0.0, f"Empty title → expected 0, got {score}"

T.run("ScoringEngine: Role match (high/medium/low/wrong/empty)", _test_scoring_role_match)


def _test_scoring_skill_match():
    from engines.scoring_engine import ScoringEngine
    s = ScoringEngine()

    rich = ("Figma, user research, usability testing, wireframing, prototyping, "
            "design system, accessibility, WCAG, interaction design, heuristic evaluation")
    score = s._score_skill_match(rich)
    assert score >= 60, f"Rich description → expected ≥60, got {score}"

    # Empty → neutral 50
    score = s._score_skill_match("")
    assert score == 50.0, f"Empty description → expected 50, got {score}"

    # Unrelated
    score = s._score_skill_match("Python Java SQL backend microservices")
    assert score < 60, f"Unrelated description → expected <60, got {score}"

T.run("ScoringEngine: Skill match (rich/empty/unrelated)", _test_scoring_skill_match)


def _test_scoring_tool_match():
    from engines.scoring_engine import ScoringEngine
    s = ScoringEngine()

    score = s._score_tool_match("Must know Figma and Adobe XD for prototyping")
    assert score >= 35, f"Figma+AdobeXD → expected ≥35, got {score}"

    # Figma alone
    score = s._score_tool_match("Figma experience required")
    assert score >= 20, f"Figma alone → expected ≥20, got {score}"

    # No tools
    score = s._score_tool_match("General design experience required")
    assert score == 0.0, f"No tools → expected 0, got {score}"

    # Empty
    score = s._score_tool_match("")
    assert score == 50.0, f"Empty → expected 50, got {score}"

T.run("ScoringEngine: Tool match (Figma/no tools/empty)", _test_scoring_tool_match)


def _test_scoring_experience_match():
    from engines.scoring_engine import ScoringEngine
    s = ScoringEngine()

    # Exact match
    score = s._score_experience_match("UX Designer", f"{s.years_exp} years of experience required")
    assert score == 100.0, f"Exact match → expected 100, got {score}"

    # Close match
    score = s._score_experience_match("UX Designer", f"{max(1, s.years_exp - 1)} years of experience required")
    assert score >= 80, f"Close match → expected ≥80, got {score}"

    # Junior role — overqualified
    score = s._score_experience_match("Junior UX Designer", "entry level position")
    assert score <= 50, f"Junior role → expected ≤50, got {score}"

    # No experience info → neutral
    score = s._score_experience_match("UX Designer", "Design beautiful interfaces")
    assert score >= 70, f"No exp info → expected ≥70, got {score}"

T.run("ScoringEngine: Experience match (exact/close/junior/neutral)", _test_scoring_experience_match)


def _test_scoring_domain_match():
    from engines.scoring_engine import ScoringEngine
    s = ScoringEngine()

    # High domain match
    score = s._score_domain_match("Experience with healthtech EHR systems and HRMS")
    assert score >= 60, f"HealthTech/HRMS → expected ≥60, got {score}"

    # Medium domain
    score = s._score_domain_match("SaaS product for enterprise customers")
    assert score >= 40, f"SaaS enterprise → expected ≥40, got {score}"

    # Empty → neutral 50
    score = s._score_domain_match("")
    assert score == 50.0, f"Empty → expected 50, got {score}"

T.run("ScoringEngine: Domain match (healthtech/saas/empty)", _test_scoring_domain_match)


def _test_scoring_compute_score_full():
    from engines.scoring_engine import ScoringEngine
    s = ScoringEngine()

    job = {
        "title": "Senior UI/UX Designer",
        "company": "Razorpay",
        "location": "Hyderabad",
        "description": (
            "Senior UI/UX Designer needed. Skills: Figma, Adobe XD, user research, "
            "usability testing, wireframing, prototyping, design systems, "
            "accessibility WCAG 2.1, Agile/Scrum. 4+ years experience. "
            "Fintech B2B SaaS product."
        ),
    }
    result = s.compute_score(job)

    for key in ["match_score", "role_match", "skill_match", "tool_match",
                "experience_match", "domain_match", "score_breakdown"]:
        assert key in result, f"Missing key: {key}"

    assert 0 <= result["match_score"] <= 100
    assert result["match_score"] >= 70, \
        f"Strong UX job → expected ≥70, got {result['match_score']}"

    # All component scores in range
    for k in ["role_match", "skill_match", "tool_match", "experience_match", "domain_match"]:
        assert 0 <= result[k] <= 100, f"{k} out of range: {result[k]}"

T.run("ScoringEngine: compute_score full pipeline (all keys, range check)", _test_scoring_compute_score_full)


def _test_scoring_batch_sorted():
    from engines.scoring_engine import ScoringEngine
    s = ScoringEngine()

    jobs = [
        {"title": "Software Engineer", "company": "A", "location": "Hyderabad",
         "description": "Python Java SQL"},
        {"title": "Senior UI/UX Designer", "company": "B", "location": "Hyderabad",
         "description": "Figma user research usability testing design system WCAG"},
        {"title": "Product Designer", "company": "C", "location": "Remote",
         "description": "Figma prototyping wireframing interaction design"},
    ]
    scored = s.score_batch(jobs)
    assert len(scored) == 3
    scores = [j["match_score"] for j in scored]
    assert scores == sorted(scores, reverse=True), \
        f"score_batch output not sorted descending: {scores}"

T.run("ScoringEngine: score_batch returns sorted results", _test_scoring_batch_sorted)


def _test_scoring_labels_colors():
    from engines.scoring_engine import ScoringEngine
    s = ScoringEngine()

    assert s.get_score_label(95) == "Excellent Match"
    assert s.get_score_label(85) == "Strong Match"
    assert s.get_score_label(75) == "Good Match"
    assert s.get_score_label(60) == "Weak Match"

    assert s.get_score_color(95) == "score-green"
    assert s.get_score_color(85) == "score-blue"
    assert s.get_score_color(75) == "score-orange"
    assert s.get_score_color(60) == "score-hidden"

T.run("ScoringEngine: Score labels and color classes", _test_scoring_labels_colors)


def _test_scoring_normalize():
    from engines.scoring_engine import ScoringEngine
    # Commas/exclamations replaced by spaces, then whitespace collapsed → single spaces
    assert ScoringEngine._normalize("Hello, World! 123") == "hello world 123"
    assert ScoringEngine._normalize("") == ""
    assert ScoringEngine._normalize(None) == ""

T.run("ScoringEngine: Text normalization", _test_scoring_normalize)


def _test_scoring_tokenize():
    from engines.scoring_engine import ScoringEngine
    tokens = ScoringEngine._tokenize("ux designer figma")
    assert "ux" in tokens
    assert "designer" in tokens
    assert "ux designer" in tokens
    assert "designer figma" in tokens
    assert "ux designer figma" in tokens

T.run("ScoringEngine: Tokenizer (words + bigrams + trigrams)", _test_scoring_tokenize)


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 4 — BASE SCRAPER
# ─────────────────────────────────────────────────────────────────────────────

def _get_scraper():
    from scrapers.naukri_scraper import NaukriScraper
    return NaukriScraper()


def _test_scraper_date_today():
    s = _get_scraper()
    today = datetime.now().strftime("%Y-%m-%d")
    for raw in ["today", "just now", "2 hours ago", "30 minutes ago", "few hours ago"]:
        result = s._parse_posted_date(raw)
        assert result == today, f"'{raw}' → expected {today}, got {result}"

T.run("BaseScraper: Date parsing — today variants", _test_scraper_date_today)


def _test_scraper_date_yesterday():
    s = _get_scraper()
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    assert s._parse_posted_date("yesterday") == yesterday

T.run("BaseScraper: Date parsing — yesterday", _test_scraper_date_yesterday)


def _test_scraper_date_days_ago():
    s = _get_scraper()
    for days in [1, 2, 3, 5, 7]:
        expected = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        result = s._parse_posted_date(f"{days} days ago")
        assert result == expected, f"'{days} days ago' → expected {expected}, got {result}"

T.run("BaseScraper: Date parsing — X days ago", _test_scraper_date_days_ago)


def _test_scraper_date_too_old():
    s = _get_scraper()
    assert s._parse_posted_date("30 days ago") is None, "30 days ago should be None"
    assert s._parse_posted_date("2 months ago") is None, "2 months ago should be None"
    # MAX_DAYS_OLD=7: condition is days > 7, so 7 days is at boundary (included), 8+ is rejected
    assert s._parse_posted_date("8 days ago") is None, "8 days ago should be None"
    assert s._parse_posted_date("2 weeks ago") is None, "2 weeks ago (14 days) should be None"

T.run("BaseScraper: Date parsing — too old returns None", _test_scraper_date_too_old)


def _test_scraper_date_iso():
    s = _get_scraper()
    recent = (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d")
    assert s._parse_posted_date(recent) == recent

    old_iso = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    assert s._parse_posted_date(old_iso) is None

T.run("BaseScraper: Date parsing — ISO format (YYYY-MM-DD)", _test_scraper_date_iso)


def _test_scraper_date_slash_format():
    """DD/MM/YYYY and DD-MM-YYYY must both parse correctly."""
    s = _get_scraper()
    recent = datetime.now() - timedelta(days=2)

    slash = recent.strftime("%d/%m/%Y")
    result = s._parse_posted_date(slash)
    assert result == recent.strftime("%Y-%m-%d"), \
        f"DD/MM/YYYY '{slash}' → expected {recent.strftime('%Y-%m-%d')}, got {result}"

    dash = recent.strftime("%d-%m-%Y")
    result = s._parse_posted_date(dash)
    assert result == recent.strftime("%Y-%m-%d"), \
        f"DD-MM-YYYY '{dash}' → expected {recent.strftime('%Y-%m-%d')}, got {result}"

T.run("BaseScraper: Date parsing — DD/MM/YYYY and DD-MM-YYYY formats", _test_scraper_date_slash_format)


def _test_scraper_date_empty():
    s = _get_scraper()
    today = datetime.now().strftime("%Y-%m-%d")
    assert s._parse_posted_date("") == today
    assert s._parse_posted_date(None) == today

T.run("BaseScraper: Date parsing — empty/None defaults to today", _test_scraper_date_empty)


def _test_scraper_job_id():
    s = _get_scraper()
    jid = s._generate_job_id("UX Designer", "Razorpay", "https://example.com/1")
    assert isinstance(jid, str) and len(jid) == 16

    # Stable
    assert jid == s._generate_job_id("UX Designer", "Razorpay", "https://example.com/1")

    # Different inputs → different IDs
    jid2 = s._generate_job_id("UI Designer", "Razorpay", "https://example.com/2")
    assert jid != jid2

T.run("BaseScraper: Job ID generation (stable MD5 hash)", _test_scraper_job_id)


def _test_scraper_normalize_valid():
    s = _get_scraper()
    today = datetime.now().strftime("%Y-%m-%d")
    raw = {
        "title": "UX Designer", "company": "TestCo",
        "location": "Hyderabad", "url": "https://example.com/job/1",
        "apply_url": "https://example.com/job/1", "source": "Test",
        "posted_date_raw": "today", "description": "Test description",
    }
    job = s._normalize_job(raw)
    assert job is not None
    assert job["title"] == "UX Designer"
    assert job["posted_date"] == today
    assert "job_id" in job
    assert job["validation_status"] == "PENDING"
    assert len(job["description"]) <= 2000

T.run("BaseScraper: normalize_job — valid job", _test_scraper_normalize_valid)


def _test_scraper_normalize_invalid():
    s = _get_scraper()
    base = {"title": "UX Designer", "company": "TestCo",
            "url": "https://example.com/1", "posted_date_raw": "today"}

    # Missing title
    r = dict(base); r["title"] = ""
    assert s._normalize_job(r) is None, "Empty title should return None"

    # Missing company
    r = dict(base); r["company"] = ""
    assert s._normalize_job(r) is None, "Empty company should return None"

    # Missing URL
    r = dict(base); r["url"] = ""
    assert s._normalize_job(r) is None, "Empty URL should return None"

    # Bad URL scheme
    r = dict(base); r["url"] = "ftp://example.com/job"
    assert s._normalize_job(r) is None, "FTP URL should return None"

    # Too old
    r = dict(base); r["posted_date_raw"] = "30 days ago"
    assert s._normalize_job(r) is None, "30-day-old job should return None"

T.run("BaseScraper: normalize_job — invalid inputs return None", _test_scraper_normalize_invalid)


def _test_scraper_dedup():
    s = _get_scraper()
    s.set_existing_data(
        urls={"https://example.com/job/1"},
        job_ids={"job_001"}
    )
    assert s._is_duplicate("job_001", "https://other.com") is True   # ID match
    assert s._is_duplicate("other", "https://example.com/job/1") is True  # URL match
    assert s._is_duplicate("other", "https://other.com") is False    # no match

T.run("BaseScraper: Duplicate detection (URL and job_id)", _test_scraper_dedup)


def _test_scraper_filter_and_normalize():
    s = _get_scraper()
    raw_jobs = [
        {"title": "UX Designer", "company": "A", "url": "https://example.com/1",
         "posted_date_raw": "today", "description": ""},
        {"title": "UI Designer", "company": "B", "url": "https://example.com/2",
         "posted_date_raw": "today", "description": ""},
        {"title": "", "company": "C", "url": "https://example.com/3",
         "posted_date_raw": "today", "description": ""},          # no title
        {"title": "UX Designer", "company": "A", "url": "https://example.com/1",
         "posted_date_raw": "today", "description": ""},          # duplicate URL
        {"title": "Old Job", "company": "D", "url": "https://example.com/4",
         "posted_date_raw": "30 days ago", "description": ""},    # too old
    ]
    result = s._filter_and_normalize(raw_jobs)
    assert len(result) == 2, f"Expected 2 after filtering, got {len(result)}"

T.run("BaseScraper: filter_and_normalize (dedup + old + invalid)", _test_scraper_filter_and_normalize)


def _test_scraper_is_date_fresh():
    s = _get_scraper()
    today = datetime.now().strftime("%Y-%m-%d")
    old = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    assert s._is_date_fresh(today) is True
    assert s._is_date_fresh(old) is False
    assert s._is_date_fresh("") is True   # unknown → assume fresh
    assert s._is_date_fresh(None) is True

T.run("BaseScraper: is_date_fresh (fresh/old/empty)", _test_scraper_is_date_fresh)


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 5 — LINK VALIDATOR
# ─────────────────────────────────────────────────────────────────────────────

def _test_validator_init():
    from validators.link_validator import LinkValidator
    v = LinkValidator()
    assert v.session is not None
    assert isinstance(v._url_cache, dict)

T.run("LinkValidator: Initialization", _test_validator_init)


def _test_validator_url_syntax():
    from validators.link_validator import LinkValidator
    v = LinkValidator()

    ok, _ = v._validate_url_syntax("https://www.example.com/job/123")
    assert ok is True

    ok, _ = v._validate_url_syntax("http://example.com/job")
    assert ok is True

    for bad in ["", None, "ftp://example.com", "not-a-url",
                "https://example.com/job with spaces",
                "x" * 2049]:
        ok, reason = v._validate_url_syntax(bad)
        assert ok is False, f"Expected False for: {bad!r}"

T.run("LinkValidator: URL syntax validation (valid/invalid)", _test_validator_url_syntax)


def _test_validator_login_redirect():
    from validators.link_validator import LinkValidator
    v = LinkValidator()

    # Redirected to login on same domain
    assert v._is_login_redirect(
        "https://linkedin.com/login?redirect=jobs",
        "https://linkedin.com/jobs/view/123") is True

    # Redirected to signin on same domain
    assert v._is_login_redirect(
        "https://example.com/signin",
        "https://example.com/job/123") is True

    # Same URL — not a redirect
    assert v._is_login_redirect(
        "https://example.com/job/123",
        "https://example.com/job/123") is False

    # None final URL
    assert v._is_login_redirect(None, "https://example.com/job/123") is False

T.run("LinkValidator: Login redirect detection", _test_validator_login_redirect)


def _test_validator_title_check():
    from validators.link_validator import LinkValidator
    v = LinkValidator()

    good_html = """<html><body>
        <h1>UX Designer at Razorpay</h1>
        <div>Job Description: We are looking for a UX Designer</div>
        <div>Responsibilities: Design user interfaces and prototypes</div>
        <div>Requirements: 3+ years experience with Figma</div>
        <div>Apply now for this exciting position</div>
    </body></html>"""
    assert v._check_title_exists(good_html, "UX Designer") is True

    html_404 = "<html><head><title>404 Page Not Found</title></head><body>page not found</body></html>"
    assert v._check_title_exists(html_404, "UX Designer") is False

    assert v._check_title_exists("", "UX Designer") is False
    assert v._check_title_exists(None, "UX Designer") is False

T.run("LinkValidator: Title existence check (valid/404/empty)", _test_validator_title_check)


def _test_validator_company_check():
    from validators.link_validator import LinkValidator
    v = LinkValidator()

    html = "<html><body><h1>UX Designer</h1><p>About us: Razorpay is a fintech company</p></body></html>"
    assert v._check_company_exists(html, "Razorpay") is True

    html_generic = "<html><body><h1>UX Designer</h1><p>About the company and our organization</p></body></html>"
    assert v._check_company_exists(html_generic, "") is True

    assert v._check_company_exists("", "Razorpay") is False

T.run("LinkValidator: Company existence check", _test_validator_company_check)


def _test_validator_expiry_check():
    from validators.link_validator import LinkValidator
    v = LinkValidator()

    active = "<html><body><h1>UX Designer</h1><p>Apply now for this exciting role</p></body></html>"
    is_active, _ = v._check_not_expired(active)
    assert is_active is True

    expired = "<html><body><p>This job is no longer available. Job no longer available.</p></body></html>"
    is_active, reason = v._check_not_expired(expired)
    assert is_active is False
    assert "Expired" in reason

    is_active, _ = v._check_not_expired("")
    assert is_active is False

T.run("LinkValidator: Expiry detection (active/expired/empty)", _test_validator_expiry_check)


def _test_validator_date_check():
    from validators.link_validator import LinkValidator
    v = LinkValidator()

    assert v._check_date_exists("<html><body>Posted 2 days ago</body></html>") is True
    assert v._check_date_exists("<html><body>2026-08-21</body></html>") is True
    assert v._check_date_exists("<html><body>Posted today</body></html>") is True
    assert v._check_date_exists("<html><body>Jan 15 2026</body></html>") is True
    assert v._check_date_exists("<html><body>No date here at all</body></html>") is False
    assert v._check_date_exists("") is False

T.run("LinkValidator: Date existence check (various formats)", _test_validator_date_check)


def _test_validator_cache_hit():
    from validators.link_validator import LinkValidator
    v = LinkValidator()
    v.clear_cache()

    url = "https://example.com/job/cached-test"
    cache_key = hashlib.md5(url.encode()).hexdigest()
    v._url_cache[cache_key] = {
        "validation_status": "VALID",
        "http_status_code": 200,
        "validation_reason": "Cached result",
    }

    job = {"url": url, "title": "UX Designer", "company": "TestCo"}
    result = v.validate(job)
    assert result["validation_status"] == "VALID"
    assert result["http_status_code"] == 200

T.run("LinkValidator: Cache hit returns cached result", _test_validator_cache_hit)


def _test_validator_invalid_url_pipeline():
    from validators.link_validator import LinkValidator
    v = LinkValidator()

    job = {"url": "not-a-valid-url", "title": "UX Designer", "company": "TestCo"}
    result = v.validate(job)
    assert result["validation_status"] == "INVALID"
    assert "Step1 FAIL" in result["validation_reason"]

T.run("LinkValidator: Invalid URL → INVALID at Step1", _test_validator_invalid_url_pipeline)


def _test_validator_batch():
    from validators.link_validator import LinkValidator
    v = LinkValidator()

    jobs = [
        {"url": "bad-url-1", "title": "UX Designer", "company": "A"},
        {"url": "bad-url-2", "title": "UI Designer", "company": "B"},
        {"url": "also-bad", "title": "Product Designer", "company": "C"},
    ]
    results = v.validate_batch(jobs)
    assert len(results) == 3
    for r in results:
        assert r["validation_status"] == "INVALID"

T.run("LinkValidator: validate_batch with all-invalid URLs", _test_validator_batch)


def _test_validator_clear_cache():
    from validators.link_validator import LinkValidator
    v = LinkValidator()
    v._url_cache["dummy"] = {"validation_status": "VALID"}
    v.clear_cache()
    assert len(v._url_cache) == 0

T.run("LinkValidator: clear_cache empties cache", _test_validator_clear_cache)


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 6 — DASHBOARD GENERATOR
# ─────────────────────────────────────────────────────────────────────────────

def _test_dashboard_init():
    from output.dashboard_generator import DashboardGenerator
    gen = DashboardGenerator()
    assert gen.today == datetime.now().strftime("%Y-%m-%d")
    assert gen.generated_at is not None

T.run("DashboardGenerator: Initialization", _test_dashboard_init)


def _test_dashboard_date_label():
    from output.dashboard_generator import DashboardGenerator
    gen = DashboardGenerator()
    today = datetime.now().strftime("%Y-%m-%d")
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    three_days = (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d")

    assert gen._format_date_label(today) == "Today"
    assert gen._format_date_label(yesterday) == "Yesterday"
    # New compact format: "3d ago" (was "3 days ago")
    result = gen._format_date_label(three_days)
    assert "3" in result and ("ago" in result or "d" in result), \
        f"Expected 3-day label to contain '3' and time indicator, got: {result!r}"
    assert gen._format_date_label("") == "Recently"
    assert gen._format_date_label("Recently") == "Recently"
    assert gen._format_date_label(None) == "Recently"

T.run("DashboardGenerator: Date label formatting", _test_dashboard_date_label)


def _test_dashboard_html_escape():
    from output.dashboard_generator import DashboardGenerator
    gen = DashboardGenerator()

    assert gen._esc("<script>") == "&lt;script&gt;"
    assert gen._esc("A & B") == "A &amp; B"
    assert gen._esc('"quoted"') == "&quot;quoted&quot;"
    assert gen._esc("it's") == "it&#39;s"

T.run("DashboardGenerator: HTML escaping (_esc)", _test_dashboard_html_escape)


def _test_dashboard_empty_state():
    from output.dashboard_generator import DashboardGenerator
    gen = DashboardGenerator()

    result = gen._empty_state([], "No jobs found today")
    assert "No jobs found today" in result
    assert "empty-state" in result

    result = gen._empty_state([{"title": "job"}], "No jobs found today")
    assert result == ""

T.run("DashboardGenerator: Empty state rendering", _test_dashboard_empty_state)


def _test_dashboard_generate_html():
    """Full generate() call — checks file is created and contains key content."""
    import config
    from output.dashboard_generator import DashboardGenerator

    gen = DashboardGenerator()
    today = datetime.now().strftime("%Y-%m-%d")

    jobs = [
        {
            "job_id": "dash_001", "title": "UX Designer", "company": "TestCo",
            "location": "Hyderabad", "url": "https://example.com/job/1",
            "apply_url": "https://example.com/job/1", "source": "Test",
            "posted_date": today, "match_score": 85.0,
            "skill_match": 80.0, "role_match": 90.0, "experience_match": 85.0,
            "tool_match": 75.0, "domain_match": 70.0,
            "score_breakdown": "Role:90 Skill:80 Tool:75 Exp:85 Domain:70",
            "validation_status": "VALID", "is_new": 1, "run_id": 1,
        }
    ]
    stats = {"jobs_crawled": 10, "jobs_validated": 5, "jobs_rejected": 2,
             "duplicates_removed": 1, "expired_rejected": 0,
             "new_jobs_added": 5, "errors": 0}

    fd, tmp_html = tempfile.mkstemp(suffix=".html")
    os.close(fd)
    original = config.DASHBOARD_FILE
    config.DASHBOARD_FILE = tmp_html

    try:
        path = gen.generate(jobs=jobs, stats=stats, run_id=1)
        assert os.path.exists(path)

        with open(path, "r", encoding="utf-8") as f:
            html = f.read()

        assert "<!DOCTYPE html>" in html
        assert "UX Designer" in html
        assert "TestCo" in html
        assert "85.0%" in html or "85%" in html
        assert "ALL_JOBS" in html
        assert "</html>" in html

        # Verify no raw </script> inside the JSON data block
        # (the JSON should have it escaped as <\/script>)
        json_start = html.find("const ALL_JOBS =")
        json_end = html.find(";\n\n        function applyFilters")
        if json_start != -1 and json_end != -1:
            json_block = html[json_start:json_end]
            assert "</script>" not in json_block, \
                "</script> found unescaped inside ALL_JOBS JSON block"
    finally:
        config.DASHBOARD_FILE = original
        if os.path.exists(tmp_html):
            os.unlink(tmp_html)

T.run("DashboardGenerator: generate() creates valid HTML file", _test_dashboard_generate_html)


def _test_dashboard_script_injection_safe():
    """Jobs with </script> in description must not break the HTML."""
    import config
    from output.dashboard_generator import DashboardGenerator

    gen = DashboardGenerator()
    today = datetime.now().strftime("%Y-%m-%d")

    jobs = [{
        "job_id": "xss_001", "title": "UX Designer",
        "company": "Evil</script><script>alert(1)</script>Co",
        "location": "Hyderabad", "url": "https://example.com/xss",
        "apply_url": "https://example.com/xss", "source": "Test",
        "posted_date": today, "match_score": 80.0,
        "skill_match": 75.0, "role_match": 85.0, "experience_match": 80.0,
        "tool_match": 70.0, "domain_match": 65.0, "score_breakdown": "",
        "validation_status": "VALID", "is_new": 0, "run_id": 1,
        "description": "Use Figma </script><script>alert('xss')</script> for design",
    }]

    fd, tmp_html = tempfile.mkstemp(suffix=".html")
    os.close(fd)
    original = config.DASHBOARD_FILE
    config.DASHBOARD_FILE = tmp_html

    try:
        gen.generate(jobs=jobs, stats={}, run_id=1)
        with open(tmp_html, "r", encoding="utf-8") as f:
            html = f.read()

        # Find the ALL_JOBS JSON block and verify </script> is escaped
        json_start = html.find("const ALL_JOBS =")
        json_end = html.find(";\n\n        function applyFilters")
        if json_start != -1 and json_end != -1:
            json_block = html[json_start:json_end]
            assert "</script>" not in json_block, \
                "Unescaped </script> found in ALL_JOBS JSON — XSS vulnerability!"
    finally:
        config.DASHBOARD_FILE = original
        if os.path.exists(tmp_html):
            os.unlink(tmp_html)

T.run("DashboardGenerator: </script> injection safety in JSON block", _test_dashboard_script_injection_safe)


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 7 — SCRAPER INSTANTIATION
# ─────────────────────────────────────────────────────────────────────────────

def _test_scraper_instances():
    from scrapers.naukri_scraper import NaukriScraper
    from scrapers.linkedin_scraper import LinkedInScraper
    from scrapers.indeed_scraper import IndeedScraper
    from scrapers.foundit_scraper import FounditScraper
    from scrapers.glassdoor_scraper import GlassdoorScraper
    from scrapers.wellfound_scraper import WellfoundScraper
    from scrapers.instahyre_scraper import InstahyreScraper
    from scrapers.company_pages_scraper import CompanyPagesScraper
    from scrapers.arbeitsagentur_scraper import ArbeitsagenturScraper
    from scrapers.german_portals_scraper import GermanPortalsScraper

    for cls in [NaukriScraper, LinkedInScraper, IndeedScraper, FounditScraper,
                GlassdoorScraper, WellfoundScraper, InstahyreScraper,
                CompanyPagesScraper, ArbeitsagenturScraper, GermanPortalsScraper]:
        obj = cls()
        assert obj.session is not None, f"{cls.__name__} session is None"
        assert isinstance(obj.existing_urls, set)
        assert isinstance(obj.existing_job_ids, set)

T.run("Scrapers: All scrapers instantiate without error", _test_scraper_instances)


def _test_scraper_set_existing_data():
    from scrapers.naukri_scraper import NaukriScraper
    s = NaukriScraper()
    urls = {"https://a.com", "https://b.com"}
    ids = {"id1", "id2"}
    s.set_existing_data(urls, ids)
    assert s.existing_urls == urls
    assert s.existing_job_ids == ids

T.run("Scrapers: set_existing_data stores URLs and IDs", _test_scraper_set_existing_data)


def _test_instahyre_parse_api_job_no_url():
    """_parse_api_job with no slug and no job_id must return None (not {})."""
    from scrapers.instahyre_scraper import InstahyreScraper
    s = InstahyreScraper()
    result = s._parse_api_job({"designation": "UX Designer", "employer": {"name": "Co"}})
    # Should be None or empty dict — either way it must be falsy so it gets filtered
    assert not result, \
        f"_parse_api_job with no URL should return falsy value, got: {result!r}"

T.run("Scrapers: InstahyreScraper._parse_api_job with no URL returns falsy", _test_instahyre_parse_api_job_no_url)


def _test_naukri_parse_api_job():
    """NaukriScraper._parse_api_job should build a valid URL."""
    from scrapers.naukri_scraper import NaukriScraper
    s = NaukriScraper()
    raw = {
        "jobId": "12345",
        "title": "UX Designer",
        "companyName": "Razorpay",
        "placeholders": [{"type": "location", "label": "Hyderabad"}],
        "footerPlaceholderLabel": "2 days ago",
        "tagsAndSkills": "Figma, User Research",
    }
    result = s._parse_api_job(raw)
    assert result["title"] == "UX Designer"
    assert result["company"] == "Razorpay"
    assert result["url"].startswith("https://www.naukri.com/")
    assert result["job_id"] == "naukri_12345"
    assert "Figma" in result["description"]

T.run("Scrapers: NaukriScraper._parse_api_job builds correct job dict", _test_naukri_parse_api_job)


def _test_company_pages_is_design_job():
    from scrapers.company_pages_scraper import _is_design_job
    assert _is_design_job("UI/UX Designer") is True
    assert _is_design_job("Senior UX Researcher") is True
    assert _is_design_job("Product Designer") is True
    assert _is_design_job("Visual Designer") is True
    assert _is_design_job("Figma Expert") is True
    assert _is_design_job("Software Engineer") is False
    assert _is_design_job("Data Scientist") is False
    assert _is_design_job("Backend Developer") is False
    assert _is_design_job("") is False

T.run("Scrapers: CompanyPagesScraper._is_design_job filter", _test_company_pages_is_design_job)


def _test_foundit_parse_json_ld():
    from scrapers.foundit_scraper import FounditScraper
    s = FounditScraper()
    data = {
        "@type": "JobPosting",
        "title": "Product Designer",
        "hiringOrganization": {"name": "CRED"},
        "jobLocation": {"address": {"addressLocality": "Bangalore"}},
        "url": "https://www.foundit.in/job/product-designer-cred-123",
        "datePosted": "2026-08-20",
        "description": "Design fintech products using Figma and user research.",
    }
    result = s._parse_json_ld(data)
    assert result is not None
    assert result["title"] == "Product Designer"
    assert result["company"] == "CRED"
    assert result["location"] == "Bangalore"
    assert result["url"].startswith("https://")

T.run("Scrapers: FounditScraper._parse_json_ld parses JobPosting", _test_foundit_parse_json_ld)


def _test_glassdoor_parse_json_ld():
    from scrapers.glassdoor_scraper import GlassdoorScraper
    s = GlassdoorScraper()
    data = {
        "@type": "JobPosting",
        "title": "Interaction Designer",
        "hiringOrganization": {"name": "Swiggy"},
        "jobLocation": {"address": {"addressLocality": "Hyderabad"}},
        "url": "https://www.glassdoor.co.in/job-listing/j?jl=99887766",
        "datePosted": "2026-08-22",
        "description": "Interaction design for food delivery app.",
    }
    result = s._parse_json_ld(data)
    assert result is not None
    assert result["title"] == "Interaction Designer"
    assert result["company"] == "Swiggy"
    assert result["job_id"] == "glassdoor_99887766"

T.run("Scrapers: GlassdoorScraper._parse_json_ld parses JobPosting", _test_glassdoor_parse_json_ld)


def _test_wellfound_parse_json_ld():
    from scrapers.wellfound_scraper import WellfoundScraper
    s = WellfoundScraper()
    data = {
        "@type": "JobPosting",
        "title": "UX Designer",
        "hiringOrganization": {"name": "Zepto"},
        "jobLocation": {"address": {"addressLocality": "Mumbai"}},
        "url": "https://wellfound.com/jobs/zepto-ux-designer",
        "datePosted": "2026-08-21",
        "description": "Design quick commerce experiences with Figma.",
    }
    result = s._parse_json_ld(data)
    assert result is not None
    assert result["title"] == "UX Designer"
    assert result["company"] == "Zepto"

T.run("Scrapers: WellfoundScraper._parse_json_ld parses JobPosting", _test_wellfound_parse_json_ld)


def _test_instahyre_parse_json_ld():
    from scrapers.instahyre_scraper import InstahyreScraper
    s = InstahyreScraper()
    data = {
        "@type": "JobPosting",
        "title": "Senior UX Designer",
        "hiringOrganization": {"name": "Freshworks"},
        "jobLocation": {"address": {"addressLocality": "Hyderabad"}},
        "url": "https://www.instahyre.com/job/freshworks-senior-ux-designer/",
        "datePosted": "2026-08-23",
        "description": "Lead UX design for enterprise SaaS products.",
    }
    result = s._parse_json_ld(data)
    assert result is not None
    assert result["title"] == "Senior UX Designer"
    assert result["company"] == "Freshworks"

T.run("Scrapers: InstahyreScraper._parse_json_ld parses JobPosting", _test_instahyre_parse_json_ld)


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 8 — INTEGRATION: SCORING + DATABASE
# ─────────────────────────────────────────────────────────────────────────────

def _test_integration_score_and_store():
    """Score a job with ScoringEngine then store it in DB — end-to-end."""
    from engines.scoring_engine import ScoringEngine
    from database.db_manager import DatabaseManager

    fd, tmp = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    os.unlink(tmp)

    try:
        scorer = ScoringEngine()
        db = DatabaseManager(db_path=tmp)
        run_id = db.start_run()

        raw_job = {
            "title": "Senior UI/UX Designer",
            "company": "Razorpay",
            "location": "Hyderabad",
            "url": "https://razorpay.com/jobs/senior-ui-ux-designer",
            "apply_url": "https://razorpay.com/jobs/senior-ui-ux-designer",
            "source": "Company Career Pages",
            "posted_date": datetime.now().strftime("%Y-%m-%d"),
            "posted_date_raw": "today",
            "description": (
                "Senior UI/UX Designer. Figma, user research, usability testing, "
                "wireframing, prototyping, design systems, WCAG 2.1, Agile. "
                "4+ years experience. Fintech B2B SaaS."
            ),
        }

        scored = scorer.compute_score(raw_job)
        assert scored["match_score"] >= 70

        import hashlib
        raw_id = f"{scored['title'].lower()}|{scored['company'].lower()}|{scored['url']}"
        scored["job_id"] = "integ_" + hashlib.md5(raw_id.encode()).hexdigest()[:12]
        scored["validation_status"] = "VALID"
        scored["http_status_code"] = 200

        result = db.insert_job(scored, run_id)
        assert result is True

        jobs = db.get_jobs_for_dashboard(min_score=70.0)
        assert len(jobs) == 1
        assert jobs[0]["match_score"] >= 70
        assert jobs[0]["company"] == "Razorpay"
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)

T.run("Integration: ScoringEngine → DatabaseManager (score + store + query)", _test_integration_score_and_store)


def _test_integration_seed_demo_data():
    """Run seed_demo_data with a temp DB — verifies end-to-end pipeline."""
    import config
    from database.db_manager import DatabaseManager
    from engines.scoring_engine import ScoringEngine
    from output.dashboard_generator import DashboardGenerator

    fd_db, tmp_db = tempfile.mkstemp(suffix=".db")
    os.close(fd_db)
    os.unlink(tmp_db)

    fd_html, tmp_html = tempfile.mkstemp(suffix=".html")
    os.close(fd_html)

    orig_db = config.DB_PATH
    orig_dash = config.DASHBOARD_FILE
    config.DB_PATH = tmp_db
    config.DASHBOARD_FILE = tmp_html

    try:
        db = DatabaseManager(db_path=tmp_db)
        scorer = ScoringEngine()
        dashboard = DashboardGenerator()
        run_id = db.start_run()

        # Insert 3 sample jobs
        today = datetime.now().strftime("%Y-%m-%d")
        sample_jobs = [
            {
                "job_id": "seed_001",
                "title": "Senior UI/UX Designer",
                "company": "Razorpay",
                "location": "Bangalore",
                "url": "https://razorpay.com/jobs/ux-1",
                "apply_url": "https://razorpay.com/jobs/ux-1",
                "source": "Company Career Pages",
                "posted_date": today,
                "posted_date_raw": "today",
                "description": "Figma user research usability testing design system WCAG Agile",
                "validation_status": "VALID",
                "http_status_code": 200,
            },
            {
                "job_id": "seed_002",
                "title": "Product Designer",
                "company": "CRED",
                "location": "Bangalore",
                "url": "https://careers.cred.club/pd-1",
                "apply_url": "https://careers.cred.club/pd-1",
                "source": "Company Career Pages",
                "posted_date": today,
                "posted_date_raw": "today",
                "description": "Figma prototyping wireframing interaction design fintech",
                "validation_status": "VALID",
                "http_status_code": 200,
            },
        ]

        inserted = 0
        for job in sample_jobs:
            scored = scorer.compute_score(job)
            scored["job_id"] = job["job_id"]
            scored["validation_status"] = "VALID"
            scored["http_status_code"] = 200
            if db.insert_job(scored, run_id):
                inserted += 1

        assert inserted == 2, f"Expected 2 inserted, got {inserted}"

        stats = {"jobs_crawled": 10, "jobs_validated": 2, "jobs_rejected": 0,
                 "duplicates_removed": 0, "expired_rejected": 0,
                 "new_jobs_added": 2, "errors": 0}
        db.finish_run(run_id, stats)

        all_jobs = db.get_jobs_for_dashboard(min_score=0)
        path = dashboard.generate(jobs=all_jobs, stats=stats, run_id=run_id)
        assert os.path.exists(path)

        with open(path, "r", encoding="utf-8") as f:
            html = f.read()
        assert "Razorpay" in html
        assert "CRED" in html
    finally:
        config.DB_PATH = orig_db
        config.DASHBOARD_FILE = orig_dash
        for p in [tmp_db, tmp_html]:
            if os.path.exists(p):
                os.unlink(p)

T.run("Integration: Full mini-pipeline (score + store + dashboard)", _test_integration_seed_demo_data)


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 9 — CONFIG SANITY
# ─────────────────────────────────────────────────────────────────────────────

def _test_config_paths_exist_or_creatable():
    import config
    # BASE_DIR must exist
    assert os.path.isdir(config.BASE_DIR), f"BASE_DIR missing: {config.BASE_DIR}"
    # LOGS_DIR should be creatable
    os.makedirs(config.LOGS_DIR, exist_ok=True)
    assert os.path.isdir(config.LOGS_DIR)

T.run("Config: BASE_DIR exists, LOGS_DIR creatable", _test_config_paths_exist_or_creatable)


def _test_config_values_sane():
    import config
    assert 0 < config.MIN_MATCH_SCORE <= 100
    assert config.MAX_WORKERS >= 1
    assert config.REQUEST_TIMEOUT >= 5
    assert config.MAX_RETRIES >= 1
    assert config.RETRY_DELAY >= 0
    assert config.RATE_LIMIT_DELAY >= 0
    assert len(config.TARGET_ROLES) > 0
    assert len(config.SEARCH_KEYWORDS) > 0
    assert len(config.COMPANY_CAREER_PAGES) > 0
    assert len(config.EXPIRED_PATTERNS) > 0
    assert len(config.LOGIN_REDIRECT_PATTERNS) > 0

T.run("Config: All numeric/list values are sane", _test_config_values_sane)


def _test_config_scraper_urls():
    import config
    for key, url in config.SCRAPER_URLS.items():
        assert url.startswith("https://"), f"SCRAPER_URLS[{key!r}] not https: {url}"

T.run("Config: All SCRAPER_URLS use https", _test_config_scraper_urls)


def _test_config_company_pages():
    import config
    for entry in config.COMPANY_CAREER_PAGES:
        assert "company" in entry, f"Missing 'company' key: {entry}"
        assert "url" in entry, f"Missing 'url' key: {entry}"
        assert entry["url"].startswith("https://"), \
            f"Company page URL not https: {entry['url']}"

T.run("Config: All COMPANY_CAREER_PAGES have company+url (https)", _test_config_company_pages)


# ─────────────────────────────────────────────────────────────────────────────
# RUN ALL TESTS AND REPORT
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    all_passed = T.report()
    sys.exit(0 if all_passed else 1)
