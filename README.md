# Venus-Kondapalli · Product & UI/UX Job Search Automation

> **Lead UX Designer | UX Researcher | Product Strategist**  
> With over 14 years of experience, I lead end-to-end product design for enterprise SaaS, FinTech, AI, B2B, and consumer applications. I specialize in user research, interaction design, design systems, ServiceNow, AI product design, stakeholder collaboration, and mentoring design teams to create impactful digital experiences.

---

## Overview

Automated job search, resume matching, URL validation, and tracking platform tailored for **Venus Kondapalli**. It searches across **Germany** (Berlin, Munich, Frankfurt, Hamburg, nationwide), **Remote (EU & Worldwide)**, and **India**, scoring every listing against a 14-year design & product profile.

Includes:
- **Dedicated Scrapers**: Jobbörse der Bundesagentur für Arbeit, LinkedIn, Indeed (DE & IN), Glassdoor, Wellfound, Shine, Instahyre, Naukri, and Company Career Portals.
- **47 German Job Portals Hub**: 1-click launchpad for StepStone, Jobbörse.de, Experteer, Kimeta, Adzuna, REKRUTER, regional German media, and tech directories.
- **Interactive Application Tracker Dashboard (`jobs_dashboard.html`)**:
  - Unified **Open Positions** view with live filters (Location, Min Score, Company, Source).
  - **"✓ Mark as Applied"** flow that moves jobs into a dedicated **"Applied Jobs & History"** tracker.
  - Interactive stage lifecycle selector (`Applied`, `Screening`, `Technical Round`, `Final Round`, `Offer Received`).
  - Private notes editor for tracking recruiter discussions.
  - One-click **Export to CSV / Excel**.

---

## How It Works

1. **Scrape** — Scrapers run in parallel across German and international sources using role and skill keywords.
2. **Score** — Each job is scored 0–100% using weighted matching (Role 30%, Skills 30%, Tools 20%, Experience 10%, Domain 10%).
3. **Validate** — Real-time HTTP verification to ensure job URLs are active and live.
4. **Store** — SQLite database (`jobs.db`) with deduplication.
5. **Dashboard** — Generates `jobs_dashboard.html` with persistent client-side application tracking via `localStorage`.

---

## How to Run

### 1. Install dependencies
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Run the pipeline
```bash
# Run full search across all sources
python main.py

# Run specific German sources
python main.py --sources arbeitsagentur,linkedin,german_portals

# Regenerate dashboard from database
python main.py --dashboard-only
```

### 3. Open Dashboard
```bash
open jobs_dashboard.html
```

---

## Run Validation Tests
```bash
python test_validation.py
```
