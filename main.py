"""
main.py - UI/UX Job Search Automation System
Main orchestrator: scrape → deduplicate → validate → score → store → generate dashboard

Usage:
    python main.py                    # Run full pipeline
    python main.py --dashboard-only   # Regenerate dashboard from existing DB
    python main.py --validate-only    # Re-validate existing jobs
    python main.py --sources naukri linkedin  # Run specific scrapers only
"""

import os
import sys
import time
import logging
import argparse
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict

# ── Path setup ────────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

import config
from db_manager import DatabaseManager
from link_validator import LinkValidator
from scoring_engine import ScoringEngine
from dashboard_generator import DashboardGenerator

# ── Scrapers ──────────────────────────────────────────────────────────────────
from scrapers.arbeitsagentur_scraper import ArbeitsagenturScraper
from scrapers.german_portals_scraper import GermanPortalsScraper
from scrapers.naukri_scraper import NaukriScraper
from scrapers.linkedin_scraper import LinkedInScraper
from scrapers.indeed_scraper import IndeedScraper
from scrapers.foundit_scraper import FounditScraper
from scrapers.glassdoor_scraper import GlassdoorScraper
from scrapers.wellfound_scraper import WellfoundScraper
from scrapers.instahyre_scraper import InstahyreScraper
from scrapers.company_pages_scraper import CompanyPagesScraper
from scrapers.shine_scraper import ShineScraper
from scrapers.timesjobs_scraper import TimesJobsScraper


# ─────────────────────────────────────────────────────────────────────────────
# LOGGING SETUP
# ─────────────────────────────────────────────────────────────────────────────
def setup_logging():
    """Configure logging to both file and console."""
    os.makedirs(config.LOGS_DIR, exist_ok=True)

    log_format = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"

    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter(log_format, date_format))

    # File handler
    file_handler = logging.FileHandler(config.LOG_FILE, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(log_format, date_format))

    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)

    # Suppress noisy third-party loggers
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("charset_normalizer").setLevel(logging.WARNING)


logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# SCRAPER REGISTRY
# ─────────────────────────────────────────────────────────────────────────────
SCRAPER_REGISTRY = {
    "arbeitsagentur": ArbeitsagenturScraper, # Priority 1: German Federal Agency
    "company_pages":  CompanyPagesScraper,   # Priority 2: German & Global Tech Careers
    "linkedin":       LinkedInScraper,       # Priority 3: Germany & Worldwide
    "german_portals": GermanPortalsScraper,  # Priority 4: Connecticum, Jobrapido, etc.
    "indeed":         IndeedScraper,         # Priority 5: Indeed Germany (de.indeed.com)
    "wellfound":      WellfoundScraper,      # Priority 6
    "glassdoor":      GlassdoorScraper,      # Priority 7: Glassdoor Germany
    "naukri":         NaukriScraper,         # Priority 8
    "foundit":        FounditScraper,        # Priority 9
    "instahyre":      InstahyreScraper,      # Priority 10
    "shine":          ShineScraper,          # Priority 11
    "timesjobs":      TimesJobsScraper,      # Priority 12
}


# ─────────────────────────────────────────────────────────────────────────────
# MAIN PIPELINE CLASS
# ─────────────────────────────────────────────────────────────────────────────
class JobSearchPipeline:
    """
    Orchestrates the full job search pipeline:
    1. Scrape from all sources
    2. Deduplicate against database
    3. Score against resume
    4. Validate URLs (multi-threaded)
    5. Store valid jobs in database
    6. Generate HTML dashboard
    """

    def __init__(self, sources: List[str] = None):
        self.db = DatabaseManager()
        self.validator = LinkValidator()
        self.scorer = ScoringEngine()
        self.dashboard = DashboardGenerator()
        self.sources = sources or list(SCRAPER_REGISTRY.keys())

        # Stats tracking
        self.stats = {
            "jobs_crawled": 0,
            "jobs_validated": 0,
            "jobs_rejected": 0,
            "duplicates_removed": 0,
            "expired_rejected": 0,
            "new_jobs_added": 0,
            "errors": 0,
        }

    def run(self) -> Dict:
        """Execute the full pipeline. Returns run statistics."""
        start_time = time.time()
        run_id = self.db.start_run()

        logger.info("=" * 70)
        logger.info("  UI/UX JOB SEARCH AUTOMATION — STARTING RUN")
        logger.info(f"  Run ID: {run_id} | Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"  Sources: {', '.join(self.sources)}")
        logger.info("=" * 70)

        try:
            # ── Step 1: Load existing data for dedup ─────────────────────────
            logger.info("Step 1: Loading existing job data for deduplication...")
            existing_urls = self.db.get_existing_urls()
            existing_job_ids = self.db.get_existing_job_ids()
            logger.info(f"  Existing jobs in DB: {len(existing_urls)}")

            # ── Step 2: Scrape all sources ────────────────────────────────────
            logger.info("Step 2: Scraping job listings from all sources...")
            all_raw_jobs = self._run_scrapers(existing_urls, existing_job_ids)
            self.stats["jobs_crawled"] = len(all_raw_jobs)
            logger.info(f"  Total raw jobs collected: {len(all_raw_jobs)}")

            if not all_raw_jobs:
                logger.warning("No jobs collected from any source. Check network/scraper logs.")
                self._finish_run(run_id, start_time)
                return self.stats

            # ── Step 3: Score against resume ──────────────────────────────────
            logger.info("Step 3: Computing resume match scores...")
            scored_jobs = self.scorer.score_batch(all_raw_jobs)
            logger.info(f"  Scored {len(scored_jobs)} jobs")

            # Filter by minimum score
            qualified_jobs = [j for j in scored_jobs
                              if j.get("match_score", 0) >= config.MIN_MATCH_SCORE]
            low_score_count = len(scored_jobs) - len(qualified_jobs)
            logger.info(
                f"  Qualified (>={config.MIN_MATCH_SCORE}%): {len(qualified_jobs)} "
                f"| Below threshold: {low_score_count}"
            )
            self.stats["jobs_rejected"] += low_score_count

            if not qualified_jobs:
                logger.warning("No jobs passed the minimum score threshold.")
                self._finish_run(run_id, start_time)
                return self.stats

            # ── Step 4: Validate URLs (multi-threaded) ────────────────────────
            logger.info(f"Step 4: Validating {len(qualified_jobs)} job URLs (multi-threaded)...")
            validated_jobs = self._validate_parallel(qualified_jobs)

            valid_jobs = [j for j in validated_jobs if j.get("validation_status") == "VALID"]
            invalid_jobs = [j for j in validated_jobs if j.get("validation_status") == "INVALID"]
            expired_jobs = [j for j in validated_jobs if j.get("validation_status") == "EXPIRED"]

            self.stats["jobs_validated"] = len(valid_jobs)
            self.stats["jobs_rejected"] += len(invalid_jobs)
            self.stats["expired_rejected"] = len(expired_jobs)

            logger.info(
                f"  Valid: {len(valid_jobs)} | Invalid: {len(invalid_jobs)} | "
                f"Expired: {len(expired_jobs)}"
            )

            # ── Step 5: Store in database ─────────────────────────────────────
            logger.info("Step 5: Storing valid jobs in database...")
            new_count = 0
            dup_count = 0

            for job in valid_jobs:
                if self.db.is_duplicate(job.get("job_id", ""), job.get("url", "")):
                    dup_count += 1
                    continue
                if self.db.insert_job(job, run_id):
                    new_count += 1

            self.stats["new_jobs_added"] = new_count
            self.stats["duplicates_removed"] = dup_count

            # Mark previous run jobs as not-new
            self.db.mark_old_jobs_not_new(run_id)

            logger.info(f"  New jobs stored: {new_count} | Duplicates skipped: {dup_count}")

            # ── Step 6: Generate dashboard ────────────────────────────────────
            logger.info("Step 6: Generating HTML dashboard...")
            dashboard_jobs = self.db.get_jobs_for_dashboard(config.MIN_MATCH_SCORE)
            dashboard_path = self.dashboard.generate(
                jobs=dashboard_jobs,
                stats=self.stats,
                run_id=run_id,
            )
            logger.info(f"  Dashboard: {dashboard_path}")

        except Exception as e:
            logger.error(f"Pipeline error: {e}", exc_info=True)
            self.stats["errors"] += 1

        finally:
            self._finish_run(run_id, start_time)

        return self.stats

    def _run_scrapers(self, existing_urls: set,
                      existing_job_ids: set) -> List[Dict]:
        """Run all configured scrapers and collect raw jobs."""
        all_jobs = []

        for source_name in self.sources:
            scraper_class = SCRAPER_REGISTRY.get(source_name)
            if not scraper_class:
                logger.warning(f"Unknown scraper: {source_name}")
                continue

            try:
                logger.info(f"  Scraping: {source_name}...")
                scraper = scraper_class()
                scraper.set_existing_data(existing_urls, existing_job_ids)
                jobs = scraper.scrape()
                all_jobs.extend(jobs)
                logger.info(f"  {source_name}: {len(jobs)} new jobs")

                # Add newly scraped URLs to the in-memory set to prevent
                # cross-scraper duplicates
                for job in jobs:
                    existing_urls.add(job.get("url", ""))
                    existing_job_ids.add(job.get("job_id", ""))

            except Exception as e:
                logger.error(f"Scraper error ({source_name}): {e}", exc_info=True)
                self.stats["errors"] += 1

        return all_jobs

    def _validate_parallel(self, jobs: List[Dict]) -> List[Dict]:
        """
        Validate jobs in parallel using ThreadPoolExecutor.
        Returns list of jobs with validation_status set.
        """
        validated = []
        total = len(jobs)

        with ThreadPoolExecutor(max_workers=config.MAX_WORKERS) as executor:
            future_to_job = {
                executor.submit(self.validator.validate, job): job
                for job in jobs
            }

            completed = 0
            for future in as_completed(future_to_job):
                try:
                    result = future.result(timeout=config.REQUEST_TIMEOUT + 5)
                    validated.append(result)
                except Exception as e:
                    original_job = future_to_job[future]
                    original_job["validation_status"] = "INVALID"
                    original_job["validation_reason"] = f"Validation exception: {e}"
                    validated.append(original_job)
                    self.stats["errors"] += 1

                completed += 1
                if completed % 20 == 0:
                    logger.info(f"  Validation progress: {completed}/{total}")

        return validated

    def _finish_run(self, run_id: int, start_time: float):
        """Finalize the run record and log summary."""
        elapsed = time.time() - start_time
        self.db.finish_run(run_id, self.stats)

        logger.info("=" * 70)
        logger.info("  RUN COMPLETE")
        logger.info(f"  Runtime: {elapsed:.1f}s")
        logger.info(f"  Jobs Crawled:        {self.stats['jobs_crawled']}")
        logger.info(f"  Jobs Validated:      {self.stats['jobs_validated']}")
        logger.info(f"  New Jobs Added:      {self.stats['new_jobs_added']}")
        logger.info(f"  Duplicates Removed:  {self.stats['duplicates_removed']}")
        logger.info(f"  Expired Rejected:    {self.stats['expired_rejected']}")
        logger.info(f"  Invalid Rejected:    {self.stats['jobs_rejected']}")
        logger.info(f"  Errors:              {self.stats['errors']}")
        logger.info(f"  Dashboard:           {config.DASHBOARD_FILE}")
        logger.info("=" * 70)


# ─────────────────────────────────────────────────────────────────────────────
# RE-VALIDATE STORED JOBS
# ─────────────────────────────────────────────────────────────────────────────
def _revalidate_stored_jobs():
    """
    Re-validate every VALID job URL currently in the database.

    Why this matters
    ────────────────
    LinkedIn /jobs/view/{id} URLs expire when a job is closed.
    Naukri, Indeed, Glassdoor listings also disappear over time.
    Running  python main.py --revalidate  checks every stored link
    and marks dead ones INVALID/EXPIRED so they are hidden from the
    dashboard and eventually cleaned up.

    Recommended schedule: run once a day alongside the normal scrape.
    """
    logger.info("=" * 70)
    logger.info("  RE-VALIDATION MODE — checking all stored job URLs")
    logger.info("=" * 70)

    db = DatabaseManager()
    validator = LinkValidator()
    dashboard = DashboardGenerator()

    jobs = db.get_all_jobs_for_revalidation()
    total = len(jobs)
    logger.info(f"  Jobs to re-validate: {total}")

    if not total:
        logger.info("  Nothing to re-validate.")
        return

    still_valid = 0
    newly_invalid = 0
    newly_expired = 0

    for i, job in enumerate(jobs, 1):
        try:
            result = validator.validate(job)
            status = result.get("validation_status", "INVALID")
            code   = result.get("http_status_code", -1)
            reason = result.get("validation_reason", "")

            db.update_job_validation(job["job_id"], status, code, reason)

            if status == "VALID":
                still_valid += 1
            elif status == "EXPIRED":
                newly_expired += 1
                logger.info(f"  EXPIRED  [{i}/{total}] {job['title']} @ {job['company']} — {job['url'][:60]}")
            else:
                newly_invalid += 1
                logger.info(f"  INVALID  [{i}/{total}] {job['title']} @ {job['company']} — {reason[:60]}")

            if i % 10 == 0:
                logger.info(f"  Progress: {i}/{total}")

        except Exception as e:
            logger.error(f"  Re-validation error for {job.get('job_id')}: {e}")

    # Remove dead links from the database
    removed = db.remove_invalid_jobs()

    logger.info("=" * 70)
    logger.info(f"  Re-validation complete")
    logger.info(f"  Still valid:    {still_valid}")
    logger.info(f"  Newly expired:  {newly_expired}")
    logger.info(f"  Newly invalid:  {newly_invalid}")
    logger.info(f"  Removed from DB:{removed}")
    logger.info("=" * 70)

    # Regenerate dashboard with cleaned data
    jobs_for_dash = db.get_jobs_for_dashboard(config.MIN_MATCH_SCORE)
    stats = db.get_last_run_stats() or {}
    path = dashboard.generate(jobs=jobs_for_dash, stats=stats, run_id=0)
    logger.info(f"  Dashboard refreshed: {path}")
    print(f"\n✅ Re-validation done. Removed {removed} dead links. Dashboard: {path}")


# ─────────────────────────────────────────────────────────────────────────────
# DASHBOARD-ONLY MODE
# ─────────────────────────────────────────────────────────────────────────────
def regenerate_dashboard():
    """Regenerate the dashboard from existing database without scraping."""
    logger.info("Dashboard-only mode: regenerating from existing database...")
    db = DatabaseManager()
    dashboard = DashboardGenerator()

    jobs = db.get_jobs_for_dashboard(config.MIN_MATCH_SCORE)
    stats = db.get_last_run_stats() or {}

    path = dashboard.generate(jobs=jobs, stats=stats, run_id=0)
    logger.info(f"Dashboard regenerated: {path}")
    return path


# ─────────────────────────────────────────────────────────────────────────────
# CLI ARGUMENT PARSER
# ─────────────────────────────────────────────────────────────────────────────
def parse_args():
    parser = argparse.ArgumentParser(
        description="UI/UX Job Search Automation System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                              # Full pipeline (all sources)
  python main.py --dashboard-only             # Regenerate dashboard only
  python main.py --sources naukri linkedin    # Run specific scrapers
  python main.py --sources naukri --no-validate  # Skip URL validation (faster)
        """,
    )
    parser.add_argument(
        "--dashboard-only",
        action="store_true",
        help="Regenerate dashboard from existing database without scraping",
    )
    parser.add_argument(
        "--sources",
        nargs="+",
        choices=list(SCRAPER_REGISTRY.keys()),
        help="Run only specific scrapers (default: all)",
    )
    parser.add_argument(
        "--no-validate",
        action="store_true",
        help="Skip URL validation (faster but less reliable)",
    )
    parser.add_argument(
        "--min-score",
        type=float,
        default=config.MIN_MATCH_SCORE,
        help=f"Minimum match score to display (default: {config.MIN_MATCH_SCORE})",
    )
    parser.add_argument(
        "--cleanup",
        action="store_true",
        help="Clean up jobs older than 30 days from database",
    )
    parser.add_argument(
        "--revalidate",
        action="store_true",
        help=(
            "Re-validate ALL stored job URLs and remove any that are now "
            "expired/invalid (LinkedIn links expire when jobs close, etc.)"
        ),
    )
    return parser.parse_args()


# ─────────────────────────────────────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────
def main():
    setup_logging()
    args = parse_args()

    logger.info("UI/UX Job Search Automation System v1.0")
    logger.info(f"Working directory: {BASE_DIR}")

    # Override config from CLI args
    if args.min_score != config.MIN_MATCH_SCORE:
        config.MIN_MATCH_SCORE = args.min_score
        logger.info(f"Min score override: {config.MIN_MATCH_SCORE}%")

    # Cleanup mode
    if args.cleanup:
        db = DatabaseManager()
        db.cleanup_old_jobs(days=30)
        logger.info("Database cleanup complete.")

    # Re-validate mode — check every stored link and purge dead ones
    if args.revalidate:
        _revalidate_stored_jobs()
        if not args.dashboard_only:
            return

    # Dashboard-only mode
    if args.dashboard_only:
        path = regenerate_dashboard()
        print(f"\n✅ Dashboard generated: {path}")
        return

    # No-validate mode: monkey-patch validator to always return VALID
    if args.no_validate:
        logger.warning("URL validation DISABLED (--no-validate flag)")
        import link_validator
        original_validate = link_validator.LinkValidator.validate

        def fast_validate(self, job):
            result = dict(job)
            result["validation_status"] = "VALID"
            result["http_status_code"] = 200
            result["validation_reason"] = "Validation skipped"
            return result

        link_validator.LinkValidator.validate = fast_validate

    # Full pipeline
    pipeline = JobSearchPipeline(sources=args.sources)
    stats = pipeline.run()

    # Print summary to console
    print("\n" + "=" * 60)
    print("  [OK] UI/UX JOB SEARCH COMPLETE")
    print("=" * 60)
    print(f"  Jobs Crawled:       {stats['jobs_crawled']}")
    print(f"  Valid Jobs:         {stats['jobs_validated']}")
    print(f"  New Jobs Added:     {stats['new_jobs_added']}")
    print(f"  Duplicates Removed: {stats['duplicates_removed']}")
    print(f"  Expired Rejected:   {stats['expired_rejected']}")
    print(f"  Invalid Rejected:   {stats['jobs_rejected']}")
    print("=" * 60)
    print(f"  Dashboard: {config.DASHBOARD_FILE}")
    print(f"  Log:       {config.LOG_FILE}")
    print("=" * 60)


if __name__ == "__main__":
    main()
