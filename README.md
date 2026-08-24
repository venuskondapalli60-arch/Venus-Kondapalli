# UI/UX Job Search Automation

Scrapes UI/UX job listings from 8 sources, scores them against a resume profile, validates URLs, stores results in SQLite, and generates an HTML dashboard.

## How It Works

1. **Scrape** — 10 scrapers run in parallel across Naukri, LinkedIn, Indeed, Foundit, Glassdoor, Wellfound, Instahyre, Shine, TimesJobs, and direct company career pages, searching using both role-based and skill-based keywords derived from the resume.
2. **Score** — Each job is scored 0–100 against the resume profile by matching job title, required skills, design tools, years of experience, and domain keywords. Only jobs above `MIN_MATCH_SCORE` (default 60) proceed.
3. **Validate** — Surviving job URLs are checked via HTTP HEAD/GET in parallel threads to confirm they are live, not expired, and not redirecting to a login wall.
4. **Store** — Valid jobs are written to a local SQLite database (`jobs.db`) with deduplication — jobs already seen in previous runs are skipped. Each run marks newly found jobs with `is_new = 1`.
5. **Dashboard** — `dashboard_generator.py` reads the database and writes `jobs_dashboard.html` — a dark-themed, filterable, sortable HTML page showing Today's Fresh Jobs (newly found this run), Last 3 Days, Last 7 Days, and Top Matches (90%+).
6. **Repeat** — Run `python main.py` daily (or schedule via Task Scheduler / cron) to keep the dashboard fresh with the latest listings.

---

## Files

| File | Purpose |
|------|---------|
| `main.py` | Entry point. Orchestrates the full pipeline: scrape → score → validate → store → dashboard. |
| `config.py` | All settings (paths, thresholds, search keywords, HTTP config) + resume profile data used for scoring. |
| `db_manager.py` | SQLite database layer. Handles job storage, deduplication, run tracking, and cleanup. |
| `scoring_engine.py` | Scores each job 0–100 against the resume profile using role, skill, tool, experience, and domain matching. |
| `link_validator.py` | Validates job URLs via HTTP HEAD/GET. Marks jobs as VALID, INVALID, or EXPIRED. |
| `dashboard_generator.py` | Generates `jobs_dashboard.html` — a filterable, sortable HTML dashboard of all valid jobs. |
| `test_validation.py` | Quick smoke test to verify the validator and scorer work correctly. |
| `run_job_search.bat` | Windows batch script to run the full pipeline with one double-click. |
| `requirements.txt` | Python package dependencies. |
| `jobs.db` | SQLite database file (auto-created on first run). |
| `jobs_dashboard.html` | Generated dashboard output (auto-created/updated on each run). |
| `scrapers/base_scraper.py` | Abstract base class for all scrapers. Provides HTTP session, date parsing, dedup, and normalization. |
| `scrapers/naukri_scraper.py` | Scrapes Naukri.com via their job search API. |
| `scrapers/linkedin_scraper.py` | Scrapes LinkedIn Jobs via the guest API endpoint. |
| `scrapers/indeed_scraper.py` | Scrapes Indeed India job listings. |
| `scrapers/foundit_scraper.py` | Scrapes Foundit (formerly Monster India) listings. |
| `scrapers/glassdoor_scraper.py` | Scrapes Glassdoor India job listings. |
| `scrapers/wellfound_scraper.py` | Scrapes Wellfound (AngelList) for startup design roles. |
| `scrapers/instahyre_scraper.py` | Scrapes Instahyre via their search API. |
| `scrapers/shine_scraper.py` | Scrapes Shine.com (Times of India group) — major Indian job portal. |
| `scrapers/timesjobs_scraper.py` | Scrapes TimesJobs.com — one of India's largest job portals. |
| `scrapers/company_pages_scraper.py` | Scrapes career pages of 26 top Indian companies directly. |

---

## How to Run

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the full pipeline (scrape + score + validate + dashboard)
```bash
python main.py
```
Or on Windows, double-click **`run_job_search.bat`**.

### 3. Open the dashboard
After the run completes, open `jobs_dashboard.html` in any browser.

---

## Other Commands

```bash
# Regenerate dashboard from existing database (no scraping)
python main.py --dashboard-only

# Run only specific sources (now 10 sources available)
python main.py --sources naukri linkedin shine timesjobs

# Skip URL validation (faster, less accurate)
python main.py --sources naukri --no-validate

# Re-validate all stored URLs and remove dead links
python main.py --revalidate

# Remove jobs older than 30 days from the database
python main.py --cleanup

# Set a custom minimum match score (default: 70)
python main.py --min-score 80
```

---

## Tuning

Edit **`config.py`** to adjust:
- `MIN_MATCH_SCORE` — minimum score to show in dashboard (default: 70)
- `MAX_DAYS_OLD` — how old a job posting can be (default: 7 days)
- `SEARCH_LOCATIONS` — target cities
- `COMPANY_CAREER_PAGES` — list of company career pages to scrape
- `SEARCH_KEYWORDS` — role-based search terms (e.g. "UX Designer", "Product Designer")
- `SKILL_SEARCH_KEYWORDS` — skill-based search terms derived from resume (e.g. "Figma Designer", "Design System Designer"). All scrapers use `ALL_SEARCH_KEYWORDS = SEARCH_KEYWORDS + SKILL_SEARCH_KEYWORDS`
- `RESUME_PROFILE` — update with your own skills, tools, and target roles. Changes here automatically update scoring weights and `SKILL_SEARCH_KEYWORDS` should be kept in sync
