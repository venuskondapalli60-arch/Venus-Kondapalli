"""
output/dashboard_generator.py - Streamlined Modern Job Tracker & Application Hub

Generates jobs_dashboard.html with:
  - Unified Open Positions view with instant search and multi-dimensional filters
  - "Mark as Applied" flow that removes jobs from Open Positions into a dedicated History tracker
  - "Applied Jobs & History" tab with applied dates, interview statuses, personal notes, and CSV export
  - "Top Matches (70%+)" quick filter tab
  - "German Portals Hub" (47 target sites launchpad)
  - Dark executive glassmorphism aesthetic with responsive layouts and toast alerts
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config

logger = logging.getLogger(__name__)


class DashboardGenerator:
    """Generates the modern HTML jobs dashboard and application tracker."""

    def __init__(self):
        self.generated_at = datetime.now().strftime("%B %d, %Y at %I:%M %p")
        self.today = datetime.now().strftime("%Y-%m-%d")
        self.yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        self.three_days_ago = (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d")

    def generate(self, jobs: List[Dict], stats: Dict, run_id: int = 0) -> str:
        logger.info(f"Generating dashboard with {len(jobs)} jobs...")

        top_jobs = [j for j in jobs if j.get("match_score", 0) >= 70]

        html = self._build_html(
            all_jobs=jobs, top_jobs=top_jobs, stats=stats, run_id=run_id
        )

        with open(config.DASHBOARD_FILE, "w", encoding="utf-8") as f:
            f.write(html)

        # Mirror to index.html for web server support
        index_file = os.path.join(config.BASE_DIR, "index.html")
        try:
            with open(index_file, "w", encoding="utf-8") as f:
                f.write(html)
        except Exception as e:
            logger.warning(f"Could not mirror to index.html: {e}")

        logger.info(f"Dashboard generated: {config.DASHBOARD_FILE}")
        return config.DASHBOARD_FILE

    # ─────────────────────────────────────────────────────────────────────────

    def _build_html(self, all_jobs: List[Dict], top_jobs: List[Dict],
                    stats: Dict, run_id: int) -> str:

        jobs_json = json.dumps(all_jobs, ensure_ascii=False, default=str)
        jobs_json = jobs_json.replace("</script>", r"<\/script>")
        jobs_json = jobs_json.replace("</SCRIPT>", r"<\/SCRIPT>")

        companies = sorted(set(j.get("company", "") for j in all_jobs if j.get("company")))
        locations = sorted(set(
            j.get("location", "").split(",")[0].strip()
            for j in all_jobs if j.get("location")
        ))
        default_sources = [
            "Bundesagentur für Arbeit", "LinkedIn", "Indeed", "Glassdoor",
            "Shine", "Naukri", "Foundit", "Wellfound", "Instahyre", "Company Career Pages"
        ]
        sources = sorted(set(default_sources) | set(j.get("source", "") for j in all_jobs if j.get("source")))

        cand_name = config.RESUME_PROFILE.get("name", "Venus Kondapalli")
        cand_title = config.RESUME_PROFILE.get("title", "Product Manager & UI UX Design Expert")
        cand_exp = f"{config.RESUME_PROFILE.get('years_of_experience', 13)}+ Years"

        german_jobs_count = sum(
            1 for j in all_jobs
            if any(loc in (j.get("location") or "").lower()
                   for loc in ["germany", "deutschland", "berlin", "munich", "münchen", "frankfurt", "hamburg", "cologne", "köln", "stuttgart", "düsseldorf"])
            or j.get("source") == "Bundesagentur für Arbeit"
        )

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Job Tracker — {cand_name} ({cand_title})</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <style>{self._get_css()}</style>
</head>
<body>

<!-- ── AMBIENT BACKGROUND GLOW ─────────────────────────────────────────── -->
<div class="bg-orbs" aria-hidden="true">
    <div class="orb orb-1"></div>
    <div class="orb orb-2"></div>
    <div class="orb orb-3"></div>
</div>

<!-- ── HEADER & CANDIDATE PROFILE ───────────────────────────────────────── -->
<header class="header">
    <div class="header-inner">
        <div class="brand">
            <div class="brand-avatar">VK</div>
            <div class="brand-info">
                <div class="brand-title-row">
                    <h1 class="brand-name">{cand_name}</h1>
                    <span class="exp-badge">{cand_exp} Exp</span>
                    <span class="de-flag-badge" title="Targeting German Openings & B1 German">🇩🇪 B1 German</span>
                </div>
                <div class="brand-subtitle">
                    {cand_title} &nbsp;·&nbsp;
                    <span class="sub-highlight">ServiceNow</span> &nbsp;·&nbsp;
                    <span class="sub-highlight">AI Products</span> &nbsp;·&nbsp;
                    <span class="sub-highlight">Design Systems</span>
                </div>
            </div>
        </div>

        <div class="header-stats">
            <div class="stat-pill" onclick="switchView('open')">
                <span class="stat-num" id="statOpen">{len(all_jobs)}</span>
                <span class="stat-lbl">Open Jobs</span>
            </div>
            <div class="stat-pill" onclick="switchView('top')">
                <span class="stat-num" id="statTop">{len(top_jobs)}</span>
                <span class="stat-lbl">70%+ Matches</span>
            </div>
            <div class="stat-pill" onclick="filterByGermany()">
                <span class="stat-num" id="statGermany">{german_jobs_count}</span>
                <span class="stat-lbl">Germany Openings</span>
            </div>
            <div class="stat-pill stat-applied" onclick="switchView('applied')">
                <span class="stat-num" id="statApplied">0</span>
                <span class="stat-lbl">Applied / Tracked</span>
            </div>
        </div>
    </div>
</header>

<!-- ── VIEW NAVIGATION TABS ─────────────────────────────────────────────── -->
<nav class="nav-tabs-wrap">
    <div class="nav-tabs-inner">
        <button class="nav-tab active" id="tabBtn-open" onclick="switchView('open')">
            <span class="tab-ico">💼</span>
            <span class="tab-name">Open Positions</span>
            <span class="tab-counter" id="tabCountOpen">{len(all_jobs)}</span>
        </button>
        <button class="nav-tab" id="tabBtn-top" onclick="switchView('top')">
            <span class="tab-ico">🏆</span>
            <span class="tab-name">Top Matches (70%+)</span>
            <span class="tab-counter" id="tabCountTop">{len(top_jobs)}</span>
        </button>
        <button class="nav-tab" id="tabBtn-applied" onclick="switchView('applied')">
            <span class="tab-ico">📋</span>
            <span class="tab-name">Applied Jobs &amp; History</span>
            <span class="tab-counter tab-counter-green" id="tabCountApplied">0</span>
        </button>
        <button class="nav-tab" id="tabBtn-german" onclick="switchView('german')">
            <span class="tab-ico">🇩🇪</span>
            <span class="tab-name">German Portals Hub</span>
            <span class="tab-counter">47</span>
        </button>
    </div>
</nav>

<!-- ── FILTERS BAR (OPEN POSITIONS) ────────────────────────────────────── -->
<div class="filters-wrap" id="filtersBar">
    <div class="filters-inner">
        <div class="search-box">
            <svg class="search-ico" viewBox="0 0 20 20" fill="none">
                <circle cx="8.5" cy="8.5" r="5.5" stroke="currentColor" stroke-width="1.8"/>
                <path d="M13 13l3.5 3.5" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/>
            </svg>
            <input type="text" id="searchInput" placeholder="Search job title, company, skills, or city..." oninput="applyFilters()">
            <button class="btn-clear-search" id="clearSearchBtn" onclick="clearSearch()" style="display:none;">✕</button>
        </div>

        <div class="selects-row">
            {self._make_dropdown("locationFilter", "📍 All Locations", [("", "All Locations"), ("Germany", "🇩🇪 Germany (All)"), ("Berlin", "Berlin"), ("Munich", "Munich / München"), ("Frankfurt", "Frankfurt"), ("Hamburg", "Hamburg"), ("Remote", "🌐 Remote / Worldwide")] + [(l, l) for l in locations if l not in ["Berlin", "Munich", "Frankfurt", "Hamburg", "Remote", "Germany"]])}
            {self._make_dropdown("companyFilter", "🏢 All Companies", [("", "All Companies")] + [(c, c) for c in companies])}
            {self._make_dropdown("sourceFilter", "🔗 All Sources", [("", "All Sources")] + [(s, s) for s in sources])}
            {self._make_dropdown("scoreFilter", "⭐ All Scores", [("0","All Scores (60%+)"),("75","75%+ Elite"),("70","70%+ Top Tier"),("65","65%+ Strong")])}
            {self._make_dropdown("sortBy", "🏆 Highest Match", [("score","Highest Match"),("date","Newest First"),("company","Company A–Z")])}
            <button class="btn-reset" onclick="resetFilters()">↺ Reset</button>
        </div>

        <div class="results-meta">
            <div class="results-meta-left">
                Showing <strong id="visibleCount">{len(all_jobs)}</strong> open positions
                <span id="filterActiveBadge" class="filter-active-indicator" style="display:none;">· Filtered</span>
            </div>
            <div class="results-meta-right">
                <label class="toggle-label">
                    <input type="checkbox" id="hideDismissedToggle" checked onchange="applyFilters()">
                    <span>Hide dismissed jobs</span>
                </label>
                <div class="timestamp-tag">🕐 {self.generated_at}</div>
            </div>
        </div>
    </div>
</div>

<!-- ── MAIN CONTENT CONTAINER ───────────────────────────────────────────── -->
<main class="main-container">

    <!-- 1. OPEN POSITIONS VIEW -->
    <section class="view-section" id="view-open">
        <div class="jobs-grid" id="grid-open">
            {self._render_job_cards(all_jobs, run_id)}
        </div>
        <div id="empty-open" class="empty-state" style="display:none;">
            <div class="empty-icon">🔍</div>
            <h3>No open positions match your filters</h3>
            <p>Try resetting or broadening your search parameters.</p>
            <button class="btn-primary-action" onclick="resetFilters()">Reset All Filters</button>
        </div>
    </section>

    <!-- 2. APPLIED JOBS & HISTORY VIEW -->
    <section class="view-section" id="view-applied" style="display:none;">
        <div class="applied-tracker-header">
            <div class="applied-header-text">
                <h2>Application Tracker &amp; History</h2>
                <p>Track jobs you applied for, update interview stages, and add private notes.</p>
            </div>
            <div class="applied-header-actions">
                <button class="btn-export-csv" onclick="exportAppliedCSV()">📥 Export to CSV / Excel</button>
                <button class="btn-clear-history" onclick="clearAllApplied()">🗑 Clear History</button>
            </div>
        </div>

        <div class="applied-stats-row">
            <div class="app-stat-card">
                <span class="app-stat-val" id="appStatTotal">0</span>
                <span class="app-stat-lbl">Total Applied</span>
            </div>
            <div class="app-stat-card">
                <span class="app-stat-val" id="appStatInterviewing">0</span>
                <span class="app-stat-lbl">Interviewing</span>
            </div>
            <div class="app-stat-card">
                <span class="app-stat-val" id="appStatOffers">0</span>
                <span class="app-stat-lbl">Offers Received</span>
            </div>
        </div>

        <div class="applied-filter-box">
            <input type="text" id="appliedSearchInput" placeholder="Filter your applied applications..." oninput="renderAppliedView()">
        </div>

        <div class="jobs-grid" id="grid-applied">
            <!-- Dynamically populated from localStorage -->
        </div>

        <div id="empty-applied" class="empty-state" style="display:none;">
            <div class="empty-icon">📝</div>
            <h3>No applications tracked yet</h3>
            <p>Browse open positions and click <strong>"✓ Mark as Applied"</strong> on any card to move it here and track your interviews!</p>
            <button class="btn-primary-action" onclick="switchView('open')">Browse Open Positions</button>
        </div>
    </section>

    <!-- 3. GERMAN PORTALS DIRECTORY VIEW -->
    <section class="view-section" id="view-german" style="display:none;">
        {self._get_german_portals_html()}
    </section>

</main>

<!-- ── TOAST NOTIFICATION CONTAINER ────────────────────────────────────── -->
<div id="toastContainer" class="toast-container" aria-live="polite"></div>

<!-- ── FOOTER ───────────────────────────────────────────────────────────── -->
<footer class="footer">
    <p>Automated Job Search &amp; Tracker &nbsp;·&nbsp; Tailored for <strong>{cand_name}</strong> ({cand_title}) &nbsp;·&nbsp; Germany &amp; International</p>
    <p class="footer-sources">Sources: Bundesagentur für Arbeit · LinkedIn · Indeed DE &amp; IN · Glassdoor · Wellfound · Company Career Portals · StepStone</p>
</footer>

<!-- ── CLIENT-SIDE CONTROLLER SCRIPT ───────────────────────────────────── -->
<script>
const ALL_JOBS = {jobs_json};

        function applyFilters() {{
            const search   = (document.getElementById('searchInput').value || '').toLowerCase().trim();
            const company  = (document.getElementById('companyFilter').value || '').toLowerCase();
            const location = (document.getElementById('locationFilter').value || '').toLowerCase();
            const source   = (document.getElementById('sourceFilter').value || '').toLowerCase();
            const minScore = parseFloat(document.getElementById('scoreFilter').value) || 0;
            const sortBy   = document.getElementById('sortBy').value || 'score';
            const hideDismissed = document.getElementById('hideDismissedToggle').checked;

            const hasActiveFilters = search || company || location || source || minScore > 0;
            const ind = document.getElementById('filterActiveBadge');
            if (ind) ind.style.display = hasActiveFilters ? 'inline-block' : 'none';

            const clearBtn = document.getElementById('clearSearchBtn');
            if (clearBtn) clearBtn.style.display = search ? 'inline-block' : 'none';

            let filtered = ALL_JOBS.filter(j => {{
                const jid = String(j.job_id);
                // Exclude applied jobs from Open view
                if (appliedJobs[jid]) return false;
                // Exclude dismissed jobs if toggled
                if (hideDismissed && dismissedJobs[jid]) return false;

                // View constraint (if top tab active)
                if (currentView === 'top' && (j.match_score || 0) < 70) return false;

                const t = (j.title || '').toLowerCase();
                const c = (j.company || '').toLowerCase();
                const l = (j.location || '').toLowerCase();
                const d = (j.description || '').toLowerCase();
                const s = (j.source || '').toLowerCase();

                if (search && !t.includes(search) && !c.includes(search) && !l.includes(search) && !d.includes(search)) {{
                    return false;
                }}
                if (company && !c.includes(company)) return false;

                if (location) {{
                    if (location === 'germany') {{
                        const deMatches = ['germany', 'deutschland', 'berlin', 'munich', 'münchen', 'frankfurt', 'hamburg', 'cologne', 'köln', 'stuttgart', 'düsseldorf'];
                        const isDe = deMatches.some(city => l.includes(city)) || s.includes('bundesagentur');
                        if (!isDe) return false;
                    }} else if (!l.includes(location)) {{
                        return false;
                    }}
                }}

                if (source && !s.includes(source)) return false;
                if ((j.match_score || 0) < minScore) return false;

                return true;
            }});

            filtered.sort((a, b) => {{
                if (sortBy === 'score') return (b.match_score || 0) - (a.match_score || 0);
                if (sortBy === 'date') return (b.posted_date || '').localeCompare(a.posted_date || '');
                if (sortBy === 'company') return (a.company || '').localeCompare(b.company || '');
                return 0;
            }});

            const grid = document.getElementById('grid-open');
            const emptyState = document.getElementById('empty-open');

            if (filtered.length === 0) {{
                grid.innerHTML = '';
                emptyState.style.display = 'block';
            }} else {{
                emptyState.style.display = 'none';
                grid.innerHTML = filtered.map(j => renderCard(j)).join("");
            }}

            document.getElementById('visibleCount').textContent = filtered.length;
            updateBadges();
        }}

// ── State Management ────────────────────────────────────────────────────────
let currentView = 'open'; // 'open' | 'top' | 'applied' | 'german'
let appliedJobs = {{}};
let dismissedJobs = {{}};

function loadState() {{
    try {{
        appliedJobs = JSON.parse(localStorage.getItem('uiux_applied_jobs') || '{{}}');
    }} catch (e) {{ appliedJobs = {{}}; }}
    try {{
        dismissedJobs = JSON.parse(localStorage.getItem('uiux_dismissed_jobs') || '{{}}');
    }} catch (e) {{ dismissedJobs = {{}}; }}
}}

function saveState() {{
    localStorage.setItem('uiux_applied_jobs', JSON.stringify(appliedJobs));
    localStorage.setItem('uiux_dismissed_jobs', JSON.stringify(dismissedJobs));
    updateBadges();
}}

function updateBadges() {{
    const appliedList = Object.values(appliedJobs);
    const appliedCount = appliedList.length;

    const unappliedOpen = ALL_JOBS.filter(j => !appliedJobs[String(j.job_id)] && !dismissedJobs[String(j.job_id)]);
    const openCount = unappliedOpen.length;
    const topCount = unappliedOpen.filter(j => (j.match_score || 0) >= 70).length;

    const deMatches = ['germany', 'deutschland', 'berlin', 'munich', 'münchen', 'frankfurt', 'hamburg', 'cologne', 'köln', 'stuttgart', 'düsseldorf'];
    const deCount = unappliedOpen.filter(j => {{
        const l = (j.location || '').toLowerCase();
        const s = (j.source || '').toLowerCase();
        return deMatches.some(city => l.includes(city)) || s.includes('bundesagentur');
    }}).length;

    const elStatOpen = document.getElementById('statOpen');
    const elTabOpen = document.getElementById('tabCountOpen');
    if (elStatOpen) elStatOpen.textContent = openCount;
    if (elTabOpen) elTabOpen.textContent = openCount;

    const elStatTop = document.getElementById('statTop');
    const elTabTop = document.getElementById('tabCountTop');
    if (elStatTop) elStatTop.textContent = topCount;
    if (elTabTop) elTabTop.textContent = topCount;

    const elStatDe = document.getElementById('statGermany');
    if (elStatDe) elStatDe.textContent = deCount;

    const elStatApp = document.getElementById('statApplied');
    const elTabApp = document.getElementById('tabCountApplied');
    if (elStatApp) elStatApp.textContent = appliedCount;
    if (elTabApp) elTabApp.textContent = appliedCount;

    // Applied tab specific stats
    const interviewing = appliedList.filter(j => ['Interviewing', 'Screening', 'Technical Round', 'Final Round'].includes(j.status)).length;
    const offers = appliedList.filter(j => j.status === 'Offer Received').length;

    const elAppTotal = document.getElementById('appStatTotal');
    const elAppInt = document.getElementById('appStatInterviewing');
    const elAppOff = document.getElementById('appStatOffers');
    if (elAppTotal) elAppTotal.textContent = appliedCount;
    if (elAppInt) elAppInt.textContent = interviewing;
    if (elAppOff) elAppOff.textContent = offers;
}}

// ── Views & Tabs ─────────────────────────────────────────────────────────────
function switchView(viewName) {{
    currentView = viewName;
    ['open', 'top', 'applied', 'german'].forEach(v => {{
        const tabBtn = document.getElementById('tabBtn-' + v);
        if (tabBtn) tabBtn.classList.toggle('active', v === viewName);
    }});

    const viewOpen = document.getElementById('view-open');
    const viewApplied = document.getElementById('view-applied');
    const viewGerman = document.getElementById('view-german');
    const filtersBar = document.getElementById('filtersBar');

    if (viewName === 'open' || viewName === 'top') {{
        viewOpen.style.display = 'block';
        viewApplied.style.display = 'none';
        viewGerman.style.display = 'none';
        filtersBar.style.display = 'block';

        if (viewName === 'top') {{
            selectDd('scoreFilter', '70', document.querySelector('#scoreFilter-panel [data-val="70"]'));
        }} else {{
            selectDd('scoreFilter', '0', document.querySelector('#scoreFilter-panel [data-val="0"]'));
        }}
        applyFilters();
    }} else if (viewName === 'applied') {{
        viewOpen.style.display = 'none';
        viewApplied.style.display = 'block';
        viewGerman.style.display = 'none';
        filtersBar.style.display = 'none';
        renderAppliedView();
    }} else if (viewName === 'german') {{
        viewOpen.style.display = 'none';
        viewApplied.style.display = 'none';
        viewGerman.style.display = 'block';
        filtersBar.style.display = 'none';
    }}

    window.scrollTo({{ top: 0, behavior: 'smooth' }});
}}

function filterByGermany() {{
    switchView('open');
    const opt = document.querySelector('#locationFilter-panel [data-val="Germany"]');
    if (opt) selectDd('locationFilter', 'Germany', opt);
}}

// ── Application Tracking Actions ─────────────────────────────────────────────
function markAsApplied(jobId) {{
    const job = ALL_JOBS.find(j => String(j.job_id) === String(jobId));
    if (!job) return;

    const jid = String(jobId);
    const now = new Date();
    const dateFormatted = now.toLocaleDateString('en-US', {{ month: 'short', day: 'numeric', year: 'numeric' }}) +
                          ' at ' + now.toLocaleTimeString('en-US', {{ hour: '2-digit', minute: '2-digit' }});

    appliedJobs[jid] = {{
        job_id: jid,
        title: job.title || 'Untitled',
        company: job.company || 'Unknown',
        location: job.location || '',
        match_score: job.match_score || 0,
        source: job.source || '',
        apply_url: job.apply_url || job.url || '#',
        url: job.url || '#',
        posted_date: job.posted_date || '',
        applied_date: dateFormatted,
        status: 'Applied',
        notes: ''
    }};

    saveState();

    const card = document.querySelector(`.job-card[data-id="${{jobId}}"]`);
    if (card) {{
        card.classList.add('card-anim-out');
        setTimeout(() => {{
            applyFilters();
        }}, 280);
    }} else {{
        applyFilters();
    }}

    showToast(`✓ Marked as Applied: "${{esc(job.title)}}"`, [
        {{ text: 'Undo', onClick: () => unapplyJob(jid) }},
        {{ text: 'View History', onClick: () => switchView('applied') }}
    ]);
}}

function unapplyJob(jobId) {{
    const jid = String(jobId);
    if (appliedJobs[jid]) {{
        delete appliedJobs[jid];
        saveState();
        renderAppliedView();
        applyFilters();
        showToast('↩ Restored job back to Open Positions');
    }}
}}

function dismissJob(jobId) {{
    const jid = String(jobId);
    dismissedJobs[jid] = true;
    saveState();

    const card = document.querySelector(`.job-card[data-id="${{jobId}}"]`);
    if (card) {{
        card.classList.add('card-anim-out');
        setTimeout(() => {{
            applyFilters();
        }}, 280);
    }} else {{
        applyFilters();
    }}

    showToast('Job dismissed from list', [
        {{ text: 'Undo', onClick: () => {{ delete dismissedJobs[jid]; saveState(); applyFilters(); }} }}
    ]);
}}

function updateAppliedStatus(jobId, newStatus) {{
    const jid = String(jobId);
    if (appliedJobs[jid]) {{
        appliedJobs[jid].status = newStatus;
        saveState();
        showToast(`Status updated to "${{newStatus}}"`);
    }}
}}

function updateAppliedNotes(jobId, notesText) {{
    const jid = String(jobId);
    if (appliedJobs[jid]) {{
        appliedJobs[jid].notes = notesText;
        saveState();
    }}
}}

function renderAppliedView() {{
    const list = Object.values(appliedJobs);
    const search = (document.getElementById('appliedSearchInput').value || '').toLowerCase().trim();
    const grid = document.getElementById('grid-applied');
    const emptyState = document.getElementById('empty-applied');

    let filtered = list;
    if (search) {{
        filtered = list.filter(j =>
            (j.title || '').toLowerCase().includes(search) ||
            (j.company || '').toLowerCase().includes(search) ||
            (j.location || '').toLowerCase().includes(search) ||
            (j.notes || '').toLowerCase().includes(search)
        );
    }}

    if (list.length === 0 || filtered.length === 0) {{
        grid.innerHTML = '';
        emptyState.style.display = 'block';
    }} else {{
        emptyState.style.display = 'none';
        grid.innerHTML = filtered.map(j => renderAppliedCard(j)).join("");
    }}
    updateBadges();
}}

function renderAppliedCard(j) {{
    const score = j.match_score || 0;
    let scoreCls = 'orange';
    if (score >= 75) scoreCls = 'green';
    else if (score >= 70) scoreCls = 'blue';

    const statusOptions = ['Applied', 'Screening', 'Technical Round', 'Final Round', 'Offer Received', 'Rejected / Closed'];
    const statusSelectHtml = statusOptions.map(opt =>
        `<option value="${{opt}}" ${{j.status === opt ? 'selected' : ''}}>${{opt}}</option>`
    ).join('');

    return `
    <div class="job-card applied-card score-${{scoreCls}}" data-id="${{esc(j.job_id)}}">
        <div class="card-top">
            <div class="card-title-wrap">
                <span class="badge-applied-status badge-status-${{esc(j.status||'Applied').toLowerCase().replace(/[^a-z]/g,'')}}">${{esc(j.status||'Applied')}}</span>
                <h3 class="card-title"><a href="${{esc(j.apply_url)}}" target="_blank" rel="noopener noreferrer">${{esc(j.title)}}</a></h3>
            </div>
            <div class="score-ring score-${{scoreCls}}">
                <span class="ring-num">${{score}}%</span>
                <span class="ring-lbl">Match</span>
            </div>
        </div>

        <div class="card-meta">
            <span class="tag tag-company">🏢 ${{esc(j.company)}}</span>
            <span class="tag tag-loc">📍 ${{esc(j.location)}}</span>
            <span class="tag tag-src">🔗 ${{esc(j.source)}}</span>
            <span class="tag tag-applied-date">🕒 Applied: ${{esc(j.applied_date)}}</span>
        </div>

        <div class="applied-controls">
            <div class="status-selector-row">
                <label class="app-control-lbl">Stage:</label>
                <select class="status-dropdown" onchange="updateAppliedStatus('${{esc(j.job_id)}}', this.value)">
                    ${{statusSelectHtml}}
                </select>
            </div>
            <div class="notes-wrap">
                <textarea class="app-notes-input" placeholder="Add notes (e.g. recruiter name, salary, interview dates)..."
                          onblur="updateAppliedNotes('${{esc(j.job_id)}}', this.value)">${{esc(j.notes || '')}}</textarea>
            </div>
        </div>

        <div class="card-actions">
            <a href="${{esc(j.apply_url)}}" target="_blank" rel="noopener noreferrer" class="btn-apply">View Posting ↗</a>
            <button type="button" class="btn-action btn-restore" onclick="unapplyJob('${{esc(j.job_id)}}')">↩ Move Back to Open</button>
            <button type="button" class="btn-action btn-dismiss" onclick="unapplyJob('${{esc(j.job_id)}}')" title="Remove tracking">🗑</button>
        </div>
    </div>`;
}}

function exportAppliedCSV() {{
    const jobsList = Object.values(appliedJobs);
    if (!jobsList.length) {{
        showToast('No applied jobs tracked yet to export!');
        return;
    }}
    const headers = ['Title', 'Company', 'Location', 'Match Score', 'Source', 'Date Applied', 'Status', 'Notes', 'Job URL'];
    const rows = jobsList.map(j => [
        `"${{(j.title || '').replace(/"/g, '""')}}"`,
        `"${{(j.company || '').replace(/"/g, '""')}}"`,
        `"${{(j.location || '').replace(/"/g, '""')}}"`,
        `"${{j.match_score || ''}}"`,
        `"${{(j.source || '').replace(/"/g, '""')}}"`,
        `"${{(j.applied_date || '').replace(/"/g, '""')}}"`,
        `"${{(j.status || '').replace(/"/g, '""')}}"`,
        `"${{(j.notes || '').replace(/"/g, '""')}}"`,
        `"${{(j.apply_url || j.url || '').replace(/"/g, '""')}}"`
    ]);
    const csvContent = "data:text/csv;charset=utf-8,﻿" + [headers.join(","), ...rows.map(e => e.join(","))].join(String.fromCharCode(10));
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', `applied_jobs_venus_kondapalli_${{new Date().toISOString().split('T')[0]}}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    showToast('📥 Applications exported to CSV successfully!');
}}

function clearAllApplied() {{
    if (confirm('Are you sure you want to clear your application history? All tracked applications will return to Open Positions.')) {{
        appliedJobs = {{}};
        saveState();
        renderAppliedView();
        applyFilters();
        showToast('Application history cleared.');
    }}
}}

// ── Card Rendering (Open Positions) ──────────────────────────────────────────
function renderCard(j) {{
    const score = j.match_score || 0;
    let cls = 'orange', lbl = 'Good Match';
    if (score >= 75) {{ cls = 'green'; lbl = 'Top Fit'; }}
    else if (score >= 70) {{ cls = 'blue'; lbl = 'Strong Match'; }}

    const isNew = j.is_new === 1;
    const newBadge = isNew ? '<span class="badge-new">NEW</span>' : '';

    const locLower = (j.location || '').toLowerCase();
    const isGerman = ['germany', 'deutschland', 'berlin', 'munich', 'münchen', 'frankfurt', 'hamburg', 'cologne'].some(c => locLower.includes(c)) || (j.source === 'Bundesagentur für Arbeit');
    const deBadge = isGerman ? '<span class="badge-de" title="Germany Opening">🇩🇪 GERMANY</span>' : '';
    const remoteBadge = locLower.includes('remote') ? '<span class="badge-remote">🌐 REMOTE</span>' : '';

    const bd = j.score_breakdown || '';
    const applyUrl = j.apply_url || j.url || '#';

    return `
    <div class="job-card score-${{cls}}" data-id="${{esc(j.job_id)}}">
        <div class="card-top">
            <div class="card-title-wrap">
                <div class="card-badges-row">
                    ${{newBadge}}
                    ${{deBadge}}
                    ${{remoteBadge}}
                    <span class="badge-src">${{esc(j.source || '')}}</span>
                </div>
                <h3 class="card-title"><a href="${{esc(applyUrl)}}" target="_blank" rel="noopener noreferrer">${{esc(j.title)}}</a></h3>
            </div>
            <div class="score-ring score-${{cls}}">
                <span class="ring-num">${{score}}%</span>
                <span class="ring-lbl">${{lbl}}</span>
            </div>
        </div>
        <div class="card-meta">
            <span class="tag tag-company">🏢 ${{esc(j.company)}}</span>
            <span class="tag tag-loc">📍 ${{esc((j.location||'').split(',')[0])}}</span>
            <span class="tag tag-date">📅 ${{esc(j.posted_date||'Recently')}}</span>
        </div>
        ${{bd ? `<div class="card-breakdown">${{esc(bd)}}</div>` : ''}}
        <div class="card-actions">
            <a href="${{esc(applyUrl)}}" target="_blank" rel="noopener noreferrer" class="btn-apply">Apply Now ↗</a>
            <button type="button" class="btn-action btn-mark-applied" onclick="markAsApplied('${{esc(j.job_id)}}')" title="Mark as applied and move to History">
                ✓ Mark as Applied
            </button>
            <button type="button" class="btn-action btn-dismiss" onclick="dismissJob('${{esc(j.job_id)}}')" title="Remove from list">✕</button>
        </div>
    </div>`;
}}

function esc(s) {{
    return String(s || '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;').replace(/'/g,'&#39;');
}}

// ── Dropdown Control ─────────────────────────────────────────────────────────
function toggleDd(id) {{
    const panel = document.getElementById(id + '-panel');
    const wrap  = document.getElementById(id + '-wrap');
    const isOpen = panel.classList.contains('open');
    closeAllDd();
    if (!isOpen) {{
        panel.classList.add('open');
        wrap.classList.add('open');
    }}
}}

function selectDd(id, val, el) {{
    document.getElementById(id).value = val;
    if (el) {{
        document.getElementById(id + '-lbl').textContent = el.textContent;
        document.querySelectorAll('#' + id + '-panel .cdd-opt').forEach(o => o.classList.remove('active'));
        el.classList.add('active');
    }}
    const panel = document.getElementById(id + '-panel');
    const wrap  = document.getElementById(id + '-wrap');
    if (panel) panel.classList.remove('open');
    if (wrap) wrap.classList.remove('open');
    applyFilters();
}}

function closeAllDd() {{
    document.querySelectorAll('.cdd-panel').forEach(p => p.classList.remove('open'));
    document.querySelectorAll('.cdd').forEach(w => w.classList.remove('open'));
}}

document.addEventListener('click', e => {{
    if (!e.target.closest('.cdd')) closeAllDd();
}});

function resetFilters() {{
    document.getElementById('searchInput').value = '';
    selectDd('locationFilter', '', document.querySelector('#locationFilter-panel [data-val=""]'));
    selectDd('companyFilter', '', document.querySelector('#companyFilter-panel [data-val=""]'));
    selectDd('sourceFilter', '', document.querySelector('#sourceFilter-panel [data-val=""]'));
    selectDd('scoreFilter', '0', document.querySelector('#scoreFilter-panel [data-val="0"]'));
    selectDd('sortBy', 'score', document.querySelector('#sortBy-panel [data-val="score"]'));
    applyFilters();
    showToast('Filters reset to default');
}}

function clearSearch() {{
    document.getElementById('searchInput').value = '';
    applyFilters();
}}

// ── Toast Notification System ────────────────────────────────────────────────
function showToast(message, actions = []) {{
    const container = document.getElementById('toastContainer');
    const toast = document.createElement('div');
    toast.className = 'toast';

    let actionsHtml = '';
    if (actions.length) {{
        actionsHtml = '<div class="toast-actions">' + actions.map((a, i) =>
            `<button type="button" class="toast-btn" id="toast-btn-${{i}}">${{a.text}}</button>`
        ).join('') + '</div>';
    }}

    toast.innerHTML = `<span class="toast-msg">${{message}}</span>${{actionsHtml}}`;
    container.appendChild(toast);

    actions.forEach((a, i) => {{
        const btn = toast.querySelector(`#toast-btn-${{i}}`);
        if (btn) {{
            btn.onclick = () => {{
                a.onClick();
                removeToast(toast);
            }};
        }}
    }});

    setTimeout(() => removeToast(toast), 4500);
}}

function removeToast(toast) {{
    toast.classList.add('toast-hide');
    setTimeout(() => {{ if (toast.parentNode) toast.parentNode.removeChild(toast); }}, 300);
}}

// ── Init ─────────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {{
    loadState();
    updateBadges();
    applyFilters();
}});
</script>
</body>
</html>"""

    # ─────────────────────────────────────────────────────────────────────────

    def _render_job_cards(self, jobs: List[Dict], run_id: int, highlight: bool = False) -> str:
        if not jobs:
            return ""
        return "\n".join(self._render_single_card(j, run_id, highlight) for j in jobs)

    def _render_single_card(self, job: Dict, run_id: int, highlight: bool = False) -> str:
        score = job.get("match_score", 0)
        is_new = job.get("is_new", 0) == 1 or job.get("run_id") == run_id

        if score >= 75:
            score_cls, score_lbl = "green", "Top Fit"
        elif score >= 70:
            score_cls, score_lbl = "blue", "Strong Match"
        else:
            score_cls, score_lbl = "orange", "Good Match"

        new_badge = '<span class="badge-new">NEW</span>' if is_new else ""

        loc_lower = (job.get("location") or "").lower()
        is_german = any(c in loc_lower for c in ["germany", "deutschland", "berlin", "munich", "münchen", "frankfurt", "hamburg", "cologne"]) or (job.get("source") == "Bundesagentur für Arbeit")
        de_badge = '<span class="badge-de" title="Germany Opening">🇩🇪 GERMANY</span>' if is_german else ""
        remote_badge = '<span class="badge-remote">🌐 REMOTE</span>' if "remote" in loc_lower else ""

        title = self._esc(job.get("title", "Untitled"))
        company = self._esc(job.get("company", "Unknown"))
        location = self._esc(job.get("location", "Location Unspecified").split(",")[0].strip())
        source = self._esc(job.get("source", ""))
        apply_url = self._esc(job.get("apply_url") or job.get("url", "#"))
        job_id = self._esc(job.get("job_id", ""))
        breakdown = self._esc(job.get("score_breakdown", ""))
        posted_lbl = self._format_date_label(job.get("posted_date", ""))

        return f"""
        <div class="job-card score-{score_cls}" data-id="{job_id}">
            <div class="card-top">
                <div class="card-title-wrap">
                    <div class="card-badges-row">
                        {new_badge}
                        {de_badge}
                        {remote_badge}
                        <span class="badge-src">{source}</span>
                    </div>
                    <h3 class="card-title"><a href="{apply_url}" target="_blank" rel="noopener noreferrer">{title}</a></h3>
                </div>
                <div class="score-ring score-{score_cls}">
                    <span class="ring-num">{score}%</span>
                    <span class="ring-lbl">{score_lbl}</span>
                </div>
            </div>
            <div class="card-meta">
                <span class="tag tag-company">🏢 {company}</span>
                <span class="tag tag-loc">📍 {location}</span>
                <span class="tag tag-date">📅 {posted_lbl}</span>
            </div>
            {f'<div class="card-breakdown">{breakdown}</div>' if breakdown else ''}
            <div class="card-actions">
                <a href="{apply_url}" target="_blank" rel="noopener noreferrer" class="btn-apply">Apply Now ↗</a>
                <button type="button" class="btn-action btn-mark-applied" onclick="markAsApplied('{job_id}')" title="Mark as applied and move to History">
                    ✓ Mark as Applied
                </button>
                <button type="button" class="btn-action btn-dismiss" onclick="dismissJob('{job_id}')" title="Remove from list">✕</button>
            </div>
        </div>"""

    def _empty_state(self, jobs: List, message: str) -> str:
        if jobs:
            return ""
        return f"""
        <div class="empty-state">
            <div class="empty-icon">📭</div>
            <p>{message}</p>
        </div>"""

    def _format_date_label(self, date_str: str) -> str:
        if not date_str or date_str == "Recently":
            return "Recently"
        try:
            dt = datetime.strptime(date_str, "%Y-%m-%d")
            diff = (datetime.now().date() - dt.date()).days
            if diff == 0:   return "Today"
            if diff == 1:   return "Yesterday"
            if diff <= 7:   return f"{diff}d ago"
            return dt.strftime("%b %d")
        except ValueError:
            return date_str

    def _make_dropdown(self, field_id: str, placeholder: str, options: list) -> str:
        items_html = ""
        for val, label in options:
            items_html += (
                f'<div class="cdd-opt" data-val="{self._esc(str(val))}" '
                f'onclick="selectDd(\'{field_id}\',\'{self._esc(str(val))}\', this)">{self._esc(label)}</div>\n'
            )
        return f"""
<div class="cdd" id="{field_id}-wrap">
    <button type="button" class="cdd-btn" onclick="toggleDd('{field_id}')">
        <span class="cdd-lbl" id="{field_id}-lbl">{placeholder}</span>
        <svg class="cdd-arrow" viewBox="0 0 10 6" fill="none">
            <path d="M1 1l4 4 4-4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
    </button>
    <input type="hidden" id="{field_id}" value="{options[0][0] if options else ''}">
    <div class="cdd-panel" id="{field_id}-panel">
        {items_html}
    </div>
</div>"""

    @staticmethod
    def _esc(text: str) -> str:
        return (str(text)
                .replace("&", "&amp;").replace("<", "&lt;")
                .replace(">", "&gt;").replace('"', "&quot;")
                .replace("'", "&#39;"))

    def _get_german_portals_html(self) -> str:
        portals = getattr(config, "GERMAN_JOB_PORTALS", [])
        if not portals:
            return ""

        categories = {}
        for p in portals:
            cat = p.get("category", "General")
            categories.setdefault(cat, []).append(p)

        cat_blocks = []
        for cat, items in categories.items():
            pills = []
            for p in items:
                name = self._esc(p.get("name", ""))
                url = self._esc(p.get("url", "#"))
                pills.append(
                    f'<a href="{url}" target="_blank" rel="noopener noreferrer" class="de-pill" title="{name}">'
                    f'<span class="de-name">{name}</span> ↗</a>'
                )
            cat_blocks.append(f"""
            <div class="de-cat-group">
                <h4 class="de-cat-title">{self._esc(cat)}</h4>
                <div class="de-cat-grid">{"".join(pills)}</div>
            </div>
            """)

        return f"""
<div class="de-hub-wrap">
    <div class="de-hub-banner">
        <div class="de-hub-title-row">
            <span class="de-badge">🇩🇪 FOCUS DIRECTORY</span>
            <h3>Germany Job Search Launchpad ({len(portals)} Portals)</h3>
        </div>
        <p class="de-hub-desc">Direct search links pre-filtered for Product Management and UI/UX Design positions across all 47 requested German platforms.</p>
    </div>
    <div class="de-categories-container">
        {"".join(cat_blocks)}
    </div>
</div>"""

    # ─────────────────────────────────────────────────────────────────────────
    # CSS
    # ─────────────────────────────────────────────────────────────────────────

    def _get_css(self) -> str:
        return """
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
body {
    background-color: #080c14;
    color: #e2e8f0;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    min-height: 100vh;
    overflow-x: hidden;
    line-height: 1.5;
}

/* ── AMBIENT ORBS ───────────────────────────────────────────────────────── */
.bg-orbs {
    position: fixed; inset: 0; pointer-events: none; z-index: 0; overflow: hidden;
}
.orb {
    position: absolute; border-radius: 50%; filter: blur(140px); opacity: 0.15;
}
.orb-1 { width: 550px; height: 550px; background: #6366f1; top: -100px; left: -100px; }
.orb-2 { width: 600px; height: 600px; background: #06b6d4; top: 30%; right: -150px; }
.orb-3 { width: 450px; height: 450px; background: #10b981; bottom: -100px; left: 20%; }

/* ── HEADER ─────────────────────────────────────────────────────────────── */
.header {
    position: relative; z-index: 10;
    background: rgba(13, 20, 36, 0.85);
    border-bottom: 1px solid rgba(255, 255, 255, 0.08);
    backdrop-filter: blur(16px);
    padding: 22px 32px;
}
.header-inner {
    max-width: 1440px; margin: 0 auto;
    display: flex; align-items: center; justify-content: space-between; gap: 24px;
    flex-wrap: wrap;
}
.brand { display: flex; align-items: center; gap: 16px; }
.brand-avatar {
    width: 48px; height: 48px; border-radius: 14px;
    background: linear-gradient(135deg, #6366f1 0%, #06b6d4 100%);
    color: #fff; font-weight: 800; font-size: 1.15rem;
    display: flex; align-items: center; justify-content: center;
    box-shadow: 0 4px 18px rgba(99, 102, 241, 0.35);
}
.brand-title-row { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
.brand-name { font-size: 1.35rem; font-weight: 800; color: #fff; letter-spacing: -0.02em; }
.exp-badge {
    background: rgba(99, 102, 241, 0.15); border: 1px solid rgba(99, 102, 241, 0.35);
    color: #a5b4fc; font-size: 0.75rem; font-weight: 700; padding: 3px 9px; border-radius: 20px;
}
.de-flag-badge {
    background: rgba(255, 215, 0, 0.12); border: 1px solid rgba(255, 215, 0, 0.3);
    color: #ffd700; font-size: 0.75rem; font-weight: 700; padding: 3px 9px; border-radius: 20px;
}
.brand-subtitle { font-size: 0.88rem; color: #94a3b8; margin-top: 3px; }
.sub-highlight { color: #cbd5e1; font-weight: 500; }

.header-stats { display: flex; align-items: center; gap: 12px; flex-wrap: wrap; }
.stat-pill {
    background: rgba(255, 255, 255, 0.04);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 12px; padding: 8px 16px; text-align: center;
    cursor: pointer; transition: all 0.2s ease;
}
.stat-pill:hover {
    background: rgba(255, 255, 255, 0.08); border-color: rgba(99, 102, 241, 0.4);
    transform: translateY(-2px);
}
.stat-pill.stat-applied {
    background: rgba(16, 185, 129, 0.08); border-color: rgba(16, 185, 129, 0.25);
}
.stat-pill.stat-applied:hover {
    background: rgba(16, 185, 129, 0.15); border-color: rgba(16, 185, 129, 0.5);
}
.stat-num { display: block; font-size: 1.25rem; font-weight: 800; color: #fff; line-height: 1.1; }
.stat-applied .stat-num { color: #34d399; }
.stat-lbl { font-size: 0.72rem; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.05em; }

/* ── VIEW NAVIGATION TABS ─────────────────────────────────────────────── */
.nav-tabs-wrap {
    position: sticky; top: 0; z-index: 20;
    background: rgba(8, 12, 20, 0.95);
    border-bottom: 1px solid rgba(255, 255, 255, 0.08);
    backdrop-filter: blur(20px);
}
.nav-tabs-inner {
    max-width: 1440px; margin: 0 auto; padding: 0 32px;
    display: flex; gap: 8px; overflow-x: auto;
}
.nav-tab {
    background: transparent; border: none; outline: none;
    color: #94a3b8; font-weight: 600; font-size: 0.92rem;
    padding: 16px 20px; display: flex; align-items: center; gap: 8px;
    cursor: pointer; position: relative; transition: all 0.2s ease;
    white-space: nowrap;
}
.nav-tab:hover { color: #fff; }
.nav-tab.active { color: #6366f1; }
.nav-tab.active::after {
    content: ''; position: absolute; bottom: 0; left: 0; right: 0; height: 2px;
    background: linear-gradient(90deg, #6366f1, #06b6d4);
    box-shadow: 0 -2px 8px rgba(99, 102, 241, 0.5);
}
.tab-counter {
    background: rgba(255, 255, 255, 0.08); color: #cbd5e1;
    font-size: 0.72rem; font-weight: 700; padding: 2px 7px; border-radius: 10px;
}
.nav-tab.active .tab-counter { background: rgba(99, 102, 241, 0.2); color: #a5b4fc; }
.tab-counter-green { background: rgba(16, 185, 129, 0.18); color: #34d399; }

/* ── FILTERS BAR ──────────────────────────────────────────────────────── */
.filters-wrap {
    position: relative; z-index: 15;
    background: rgba(13, 20, 36, 0.6);
    border-bottom: 1px solid rgba(255, 255, 255, 0.06);
    padding: 18px 32px;
}
.filters-inner { max-width: 1440px; margin: 0 auto; display: flex; flex-direction: column; gap: 14px; }
.search-box {
    position: relative; display: flex; align-items: center; width: 100%;
}
.search-ico {
    position: absolute; left: 16px; width: 18px; height: 18px;
    color: #64748b; pointer-events: none;
}
.search-box input {
    width: 100%; background: rgba(255, 255, 255, 0.04);
    border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 12px;
    padding: 13px 44px 13px 46px; color: #fff; font-size: 0.95rem;
    outline: none; transition: all 0.2s ease;
}
.search-box input:focus {
    background: rgba(255, 255, 255, 0.07); border-color: #6366f1;
    box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.2);
}
.btn-clear-search {
    position: absolute; right: 14px; background: rgba(255, 255, 255, 0.1);
    border: none; color: #94a3b8; border-radius: 50%; width: 22px; height: 22px;
    font-size: 0.75rem; cursor: pointer; display: flex; align-items: center; justify-content: center;
}
.selects-row {
    display: flex; gap: 10px; flex-wrap: wrap; align-items: center;
}
.btn-reset {
    background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255, 255, 255, 0.1);
    color: #94a3b8; font-weight: 600; font-size: 0.82rem; padding: 8px 14px;
    border-radius: 9px; cursor: pointer; transition: all 0.2s ease;
}
.btn-reset:hover { background: rgba(255, 255, 255, 0.1); color: #fff; }

.results-meta {
    display: flex; align-items: center; justify-content: space-between; gap: 16px;
    font-size: 0.85rem; color: #94a3b8; flex-wrap: wrap;
}
.results-meta strong { color: #fff; }
.filter-active-indicator {
    background: rgba(99, 102, 241, 0.2); color: #a5b4fc;
    font-size: 0.72rem; padding: 2px 7px; border-radius: 6px; font-weight: 600;
}
.results-meta-right { display: flex; align-items: center; gap: 18px; }
.toggle-label {
    display: flex; align-items: center; gap: 7px; cursor: pointer; user-select: none;
    font-size: 0.82rem; color: #cbd5e1;
}
.timestamp-tag { font-size: 0.78rem; color: #64748b; }

/* ── CUSTOM DROPDOWN ──────────────────────────────────────────────────── */
.cdd { position: relative; }
.cdd-btn {
    background: rgba(255, 255, 255, 0.04);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 9px; padding: 8px 14px; color: #cbd5e1;
    font-size: 0.82rem; font-weight: 500; cursor: pointer;
    display: flex; align-items: center; gap: 8px; transition: all 0.2s ease;
}
.cdd-btn:hover, .cdd.open .cdd-btn {
    background: rgba(255, 255, 255, 0.08); border-color: rgba(99, 102, 241, 0.4); color: #fff;
}
.cdd-arrow { width: 9px; height: 6px; color: #94a3b8; transition: transform 0.2s ease; }
.cdd.open .cdd-arrow { transform: rotate(180deg); }
.cdd-panel {
    display: none; position: absolute; top: calc(100% + 6px); left: 0; z-index: 100;
    min-width: 200px; max-height: 280px; overflow-y: auto;
    background: #0f172a; border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 10px; padding: 6px; box-shadow: 0 12px 36px rgba(0, 0, 0, 0.6);
}
.cdd-panel.open { display: block; animation: fadeInDd 0.15s ease-out; }
@keyframes fadeInDd { from { opacity: 0; transform: translateY(-4px); } to { opacity: 1; transform: translateY(0); } }
.cdd-opt {
    padding: 7px 11px; border-radius: 6px; font-size: 0.8rem; color: #94a3b8;
    cursor: pointer; transition: all 0.15s ease;
}
.cdd-opt:hover { background: rgba(99, 102, 241, 0.15); color: #fff; }
.cdd-opt.active { background: rgba(99, 102, 241, 0.25); color: #a5b4fc; font-weight: 600; }

/* ── MAIN CONTENT ─────────────────────────────────────────────────────── */
.main-container {
    max-width: 1440px; margin: 0 auto; padding: 28px 32px 80px;
    position: relative; z-index: 5;
}
.jobs-grid {
    display: grid; grid-template-columns: repeat(auto-fill, minmax(380px, 1fr)); gap: 20px;
}

/* ── JOB CARD ─────────────────────────────────────────────────────────── */
.job-card {
    background: rgba(255, 255, 255, 0.035);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 16px; padding: 20px;
    display: flex; flex-direction: column; gap: 14px;
    backdrop-filter: blur(12px);
    transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
    position: relative;
}
.job-card:hover {
    background: rgba(255, 255, 255, 0.06);
    border-color: rgba(99, 102, 241, 0.35);
    transform: translateY(-3px);
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.35);
}
.job-card.card-anim-out {
    opacity: 0; transform: scale(0.95) translateY(10px);
    transition: all 0.28s ease;
}

.card-top { display: flex; justify-content: space-between; align-items: flex-start; gap: 14px; }
.card-title-wrap { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 6px; }
.card-badges-row { display: flex; align-items: center; gap: 6px; flex-wrap: wrap; }
.card-title {
    font-size: 1.05rem; font-weight: 700; color: #fff; line-height: 1.35;
    word-break: break-word;
}
.card-title a { color: #fff; text-decoration: none; transition: color 0.2s ease; }
.card-title a:hover { color: #6366f1; }

/* Badges */
.badge-new {
    background: linear-gradient(135deg, #ec4899, #8b5cf6); color: #fff;
    font-size: 0.68rem; font-weight: 800; padding: 2px 7px; border-radius: 6px; letter-spacing: 0.5px;
}
.badge-de {
    background: rgba(255, 215, 0, 0.15); border: 1px solid rgba(255, 215, 0, 0.35);
    color: #ffd700; font-size: 0.68rem; font-weight: 800; padding: 2px 7px; border-radius: 6px;
}
.badge-remote {
    background: rgba(6, 182, 212, 0.15); border: 1px solid rgba(6, 182, 212, 0.35);
    color: #22d3ee; font-size: 0.68rem; font-weight: 700; padding: 2px 7px; border-radius: 6px;
}
.badge-src {
    background: rgba(255, 255, 255, 0.05); color: #94a3b8;
    font-size: 0.68rem; padding: 2px 7px; border-radius: 6px;
}

/* Score Ring */
.score-ring {
    min-width: 64px; border-radius: 12px; padding: 6px 8px; text-align: center;
    display: flex; flex-direction: column; align-items: center; justify-content: center;
    border: 1px solid transparent;
}
.score-ring.score-green {
    background: rgba(16, 185, 129, 0.12); border-color: rgba(16, 185, 129, 0.35); color: #34d399;
}
.score-ring.score-blue {
    background: rgba(99, 102, 241, 0.14); border-color: rgba(99, 102, 241, 0.35); color: #818cf8;
}
.score-ring.score-orange {
    background: rgba(245, 158, 11, 0.12); border-color: rgba(245, 158, 11, 0.35); color: #fbbf24;
}
.ring-num { font-size: 1.08rem; font-weight: 800; line-height: 1; }
.ring-lbl { font-size: 0.62rem; text-transform: uppercase; font-weight: 700; opacity: 0.85; margin-top: 2px; }

/* Card Meta */
.card-meta { display: flex; flex-wrap: wrap; gap: 8px 12px; font-size: 0.82rem; color: #94a3b8; }
.tag-company { color: #e2e8f0; font-weight: 600; }
.card-breakdown {
    background: rgba(255, 255, 255, 0.025); border-left: 2px solid rgba(99, 102, 241, 0.4);
    padding: 6px 10px; font-size: 0.78rem; color: #cbd5e1; border-radius: 0 6px 6px 0;
}

/* Card Actions */
.card-actions { display: flex; align-items: center; gap: 8px; margin-top: auto; padding-top: 8px; }
.btn-apply {
    flex: 1; background: linear-gradient(135deg, #4f46e5 0%, #06b6d4 100%);
    color: #fff; font-weight: 700; font-size: 0.84rem; padding: 9px 16px;
    border-radius: 10px; text-align: center; text-decoration: none;
    transition: all 0.2s ease; box-shadow: 0 4px 14px rgba(79, 70, 229, 0.25);
}
.btn-apply:hover {
    box-shadow: 0 6px 20px rgba(79, 70, 229, 0.45); filter: brightness(1.1); transform: translateY(-1px);
}
.btn-action {
    background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 10px; padding: 8px 13px; font-size: 0.8rem; font-weight: 600;
    cursor: pointer; transition: all 0.2s ease; display: flex; align-items: center; justify-content: center;
}
.btn-mark-applied {
    background: rgba(16, 185, 129, 0.1); border-color: rgba(16, 185, 129, 0.25); color: #34d399;
}
.btn-mark-applied:hover {
    background: rgba(16, 185, 129, 0.22); border-color: rgba(16, 185, 129, 0.5); color: #fff;
}
.btn-dismiss { color: #94a3b8; width: 36px; }
.btn-dismiss:hover { background: rgba(239, 68, 68, 0.15); border-color: rgba(239, 68, 68, 0.35); color: #f87171; }

/* ── APPLIED TRACKER VIEW ─────────────────────────────────────────────── */
.applied-tracker-header {
    display: flex; justify-content: space-between; align-items: center; gap: 20px;
    margin-bottom: 24px; flex-wrap: wrap;
}
.applied-header-text h2 { font-size: 1.4rem; font-weight: 800; color: #fff; }
.applied-header-text p { color: #94a3b8; font-size: 0.88rem; margin-top: 4px; }
.applied-header-actions { display: flex; align-items: center; gap: 10px; }
.btn-export-csv {
    background: linear-gradient(135deg, #10b981 0%, #059669 100%);
    color: #fff; font-weight: 700; font-size: 0.84rem; padding: 10px 18px;
    border-radius: 10px; border: none; cursor: pointer; transition: all 0.2s ease;
}
.btn-export-csv:hover { filter: brightness(1.1); transform: translateY(-1px); }
.btn-clear-history {
    background: rgba(239, 68, 68, 0.1); border: 1px solid rgba(239, 68, 68, 0.25);
    color: #f87171; font-weight: 600; font-size: 0.84rem; padding: 9px 14px;
    border-radius: 10px; cursor: pointer; transition: all 0.2s ease;
}
.btn-clear-history:hover { background: rgba(239, 68, 68, 0.2); }

.applied-stats-row {
    display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px;
    margin-bottom: 24px;
}
.app-stat-card {
    background: rgba(255, 255, 255, 0.035); border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 14px; padding: 18px 20px; text-align: center;
}
.app-stat-val { font-size: 1.6rem; font-weight: 800; color: #34d399; display: block; }
.app-stat-lbl { font-size: 0.78rem; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.05em; margin-top: 4px; }

.applied-filter-box { margin-bottom: 24px; }
.applied-filter-box input {
    width: 100%; background: rgba(255, 255, 255, 0.04);
    border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 12px;
    padding: 12px 18px; color: #fff; font-size: 0.9rem; outline: none;
}
.applied-filter-box input:focus {
    border-color: #10b981; box-shadow: 0 0 0 3px rgba(16, 185, 129, 0.2);
}

.applied-card { border-left: 3px solid #10b981; }
.badge-applied-status {
    font-size: 0.68rem; font-weight: 800; padding: 2px 8px; border-radius: 6px; text-transform: uppercase;
}
.badge-status-applied { background: rgba(59, 130, 246, 0.18); color: #60a5fa; border: 1px solid rgba(59, 130, 246, 0.35); }
.badge-status-screening { background: rgba(245, 158, 11, 0.18); color: #fbbf24; border: 1px solid rgba(245, 158, 11, 0.35); }
.badge-status-technicalround { background: rgba(139, 92, 246, 0.18); color: #c084fc; border: 1px solid rgba(139, 92, 246, 0.35); }
.badge-status-finalround { background: rgba(236, 72, 153, 0.18); color: #f472b6; border: 1px solid rgba(236, 72, 153, 0.35); }
.badge-status-offerreceived { background: rgba(16, 185, 129, 0.22); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.45); }
.badge-status-rejectedclosed { background: rgba(148, 163, 184, 0.15); color: #94a3b8; border: 1px solid rgba(148, 163, 184, 0.3); }

.tag-applied-date { color: #34d399; font-weight: 500; }
.applied-controls {
    display: flex; flex-direction: column; gap: 10px;
    background: rgba(0, 0, 0, 0.25); border-radius: 10px; padding: 12px;
}
.status-selector-row { display: flex; align-items: center; gap: 10px; }
.app-control-lbl { font-size: 0.78rem; color: #94a3b8; font-weight: 600; }
.status-dropdown {
    background: #1e293b; border: 1px solid rgba(255, 255, 255, 0.12);
    color: #fff; font-size: 0.8rem; font-weight: 600; padding: 5px 10px;
    border-radius: 8px; outline: none; cursor: pointer; flex: 1;
}
.app-notes-input {
    width: 100%; background: #0b1120; border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 8px; padding: 8px 10px; color: #e2e8f0; font-size: 0.8rem;
    outline: none; resize: vertical; min-height: 50px; font-family: inherit;
}
.app-notes-input:focus { border-color: #6366f1; }
.btn-restore {
    background: rgba(99, 102, 241, 0.1); border-color: rgba(99, 102, 241, 0.3); color: #a5b4fc;
}
.btn-restore:hover { background: rgba(99, 102, 241, 0.2); color: #fff; }

/* ── GERMAN DIRECTORY ─────────────────────────────────────────────────── */
.de-hub-wrap { display: flex; flex-direction: column; gap: 24px; }
.de-hub-banner {
    background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 215, 0, 0.25);
    border-radius: 16px; padding: 24px;
}
.de-hub-title-row { display: flex; align-items: center; gap: 12px; margin-bottom: 8px; }
.de-badge {
    background: linear-gradient(135deg, #dd0000, #ffcc00); color: #111;
    font-weight: 800; font-size: 0.72rem; padding: 3px 8px; border-radius: 6px;
}
.de-hub-banner h3 { color: #fff; font-size: 1.25rem; font-weight: 800; }
.de-hub-desc { color: #94a3b8; font-size: 0.88rem; }
.de-categories-container { display: flex; flex-direction: column; gap: 24px; }
.de-cat-group {
    background: rgba(255, 255, 255, 0.025); border: 1px solid rgba(255, 255, 255, 0.06);
    border-radius: 14px; padding: 20px;
}
.de-cat-title {
    font-size: 0.92rem; font-weight: 700; color: #a5b4fc; text-transform: uppercase;
    letter-spacing: 0.05em; margin-bottom: 14px;
}
.de-cat-grid {
    display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 10px;
}
.de-pill {
    background: rgba(255, 255, 255, 0.04); border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 9px; padding: 9px 12px; color: #e2e8f0; font-size: 0.82rem;
    text-decoration: none; display: flex; justify-content: space-between; align-items: center;
    transition: all 0.2s ease;
}
.de-pill:hover {
    background: rgba(255, 215, 0, 0.12); border-color: rgba(255, 215, 0, 0.4); color: #fff;
    transform: translateY(-2px);
}

/* ── EMPTY STATE ──────────────────────────────────────────────────────── */
.empty-state {
    text-align: center; padding: 60px 20px; background: rgba(255, 255, 255, 0.02);
    border: 1px dashed rgba(255, 255, 255, 0.1); border-radius: 16px; margin: 20px 0;
}
.empty-icon { font-size: 2.8rem; margin-bottom: 12px; opacity: 0.85; }
.empty-state h3 { font-size: 1.15rem; font-weight: 700; color: #fff; margin-bottom: 6px; }
.empty-state p { color: #94a3b8; font-size: 0.88rem; max-width: 440px; margin: 0 auto 18px; }
.btn-primary-action {
    background: linear-gradient(135deg, #6366f1, #06b6d4); color: #fff; font-weight: 700;
    font-size: 0.85rem; padding: 9px 18px; border-radius: 9px; border: none; cursor: pointer;
}

/* ── TOASTS ───────────────────────────────────────────────────────────── */
.toast-container {
    position: fixed; bottom: 24px; right: 24px; z-index: 1000;
    display: flex; flex-direction: column; gap: 10px; pointer-events: none;
}
.toast {
    background: #0f172a; border: 1px solid rgba(99, 102, 241, 0.4);
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.6);
    color: #fff; padding: 12px 18px; border-radius: 12px; font-size: 0.85rem;
    display: flex; align-items: center; gap: 14px; pointer-events: auto;
    animation: toastSlideIn 0.25s cubic-bezier(0.16, 1, 0.3, 1);
}
@keyframes toastSlideIn { from { transform: translateY(100%); opacity: 0; } to { transform: translateY(0); opacity: 1; } }
.toast.toast-hide { opacity: 0; transform: translateY(10px); transition: all 0.25s ease; }
.toast-msg { font-weight: 500; }
.toast-actions { display: flex; gap: 8px; }
.toast-btn {
    background: rgba(255, 255, 255, 0.1); border: none; color: #a5b4fc;
    font-size: 0.78rem; font-weight: 700; padding: 4px 9px; border-radius: 6px; cursor: pointer;
}
.toast-btn:hover { background: rgba(255, 255, 255, 0.2); color: #fff; }

/* ── FOOTER ───────────────────────────────────────────────────────────── */
.footer {
    border-top: 1px solid rgba(255, 255, 255, 0.08); padding: 28px 32px;
    text-align: center; font-size: 0.82rem; color: #64748b; background: rgba(8, 12, 20, 0.8);
}
.footer strong { color: #cbd5e1; }
.footer-sources { margin-top: 6px; font-size: 0.75rem; color: #475569; }

/* ── RESPONSIVE ───────────────────────────────────────────────────────── */
@media (max-width: 768px) {
    .header, .nav-tabs-inner, .filters-wrap, .main-container { padding-left: 16px; padding-right: 16px; }
    .jobs-grid { grid-template-columns: 1fr; }
    .header-inner { flex-direction: column; align-items: flex-start; }
    .header-stats { width: 100%; justify-content: space-between; }
    .results-meta { flex-direction: column; align-items: flex-start; }
}
"""
