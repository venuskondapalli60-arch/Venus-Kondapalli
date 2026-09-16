# UI/UX & Product Management Job Hunt Platform
**Candidate**: Venus Kondapalli (Product Manager & UI UX Design Expert)

## Project Overview
This repository contains the automated job search, validation, AI scoring, and tracking platform customized for **Venus Kondapalli** (13+ Years Experience, B1 German).

## Structure & Main Components
- `main.py`: Main orchestrator (Scrape → Deduplicate → Validate → Score → Store → Generate Dashboard).
- `config.py`: Portals configuration, weights, directories, and thresholds.
- `resume_data.py`: Candidate profile, keywords, experience, skills, and scoring profile.
- `dashboard_generator.py`: Generates `jobs_dashboard.html` and mirrors `index.html`.
- `scoring_engine.py`: Multi-factor scoring (role, skill, tool, experience, domain).
- `link_validator.py`: Multi-step link and status validation.
- `db_manager.py`: SQLite database manager (`jobs.db`).
- `scrapers/`: Scrapers for Bundesagentur für Arbeit, German portals, LinkedIn, Indeed, Naukri, Foundit, Glassdoor, Wellfound, Instahyre, Shine, TimesJobs, and Company Career Pages.
- `setup_scheduler.sh`: macOS `launchd` daily scheduler script (runs daily at 10:00 AM).
- `run_job_search.sh`: One-click bash script to run the pipeline.
- `test_validation.py`: Complete test suite (80/80 unit and integration tests).

## Daily Automation
- Daily scheduled execution at **10:00 AM** via macOS `launchd` service (`com.venuskondapalli.jobhunt`).
- In-app Antigravity recurring cron task (`0 10 * * *`).

## Dashboard
- Open locally: `open http://localhost:8000` (Server: `python3 -m http.server 8000`).
