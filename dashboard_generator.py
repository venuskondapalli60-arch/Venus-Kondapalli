"""
output/dashboard_generator.py - Modern Glassmorphism Dashboard Generator

Generates jobs_dashboard.html with:
  - Dark gradient background with animated floating orbs
  - Glassmorphism job cards with hover glow effects
  - Smooth entrance animations (fade-in + slide-up)
  - Animated score badges and NEW badges
  - Premium Inter typography
  - Fully responsive design
  - Client-side filtering and sorting (pure JavaScript)
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
    """Generates the HTML jobs dashboard."""

    def __init__(self):
        self.generated_at = datetime.now().strftime("%B %d, %Y at %I:%M %p")
        self.today = datetime.now().strftime("%Y-%m-%d")
        self.yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        self.three_days_ago = (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d")

    def generate(self, jobs: List[Dict], stats: Dict, run_id: int = 0) -> str:
        logger.info(f"Generating dashboard with {len(jobs)} jobs...")

        # "Today's Fresh Jobs" = jobs added in the most recent run (is_new=1),
        # not jobs whose posted_date happens to be today (most scraped jobs are
        # posted days ago even when we first discover them).
        today_jobs = [j for j in jobs if j.get("is_new", 0) == 1]
        last3_jobs = [j for j in jobs if j.get("is_new", 0) == 0
                      and self.three_days_ago <= j.get("posted_date", "")]
        last7_jobs = [j for j in jobs if j.get("is_new", 0) == 0
                      and j.get("posted_date", "") < self.three_days_ago]
        top_jobs   = [j for j in jobs if j.get("match_score", 0) >= 90]

        html = self._build_html(
            all_jobs=jobs, today_jobs=today_jobs, last3_jobs=last3_jobs,
            last7_jobs=last7_jobs, top_jobs=top_jobs, stats=stats, run_id=run_id,
        )

        with open(config.DASHBOARD_FILE, "w", encoding="utf-8") as f:
            f.write(html)

        logger.info(f"Dashboard generated: {config.DASHBOARD_FILE}")
        return config.DASHBOARD_FILE

    # ─────────────────────────────────────────────────────────────────────────

    def _build_html(self, all_jobs, today_jobs, last3_jobs, last7_jobs,
                    top_jobs, stats, run_id) -> str:

        jobs_json = json.dumps(all_jobs, ensure_ascii=False, default=str)
        jobs_json = jobs_json.replace("</script>", r"<\/script>")
        jobs_json = jobs_json.replace("</SCRIPT>", r"<\/SCRIPT>")

        companies = sorted(set(j.get("company", "") for j in all_jobs if j.get("company")))
        locations = sorted(set(
            j.get("location", "").split(",")[0].strip()
            for j in all_jobs if j.get("location")
        ))
        sources = sorted(set(j.get("source", "") for j in all_jobs if j.get("source")))

        company_options = "\n".join(f'<option value="{c}">{c}</option>' for c in companies)
        location_options = "\n".join(f'<option value="{l}">{l}</option>' for l in locations)
        source_options = "\n".join(f'<option value="{s}">{s}</option>' for s in sources)

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>UI/UX Job Tracker — Srikar Jupudi</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <style>{self._get_css()}</style>
</head>
<body>

<!-- ── ANIMATED BACKGROUND ORBS ──────────────────────────────────────────── -->
<div class="bg-orbs" aria-hidden="true">
    <div class="orb orb-1"></div>
    <div class="orb orb-2"></div>
    <div class="orb orb-3"></div>
    <div class="orb orb-4"></div>
</div>

<!-- ── HEADER ─────────────────────────────────────────────────────────────── -->
<header class="header">
    <div class="header-inner">
        <div class="brand">
            <div class="brand-icon">🎨</div>
            <div class="brand-text">
                <h1>UI/UX Job Tracker</h1>
                <p>Srikar Jupudi &nbsp;·&nbsp; 4+ Years &nbsp;·&nbsp; Hyderabad</p>
            </div>
        </div>
        <div class="header-meta">
            <div class="pill-stats">
                <div class="pill-stat">
                    <span class="pill-num">{len(all_jobs)}</span>
                    <span class="pill-lbl">Jobs</span>
                </div>
                <div class="pill-divider"></div>
                <div class="pill-stat">
                    <span class="pill-num">{len(today_jobs)}</span>
                    <span class="pill-lbl">Today</span>
                </div>
                <div class="pill-divider"></div>
                <div class="pill-stat">
                    <span class="pill-num">{len(top_jobs)}</span>
                    <span class="pill-lbl">Top</span>
                </div>
            </div>
            <div class="updated-tag">🕐 {self.generated_at}</div>
        </div>
    </div>
</header>

<!-- ── FILTERS ─────────────────────────────────────────────────────────────── -->
<div class="filters-wrap">
    <div class="filters-inner">
        <div class="search-box">
            <svg class="search-ico" viewBox="0 0 20 20" fill="none">
                <circle cx="8.5" cy="8.5" r="5.5" stroke="currentColor" stroke-width="1.8"/>
                <path d="M13 13l3.5 3.5" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/>
            </svg>
            <input type="text" id="searchInput" placeholder="Search jobs, companies, skills…" oninput="applyFilters()">
        </div>
        <div class="selects-row">
            {self._make_dropdown("companyFilter", "🏢 All Companies", [("", "All Companies")] + [(c, c) for c in companies])}
            {self._make_dropdown("locationFilter", "📍 All Locations", [("", "All Locations")] + [(l, l) for l in locations])}
            {self._make_dropdown("sourceFilter", "🔗 All Sources", [("", "All Sources")] + [(s, s) for s in sources])}
            {self._make_dropdown("scoreFilter", "⭐ All Scores", [("0","All Scores"),("90","90%+ Excellent"),("80","80%+ Strong"),("70","70%+ Good")])}
            {self._make_dropdown("dateFilter", "📅 Last 7 Days", [("7","Last 7 Days"),("1","Today Only"),("3","Last 3 Days")])}
            {self._make_dropdown("sortBy", "🏆 Best Match", [("score","Best Match"),("date","Newest First"),("company","Company A–Z")])}
            <button class="btn-reset" onclick="resetFilters()">↺ Reset</button>
        </div>
        <div class="result-count">
            Showing <strong id="visibleCount">{len(all_jobs)}</strong> of {len(all_jobs)} jobs
        </div>
    </div>
</div>

<!-- ── MAIN ────────────────────────────────────────────────────────────────── -->
<main class="main">

    <!-- TOP MATCHES -->
    <section class="section" id="section-top">
        <div class="section-head">
            <div class="section-title">
                <span class="section-icon">🏆</span>
                <h2>Top Matches</h2>
                <span class="score-pill">90%+</span>
            </div>
            <span class="count-badge">{len(top_jobs)}</span>
        </div>
        <div class="jobs-grid" id="grid-top">
            {self._render_job_cards(top_jobs, run_id, highlight=True)}
        </div>
        {self._empty_state(top_jobs, "No 90%+ matches yet — run the scraper to find top jobs.")}
    </section>

    <!-- TODAY -->
    <section class="section" id="section-today">
        <div class="section-head">
            <div class="section-title">
                <span class="section-icon">🔥</span>
                <h2>Today's Fresh Jobs</h2>
            </div>
            <span class="count-badge">{len(today_jobs)}</span>
        </div>
        <div class="jobs-grid" id="grid-today">
            {self._render_job_cards(today_jobs, run_id)}
        </div>
        {self._empty_state(today_jobs, "No new jobs posted today yet.")}
    </section>

    <!-- LAST 3 DAYS -->
    <section class="section" id="section-3days">
        <div class="section-head">
            <div class="section-title">
                <span class="section-icon">📅</span>
                <h2>Last 3 Days</h2>
            </div>
            <span class="count-badge">{len(last3_jobs)}</span>
        </div>
        <div class="jobs-grid" id="grid-3days">
            {self._render_job_cards(last3_jobs, run_id)}
        </div>
        {self._empty_state(last3_jobs, "No jobs from the last 3 days.")}
    </section>

    <!-- LAST 7 DAYS -->
    <section class="section" id="section-7days">
        <div class="section-head">
            <div class="section-title">
                <span class="section-icon">📆</span>
                <h2>Last 7 Days</h2>
            </div>
            <span class="count-badge">{len(last7_jobs)}</span>
        </div>
        <div class="jobs-grid" id="grid-7days">
            {self._render_job_cards(last7_jobs, run_id)}
        </div>
        {self._empty_state(last7_jobs, "No jobs from the last 7 days.")}
    </section>

    <!-- HIDDEN: all jobs for JS filtering -->
    <section class="section" id="section-all" style="display:none;">
        <div class="jobs-grid" id="grid-all">
            {self._render_job_cards(all_jobs, run_id)}
        </div>
    </section>

    <!-- FILTERED RESULTS -->
    <section class="section" id="section-filtered" style="display:none;">
        <div class="section-head">
            <div class="section-title">
                <span class="section-icon">🔎</span>
                <h2>Filtered Results</h2>
            </div>
            <span class="count-badge" id="filteredCount">0</span>
        </div>
        <div class="jobs-grid" id="grid-filtered"></div>
    </section>

</main>

<!-- ── FOOTER ─────────────────────────────────────────────────────────────── -->
<footer class="footer">
    <p>UI/UX Job Tracker &nbsp;·&nbsp; Built for Srikar Jupudi &nbsp;·&nbsp; Auto-refreshes daily</p>
    <p class="footer-sources">LinkedIn · Naukri · Indeed · Foundit · Glassdoor · Wellfound · Instahyre · Company Pages</p>
</footer>

<!-- ── JAVASCRIPT ─────────────────────────────────────────────────────────── -->
<script>
const ALL_JOBS = {jobs_json};

function applyFilters() {{
    const search   = document.getElementById('searchInput').value.toLowerCase();
    const company  = document.getElementById('companyFilter').value.toLowerCase();
    const location = document.getElementById('locationFilter').value.toLowerCase();
    const source   = document.getElementById('sourceFilter').value.toLowerCase();
    const minScore = parseFloat(document.getElementById('scoreFilter').value) || 0;
    const days     = parseInt(document.getElementById('dateFilter').value) || 7;
    const sortBy   = document.getElementById('sortBy').value;

    const cutoff = new Date();
    cutoff.setDate(cutoff.getDate() - days);
    const cutoffStr = cutoff.toISOString().split('T')[0];

    const hasFilters = search || company || location || source || minScore > 0;

    let filtered = ALL_JOBS.filter(j => {{
        const t = (j.title||'').toLowerCase(), c2 = (j.company||'').toLowerCase(),
              d = (j.description||'').toLowerCase(), l = (j.location||'').toLowerCase();
        return (!search  || t.includes(search) || c2.includes(search) || d.includes(search) || l.includes(search))
            && (!company  || c2.includes(company))
            && (!location || l.includes(location))
            && (!source   || (j.source||'').toLowerCase().includes(source))
            && (j.match_score||0) >= minScore
            && (!j.posted_date || j.posted_date >= cutoffStr);
    }});

    filtered.sort((a,b) => {{
        if (sortBy==='score')   return (b.match_score||0)-(a.match_score||0);
        if (sortBy==='date')    return (b.posted_date||'').localeCompare(a.posted_date||'');
        if (sortBy==='company') return (a.company||'').localeCompare(b.company||'');
        return 0;
    }});

    document.getElementById('visibleCount').textContent = filtered.length;
    document.getElementById('filteredCount').textContent = filtered.length;

    if (hasFilters) {{
        ['section-top','section-today','section-3days','section-7days'].forEach(id =>
            document.getElementById(id).style.display = 'none');
        const sec = document.getElementById('section-filtered');
        sec.style.display = 'block';
        document.getElementById('grid-filtered').innerHTML =
            filtered.map(j => renderCard(j)).join('');
        animateCards('#grid-filtered .job-card');
    }} else {{
        document.getElementById('section-filtered').style.display = 'none';
        ['section-top','section-today','section-3days','section-7days'].forEach(id =>
            document.getElementById(id).style.display = 'block');
    }}
}}

// ── Custom Dropdown Logic ─────────────────────────────────────────────────
function toggleDd(fieldId) {{
    const wrap = document.getElementById(fieldId + '-wrap');
    const isOpen = wrap.classList.contains('open');
    // Close all open dropdowns first
    document.querySelectorAll('.cdd.open').forEach(el => el.classList.remove('open'));
    if (!isOpen) wrap.classList.add('open');
}}

function selectDd(fieldId, value, optEl) {{
    // Update hidden input
    document.getElementById(fieldId).value = value;
    // Update label text
    document.getElementById(fieldId + '-lbl').textContent = optEl.textContent;
    // Mark selected option
    const panel = document.getElementById(fieldId + '-panel');
    panel.querySelectorAll('.cdd-opt').forEach(o => o.classList.remove('selected'));
    optEl.classList.add('selected');
    // Close dropdown
    document.getElementById(fieldId + '-wrap').classList.remove('open');
    // Trigger filter
    applyFilters();
}}

// Close dropdowns when clicking outside
document.addEventListener('click', function(e) {{
    if (!e.target.closest('.cdd')) {{
        document.querySelectorAll('.cdd.open').forEach(el => el.classList.remove('open'));
    }}
}});

function resetFilters() {{
    document.getElementById('searchInput').value = '';
    // Reset each custom dropdown to its first option
    [
        ['companyFilter', '🏢 All Companies', ''],
        ['locationFilter', '📍 All Locations', ''],
        ['sourceFilter',  '🔗 All Sources',   ''],
        ['scoreFilter',   '⭐ All Scores',     '0'],
        ['dateFilter',    '📅 Last 7 Days',    '7'],
        ['sortBy',        '🏆 Best Match',     'score'],
    ].forEach(([id, label, val]) => {{
        document.getElementById(id).value = val;
        document.getElementById(id + '-lbl').textContent = label;
        const panel = document.getElementById(id + '-panel');
        if (panel) panel.querySelectorAll('.cdd-opt').forEach(o => o.classList.remove('selected'));
    }});
    applyFilters();
}}

function renderCard(j) {{
    const score = j.match_score || 0;
    let cls = 'orange', lbl = 'Good Match';
    if (score >= 90) {{ cls = 'green'; lbl = 'Excellent'; }}
    else if (score >= 80) {{ cls = 'blue'; lbl = 'Strong Match'; }}
    const isNew = j.is_new === 1;
    const newBadge = isNew ? '<span class="badge-new">NEW</span>' : '';
    const applyUrl = j.apply_url || j.url || '#';
    const bd = j.score_breakdown || '';
    return `
    <div class="job-card score-${{cls}} ${{isNew?'is-new':''}}">
        <div class="card-top">
            <div class="card-title-wrap">${{newBadge}}<h3 class="card-title">${{esc(j.title||'')}}</h3></div>
            <div class="score-ring score-${{cls}}">
                <span class="ring-num">${{score}}%</span>
                <span class="ring-lbl">${{lbl}}</span>
            </div>
        </div>
        <div class="card-meta">
            <span class="tag tag-company">🏢 ${{esc(j.company||'')}}</span>
            <span class="tag tag-loc">📍 ${{esc((j.location||'India').split(',')[0])}}</span>
            <span class="tag tag-date">📅 ${{esc(j.posted_date||'Recently')}}</span>
            <span class="tag tag-src">🔗 ${{esc(j.source||'')}}</span>
        </div>
        ${{bd ? `<div class="card-breakdown">${{esc(bd)}}</div>` : ''}}
        <div class="card-actions">
            <a href="${{applyUrl}}" target="_blank" rel="noopener" class="btn-apply">Apply Now →</a>
            <a href="${{j.url||'#'}}" target="_blank" rel="noopener" class="btn-view">View</a>
        </div>
    </div>`;
}}

function esc(s) {{
    return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}}

function animateCards(sel) {{
    document.querySelectorAll(sel).forEach((el,i) => {{
        el.style.opacity = '0';
        el.style.transform = 'translateY(24px)';
        setTimeout(() => {{
            el.style.transition = 'opacity 0.45s ease, transform 0.45s ease';
            el.style.opacity = '1';
            el.style.transform = 'translateY(0)';
        }}, i * 60);
    }});
}}

document.addEventListener('DOMContentLoaded', () => {{
    animateCards('.job-card');
    document.getElementById('visibleCount').textContent = ALL_JOBS.length;
}});
</script>
</body>
</html>"""

    # ─────────────────────────────────────────────────────────────────────────

    def _render_job_cards(self, jobs: List[Dict], run_id: int,
                           highlight: bool = False) -> str:
        if not jobs:
            return ""
        return "\n".join(self._render_single_card(j, run_id, highlight) for j in jobs)

    def _render_single_card(self, job: Dict, run_id: int,
                             highlight: bool = False) -> str:
        score  = job.get("match_score", 0)
        is_new = job.get("is_new", 0) == 1 or job.get("run_id") == run_id

        if score >= 90:
            score_cls, score_lbl = "green", "Excellent"
        elif score >= 80:
            score_cls, score_lbl = "blue", "Strong Match"
        else:
            score_cls, score_lbl = "orange", "Good Match"

        new_badge     = '<span class="badge-new">NEW</span>' if is_new else ""
        highlight_cls = "highlight" if highlight else ""
        new_cls       = "is-new" if is_new else ""

        title       = self._esc(job.get("title", ""))
        company     = self._esc(job.get("company", ""))
        location    = self._esc(job.get("location", "India").split(",")[0].strip())
        source      = self._esc(job.get("source", ""))
        apply_url   = job.get("apply_url") or job.get("url", "#")
        view_url    = job.get("url", "#")
        breakdown   = self._esc(job.get("score_breakdown", ""))
        posted_lbl  = self._format_date_label(job.get("posted_date", ""))

        return f"""
        <div class="job-card score-{score_cls} {highlight_cls} {new_cls}">
            <div class="card-top">
                <div class="card-title-wrap">
                    {new_badge}
                    <h3 class="card-title">{title}</h3>
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
                <span class="tag tag-src">🔗 {source}</span>
            </div>
            {f'<div class="card-breakdown">{breakdown}</div>' if breakdown else ''}
            <div class="card-actions">
                <a href="{apply_url}" target="_blank" rel="noopener noreferrer"
                   class="btn-apply">Apply Now →</a>
                <a href="{view_url}" target="_blank" rel="noopener noreferrer"
                   class="btn-view">View</a>
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
            dt   = datetime.strptime(date_str, "%Y-%m-%d")
            diff = (datetime.now().date() - dt.date()).days
            if diff == 0:   return "Today"
            if diff == 1:   return "Yesterday"
            if diff <= 7:   return f"{diff}d ago"
            return dt.strftime("%b %d")
        except ValueError:
            return date_str

    def _make_dropdown(self, field_id: str, placeholder: str,
                       options: list) -> str:
        """Render a fully custom dark-themed dropdown (replaces native <select>)."""
        items_html = ""
        for val, label in options:
            items_html += (
                f'<div class="cdd-opt" data-val="{self._esc(str(val))}" '
                f'onclick="selectDd(\'{field_id}\',\'{self._esc(str(val))}\','
                f'this)">{self._esc(label)}</div>\n'
            )
        return f"""
<div class="cdd" id="{field_id}-wrap">
    <button type="button" class="cdd-btn" onclick="toggleDd('{field_id}')">
        <span class="cdd-lbl" id="{field_id}-lbl">{placeholder}</span>
        <svg class="cdd-arrow" viewBox="0 0 10 6" fill="none">
            <path d="M1 1l4 4 4-4" stroke="currentColor" stroke-width="1.5"
                  stroke-linecap="round" stroke-linejoin="round"/>
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

    # ─────────────────────────────────────────────────────────────────────────
    # CSS
    # ─────────────────────────────────────────────────────────────────────────

    def _get_css(self) -> str:
        return """
/* ── Reset ──────────────────────────────────────────────────────────────── */
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

/* ── Tokens ─────────────────────────────────────────────────────────────── */
:root {
    --bg:        #0d0d1a;
    --bg2:       #12122a;
    --surface:   rgba(255,255,255,0.055);
    --surface-h: rgba(255,255,255,0.09);
    --border:    rgba(255,255,255,0.10);
    --border-h:  rgba(255,255,255,0.22);
    --text:      #e8e8f0;
    --text-2:    #9898b8;
    --text-3:    #5a5a7a;

    --green:  #22d3a0;  --green-dim:  rgba(34,211,160,.15);  --green-glow: rgba(34,211,160,.35);
    --blue:   #60a5fa;  --blue-dim:   rgba(96,165,250,.15);  --blue-glow:  rgba(96,165,250,.35);
    --orange: #fb923c;  --orange-dim: rgba(251,146,60,.15);  --orange-glow:rgba(251,146,60,.35);
    --purple: #a78bfa;  --pink: #f472b6;

    --grad-brand: linear-gradient(135deg, #7c3aed 0%, #a855f7 50%, #ec4899 100%);
    --grad-card-green:  linear-gradient(135deg, rgba(34,211,160,.08) 0%, transparent 60%);
    --grad-card-blue:   linear-gradient(135deg, rgba(96,165,250,.08) 0%, transparent 60%);
    --grad-card-orange: linear-gradient(135deg, rgba(251,146,60,.08) 0%, transparent 60%);

    --radius-sm: 10px; --radius: 16px; --radius-lg: 22px; --radius-xl: 28px;
    --shadow-card: 0 8px 32px rgba(0,0,0,.45);
    --shadow-hover: 0 20px 60px rgba(0,0,0,.6);
    --blur: blur(18px);
}

/* ── Base ────────────────────────────────────────────────────────────────── */
html { scroll-behavior: smooth; }
body {
    font-family: 'Inter', -apple-system, sans-serif;
    background: var(--bg);
    color: var(--text);
    min-height: 100vh;
    overflow-x: hidden;
    line-height: 1.6;
}

/* ── Animated Background Orbs ───────────────────────────────────────────── */
.bg-orbs { position: fixed; inset: 0; pointer-events: none; z-index: 0; overflow: hidden; }
.orb {
    position: absolute; border-radius: 50%;
    filter: blur(80px); opacity: 0.18;
    animation: drift 18s ease-in-out infinite alternate;
}
.orb-1 { width: 600px; height: 600px; background: #7c3aed; top: -200px; left: -150px; animation-duration: 20s; }
.orb-2 { width: 500px; height: 500px; background: #ec4899; top: 30%; right: -180px; animation-duration: 25s; animation-delay: -8s; }
.orb-3 { width: 400px; height: 400px; background: #06b6d4; bottom: -100px; left: 30%; animation-duration: 22s; animation-delay: -4s; }
.orb-4 { width: 350px; height: 350px; background: #10b981; bottom: 20%; right: 20%; animation-duration: 28s; animation-delay: -12s; }
@keyframes drift {
    0%   { transform: translate(0,0) scale(1); }
    33%  { transform: translate(40px,-30px) scale(1.05); }
    66%  { transform: translate(-20px,50px) scale(0.97); }
    100% { transform: translate(30px,20px) scale(1.03); }
}

/* ── Header ─────────────────────────────────────────────────────────────── */
.header {
    position: sticky; top: 0; z-index: 100;
    background: rgba(13,13,26,0.75);
    backdrop-filter: var(--blur);
    -webkit-backdrop-filter: var(--blur);
    border-bottom: 1px solid var(--border);
    padding: 18px 0;
}
.header-inner {
    max-width: 1400px; margin: 0 auto; padding: 0 28px;
    display: flex; align-items: center; justify-content: space-between;
    flex-wrap: wrap; gap: 16px;
}
.brand { display: flex; align-items: center; gap: 14px; }
.brand-icon {
    font-size: 2rem; width: 52px; height: 52px;
    background: var(--grad-brand);
    border-radius: var(--radius);
    display: flex; align-items: center; justify-content: center;
    box-shadow: 0 0 24px rgba(168,85,247,.4);
    flex-shrink: 0;
}
.brand-text h1 {
    font-size: 1.35rem; font-weight: 800; letter-spacing: -0.5px;
    background: var(--grad-brand); -webkit-background-clip: text;
    -webkit-text-fill-color: transparent; background-clip: text;
}
.brand-text p { font-size: 0.78rem; color: var(--text-2); margin-top: 2px; }

.header-meta { display: flex; flex-direction: column; align-items: flex-end; gap: 8px; }
.pill-stats {
    display: flex; align-items: center; gap: 0;
    background: var(--surface); border: 1px solid var(--border);
    border-radius: 50px; padding: 6px 18px;
    backdrop-filter: var(--blur);
}
.pill-stat { text-align: center; padding: 0 12px; }
.pill-num { display: block; font-size: 1.3rem; font-weight: 800; color: var(--text); line-height: 1; }
.pill-lbl { font-size: 0.65rem; color: var(--text-2); text-transform: uppercase; letter-spacing: 0.8px; }
.pill-divider { width: 1px; height: 32px; background: var(--border); }
.updated-tag { font-size: 0.72rem; color: var(--text-3); }

/* ── Filters ─────────────────────────────────────────────────────────────── */
.filters-wrap {
    position: sticky; top: 89px; z-index: 90;
    background: rgba(13,13,26,0.7);
    backdrop-filter: var(--blur);
    -webkit-backdrop-filter: var(--blur);
    border-bottom: 1px solid var(--border);
    padding: 14px 0;
}
.filters-inner {
    max-width: 1400px; margin: 0 auto; padding: 0 28px;
    display: flex; flex-direction: column; gap: 10px;
}
.search-box {
    position: relative; width: 100%;
}
.search-ico {
    position: absolute; left: 14px; top: 50%; transform: translateY(-50%);
    width: 16px; height: 16px; color: var(--text-3);
}
.search-box input {
    width: 100%; padding: 11px 16px 11px 42px;
    background: var(--surface); border: 1px solid var(--border);
    border-radius: var(--radius); color: var(--text);
    font-size: 0.9rem; font-family: inherit; outline: none;
    transition: border-color 0.2s, box-shadow 0.2s;
}
.search-box input::placeholder { color: var(--text-3); }
.search-box input:focus {
    border-color: var(--purple);
    box-shadow: 0 0 0 3px rgba(167,139,250,.15);
}
.selects-row {
    display: flex; flex-wrap: wrap; gap: 8px; align-items: center;
}
.selects-row select, .btn-reset {
    padding: 9px 14px;
    background: var(--surface); border: 1px solid var(--border);
    border-radius: var(--radius-sm); color: var(--text);
    font-size: 0.8rem; font-family: inherit; cursor: pointer; outline: none;
    transition: border-color 0.2s, background 0.2s;
    appearance: none; -webkit-appearance: none;
}
.selects-row select:focus, .btn-reset:hover {
    border-color: var(--purple); background: var(--surface-h);
}
.btn-reset { color: var(--text-2); letter-spacing: 0.3px; }
.result-count { font-size: 0.78rem; color: var(--text-3); }
.result-count strong { color: var(--purple); }

/* ── Main ────────────────────────────────────────────────────────────────── */
.main {
    max-width: 1400px; margin: 0 auto; padding: 36px 28px 60px;
    position: relative; z-index: 1;
}

/* ── Section ─────────────────────────────────────────────────────────────── */
.section { margin-bottom: 52px; }
.section-head {
    display: flex; align-items: center; justify-content: space-between;
    margin-bottom: 24px;
}
.section-title {
    display: flex; align-items: center; gap: 10px;
}
.section-icon { font-size: 1.3rem; }
.section-title h2 {
    font-size: 1.2rem; font-weight: 700; color: var(--text);
    letter-spacing: -0.3px;
}
.score-pill {
    background: linear-gradient(135deg, rgba(34,211,160,.2), rgba(34,211,160,.05));
    border: 1px solid rgba(34,211,160,.3);
    color: var(--green); font-size: 0.72rem; font-weight: 700;
    padding: 3px 10px; border-radius: 20px; letter-spacing: 0.5px;
}
.count-badge {
    background: var(--surface); border: 1px solid var(--border);
    color: var(--text-2); font-size: 0.78rem; font-weight: 600;
    padding: 4px 14px; border-radius: 20px;
}

/* ── Jobs Grid ───────────────────────────────────────────────────────────── */
.jobs-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
    gap: 20px;
}

/* ── Job Card ────────────────────────────────────────────────────────────── */
.job-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius-lg);
    padding: 22px;
    box-shadow: var(--shadow-card);
    backdrop-filter: var(--blur);
    -webkit-backdrop-filter: var(--blur);
    transition: transform 0.3s cubic-bezier(.34,1.56,.64,1),
                box-shadow 0.3s ease,
                border-color 0.3s ease;
    position: relative; overflow: hidden;
    /* entrance animation applied via JS */
}
.job-card::before {
    content: ''; position: absolute; inset: 0; border-radius: inherit;
    opacity: 0; transition: opacity 0.3s;
    pointer-events: none;
}
.job-card.score-green  { background: var(--grad-card-green);  border-left: 3px solid var(--green); }
.job-card.score-blue   { background: var(--grad-card-blue);   border-left: 3px solid var(--blue); }
.job-card.score-orange { background: var(--grad-card-orange); border-left: 3px solid var(--orange); }

.job-card.score-green::before  { background: radial-gradient(ellipse at top left, var(--green-glow), transparent 70%); }
.job-card.score-blue::before   { background: radial-gradient(ellipse at top left, var(--blue-glow),  transparent 70%); }
.job-card.score-orange::before { background: radial-gradient(ellipse at top left, var(--orange-glow),transparent 70%); }

.job-card:hover {
    transform: translateY(-6px) scale(1.01);
    box-shadow: var(--shadow-hover);
    border-color: var(--border-h);
}
.job-card.score-green:hover  { box-shadow: var(--shadow-hover), 0 0 40px var(--green-glow); }
.job-card.score-blue:hover   { box-shadow: var(--shadow-hover), 0 0 40px var(--blue-glow); }
.job-card.score-orange:hover { box-shadow: var(--shadow-hover), 0 0 40px var(--orange-glow); }
.job-card:hover::before { opacity: 1; }

.job-card.highlight {
    background: linear-gradient(135deg, rgba(34,211,160,.1), rgba(96,165,250,.06), transparent);
}
.job-card.is-new { animation: card-pulse 2.5s ease-in-out 2; }
@keyframes card-pulse {
    0%,100% { box-shadow: var(--shadow-card); }
    50%      { box-shadow: var(--shadow-card), 0 0 30px rgba(34,211,160,.4); }
}

/* Card internals */
.card-top {
    display: flex; justify-content: space-between; align-items: flex-start;
    gap: 14px; margin-bottom: 14px;
}
.card-title-wrap { flex: 1; }
.card-title {
    font-size: 0.97rem; font-weight: 600; color: var(--text);
    line-height: 1.45; margin-top: 4px;
}

/* Score ring */
.score-ring {
    display: flex; flex-direction: column; align-items: center;
    padding: 10px 14px; border-radius: var(--radius);
    min-width: 76px; text-align: center; flex-shrink: 0;
    border: 1px solid transparent;
}
.score-ring.score-green  { background: var(--green-dim);  border-color: rgba(34,211,160,.25); }
.score-ring.score-blue   { background: var(--blue-dim);   border-color: rgba(96,165,250,.25); }
.score-ring.score-orange { background: var(--orange-dim); border-color: rgba(251,146,60,.25); }
.ring-num {
    font-size: 1.25rem; font-weight: 800; line-height: 1;
}
.score-ring.score-green  .ring-num { color: var(--green); }
.score-ring.score-blue   .ring-num { color: var(--blue); }
.score-ring.score-orange .ring-num { color: var(--orange); }
.ring-lbl {
    font-size: 0.6rem; font-weight: 600; text-transform: uppercase;
    letter-spacing: 0.4px; margin-top: 3px; color: var(--text-2);
}

/* NEW badge */
.badge-new {
    display: inline-block;
    background: linear-gradient(135deg, #22d3a0, #06b6d4);
    color: #000; font-size: 0.6rem; font-weight: 800;
    padding: 2px 9px; border-radius: 20px; letter-spacing: 0.8px;
    text-transform: uppercase; margin-bottom: 5px;
    animation: glow-new 1.8s ease-in-out infinite alternate;
}
@keyframes glow-new {
    from { box-shadow: 0 0 6px rgba(34,211,160,.5); }
    to   { box-shadow: 0 0 16px rgba(34,211,160,.9), 0 0 30px rgba(34,211,160,.3); }
}

/* Tags */
.card-meta { display: flex; flex-wrap: wrap; gap: 7px; margin-bottom: 14px; }
.tag {
    font-size: 0.74rem; padding: 4px 11px; border-radius: 20px;
    border: 1px solid var(--border); color: var(--text-2);
    background: rgba(255,255,255,.04);
    transition: background 0.2s, border-color 0.2s;
}
.job-card:hover .tag { background: rgba(255,255,255,.07); }
.tag-src { border-color: rgba(167,139,250,.3); color: var(--purple); background: rgba(167,139,250,.08); }

/* Score breakdown */
.card-breakdown {
    font-size: 0.68rem; color: var(--text-3); margin-bottom: 14px;
    font-family: 'SF Mono', 'Fira Code', monospace;
    background: rgba(255,255,255,.03); border: 1px solid var(--border);
    padding: 7px 12px; border-radius: var(--radius-sm);
    letter-spacing: 0.3px;
}

/* Action buttons */
.card-actions { display: flex; gap: 10px; margin-top: 16px; }
.btn-apply {
    flex: 1; padding: 11px 18px; text-align: center;
    background: var(--grad-brand);
    color: white; text-decoration: none; border-radius: var(--radius-sm);
    font-size: 0.84rem; font-weight: 700; letter-spacing: 0.2px;
    transition: opacity 0.2s, transform 0.2s, box-shadow 0.2s;
    box-shadow: 0 4px 20px rgba(168,85,247,.3);
}
.btn-apply:hover {
    opacity: 0.9; transform: translateY(-1px);
    box-shadow: 0 8px 30px rgba(168,85,247,.5);
}
.btn-view {
    padding: 11px 18px; text-align: center;
    background: var(--surface); border: 1px solid var(--border);
    color: var(--text-2); text-decoration: none; border-radius: var(--radius-sm);
    font-size: 0.84rem; font-weight: 500;
    transition: background 0.2s, border-color 0.2s, color 0.2s;
}
.btn-view:hover { background: var(--surface-h); border-color: var(--border-h); color: var(--text); }

/* ── Empty State ─────────────────────────────────────────────────────────── */
.empty-state {
    text-align: center; padding: 56px 24px;
    background: var(--surface); border: 1px dashed var(--border);
    border-radius: var(--radius-lg);
}
.empty-icon { font-size: 2.8rem; margin-bottom: 14px; opacity: 0.5; }
.empty-state p { font-size: 0.9rem; color: var(--text-3); }

/* ── Footer ──────────────────────────────────────────────────────────────── */
.footer {
    text-align: center; padding: 28px;
    border-top: 1px solid var(--border);
    color: var(--text-3); font-size: 0.78rem; line-height: 2;
    position: relative; z-index: 1;
}
.footer-sources { font-size: 0.72rem; opacity: 0.6; margin-top: 4px; }

/* ── Custom Dropdown ─────────────────────────────────────────────────────── */
.cdd {
    position: relative; display: inline-block;
}
.cdd-btn {
    display: flex; align-items: center; gap: 8px;
    padding: 9px 14px;
    background: rgba(255,255,255,0.07);
    border: 1px solid rgba(255,255,255,0.15);
    border-radius: var(--radius-sm);
    color: var(--text); font-size: 0.82rem; font-family: inherit;
    cursor: pointer; outline: none; white-space: nowrap;
    transition: border-color 0.2s, background 0.2s, box-shadow 0.2s;
    min-width: 130px;
}
.cdd-btn:hover {
    border-color: var(--purple);
    background: rgba(167,139,250,0.12);
    box-shadow: 0 0 0 3px rgba(167,139,250,0.1);
}
.cdd.open .cdd-btn {
    border-color: var(--purple);
    background: rgba(167,139,250,0.15);
    box-shadow: 0 0 0 3px rgba(167,139,250,0.15);
}
.cdd-lbl { flex: 1; text-align: left; font-weight: 500; }
.cdd-arrow {
    width: 10px; height: 6px; flex-shrink: 0; color: var(--text-2);
    transition: transform 0.25s ease;
}
.cdd.open .cdd-arrow { transform: rotate(180deg); }

.cdd-panel {
    display: none;
    position: absolute; top: calc(100% + 6px); left: 0;
    min-width: 100%; max-width: 260px;
    background: #1a1a30;
    border: 1px solid rgba(167,139,250,0.3);
    border-radius: var(--radius);
    box-shadow: 0 16px 48px rgba(0,0,0,0.7), 0 0 0 1px rgba(167,139,250,0.1);
    backdrop-filter: blur(24px);
    -webkit-backdrop-filter: blur(24px);
    z-index: 200;
    overflow: hidden;
    max-height: 280px; overflow-y: auto;
    animation: dd-in 0.18s ease;
}
.cdd.open .cdd-panel { display: block; }

@keyframes dd-in {
    from { opacity: 0; transform: translateY(-8px) scale(0.97); }
    to   { opacity: 1; transform: translateY(0) scale(1); }
}

.cdd-opt {
    padding: 10px 16px;
    font-size: 0.82rem; color: var(--text-2);
    cursor: pointer; white-space: nowrap; overflow: hidden;
    text-overflow: ellipsis;
    transition: background 0.15s, color 0.15s;
    border-bottom: 1px solid rgba(255,255,255,0.04);
}
.cdd-opt:last-child { border-bottom: none; }
.cdd-opt:hover {
    background: rgba(167,139,250,0.15);
    color: var(--text);
}
.cdd-opt.selected {
    background: rgba(167,139,250,0.2);
    color: var(--purple);
    font-weight: 600;
}

/* Scrollbar for dropdown panel */
.cdd-panel::-webkit-scrollbar { width: 4px; }
.cdd-panel::-webkit-scrollbar-track { background: transparent; }
.cdd-panel::-webkit-scrollbar-thumb { background: rgba(167,139,250,0.3); border-radius: 4px; }

/* ── Responsive ──────────────────────────────────────────────────────────── */
@media (max-width: 768px) {
    .header-inner { flex-direction: column; align-items: flex-start; }
    .header-meta  { align-items: flex-start; }
    .jobs-grid    { grid-template-columns: 1fr; }
    .selects-row  { flex-direction: column; }
    .cdd, .cdd-btn { width: 100%; }
    .btn-reset { width: 100%; }
    .main { padding: 24px 16px 48px; }
}
"""
