"""
config.py - Central configuration for the UI/UX Job Search Automation System
All tunable parameters, paths, and constants are defined here.
"""

import os
from datetime import datetime

# ─────────────────────────────────────────────
# BASE PATHS
# ─────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "jobs.db")
LOGS_DIR = os.path.join(BASE_DIR, "logs")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
DASHBOARD_FILE = os.path.join(BASE_DIR, "jobs_dashboard.html")
LOG_FILE = os.path.join(LOGS_DIR, f"daily_run_{datetime.now().strftime('%Y%m%d')}.log")

# ─────────────────────────────────────────────
# SEARCH CONFIGURATION
# ─────────────────────────────────────────────
SEARCH_LOCATIONS = [
    "Germany",
    "Berlin",
    "Munich",
    "Frankfurt",
    "Hamburg",
    "Remote",
    "Europe",
    "Hyderabad",
    "Bangalore",
    "India",
]
MAX_DAYS_OLD = 7
MIN_MATCH_SCORE = 60
MAX_WORKERS = 8
REQUEST_TIMEOUT = 10
MAX_RETRIES = 1
RETRY_DELAY = 1
RATE_LIMIT_DELAY = 1.0

# ─────────────────────────────────────────────
# TARGET JOB ROLES
# ─────────────────────────────────────────────
TARGET_ROLES = [
    "Product Manager",
    "Lead Product Manager",
    "Product Designer",
    "Lead Product Designer",
    "Senior Product Designer",
    "Staff Product Designer",
    "UI/UX Designer",
    "Senior UI/UX Designer",
    "UI/UX Design Expert",
    "UI/UX Lead",
    "UX Designer",
    "UI Designer",
    "Staff UX Designer",
    "UX Researcher",
    "Lead UX Researcher",
    "UX Design Consultant",
    "Enterprise UX Designer",
    "ServiceNow UX Designer",
    "ServiceNow UX Consultant",
    "Design Lead",
    "Interaction Designer",
    "Design System Designer",
    "Digital Product Designer",
    "Visual Designer",
    "Experience Designer",
]

SEARCH_KEYWORDS = [
    "Product Manager",
    "Product Designer",
    "UI UX Designer",
    "Senior Product Designer",
    "Senior UX Designer",
    "Lead Product Designer",
    "Staff UX Designer",
    "UX Researcher",
    "Design Lead",
    "ServiceNow UX",
]

# Skill-based search queries derived from resume profile
SKILL_SEARCH_KEYWORDS = [
    "Figma Product Designer",
    "Design Systems Lead",
    "Enterprise UX Designer",
    "AI Product Manager",
    "UX Research Lead",
    "Accessibility UX Designer",
    "B2B SaaS Product Designer",
    "ServiceNow Designer",
    "Mobile UX Designer",
    "Frontend UX Designer",
]

# Combined list used by all scrapers (role-based + skill-based)
ALL_SEARCH_KEYWORDS = SEARCH_KEYWORDS + SKILL_SEARCH_KEYWORDS

# ─────────────────────────────────────────────
# HTTP HEADERS
# ─────────────────────────────────────────────
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
]

DEFAULT_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9,de;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Cache-Control": "max-age=0",
}

# ─────────────────────────────────────────────
# SOURCE PRIORITY (lower = higher priority)
# ─────────────────────────────────────────────
SOURCE_PRIORITY = {
    "Bundesagentur für Arbeit": 1,
    "Company Career Pages": 2,
    "LinkedIn": 3,
    "German Job Portals": 4,
    "Indeed": 5,
    "Glassdoor": 6,
    "Wellfound": 7,
    "Naukri": 8,
    "Foundit": 9,
    "Instahyre": 10,
}

# ─────────────────────────────────────────────
# SCRAPER ENDPOINTS
# ─────────────────────────────────────────────
SCRAPER_URLS = {
    "arbeitsagentur": "https://www.arbeitsagentur.de/jobsuche/suche",
    "connecticum": "https://www.connecticum.de/jobsuche",
    "jobrapido_de": "https://de.jobrapido.com/",
    "studentjob_de": "https://www.studentjob.de/stellenangebote",
    "politjobs_de": "https://politjobs.de/",
    "rheinpfalz_de": "https://jobs.rheinpfalz.de/jobs/suche",
    "pagepersonnel_de": "https://www.pagepersonnel.de/browse/jobs",
    "naukri_api": "https://www.naukri.com/jobapi/v3/search",
    "naukri_base": "https://www.naukri.com",
    "indeed_base": "https://in.indeed.com/jobs",
    "indeed_de": "https://de.indeed.com/jobs",
    "linkedin_guest": "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search",
    "linkedin_search": "https://www.linkedin.com/jobs/search/",
    "foundit_base": "https://www.foundit.in/srp/results",
    "glassdoor_base": "https://www.glassdoor.co.in/Job/jobs.htm",
    "glassdoor_de": "https://www.glassdoor.de/Job/jobs.htm",
    "wellfound_base": "https://wellfound.com/jobs",
    "instahyre_api": "https://www.instahyre.com/api/v1/search_jobs/",
}

# ─────────────────────────────────────────────
# GERMAN JOB SITES & PORTALS (User's Target Directory)
# ─────────────────────────────────────────────
GERMAN_JOB_PORTALS = [
    {"name": "Jobbörse der Bundesagentur für Arbeit", "url": "https://www.arbeitsagentur.de/jobsuche/suche?angebotsart=1&was=Product%20Manager&wo=Deutschland", "category": "Federal & Public"},
    {"name": "StepStone", "url": "https://www.stepstone.de/jobs/product-manager/in-deutschland", "category": "General & Tech"},
    {"name": "Jobbörse.de", "url": "https://www.jobboerse.de/jobs/suche?q=Product+Manager", "category": "General & Tech"},
    {"name": "Indeed Deutschland", "url": "https://de.indeed.com/jobs?q=Product+Manager&l=Deutschland", "category": "General & Tech"},
    {"name": "Connecticum", "url": "https://www.connecticum.de/jobsuche?q=Product+Manager", "category": "Tech & Careers"},
    {"name": "Kimeta.de", "url": "https://www.kimeta.de/stellenangebote-product-manager", "category": "Meta-Search"},
    {"name": "JobRobot", "url": "https://www.jobrobot.de/", "category": "Meta-Search"},
    {"name": "Adzuna Deutschland", "url": "https://www.adzuna.de/search?q=Product+Manager", "category": "Meta-Search"},
    {"name": "Monster Deutschland", "url": "https://www.monster.de/jobs/suche/?q=Product+Manager&where=Deutschland", "category": "General & Tech"},
    {"name": "Jooble Deutschland", "url": "https://de.jooble.org/SearchResult?ukw=Product%20Manager&rgn=Deutschland", "category": "Meta-Search"},
    {"name": "REKRUTER", "url": "https://www.rekruter.de/", "category": "Specialist"},
    {"name": "Experteer", "url": "https://www.experteer.de/jobs/search?q=Product+Manager", "category": "Senior & Executive"},
    {"name": "Stellenticket", "url": "https://www.stellenticket.de/", "category": "University & Tech"},
    {"name": "Yourfirm", "url": "https://www.yourfirm.de/suche/Product%20Manager/Deutschland/", "category": "Mittelstand & SME"},
    {"name": "WeserKurier Jobs", "url": "https://stellenmarkt.weser-kurier.de/", "category": "Regional Newspaper"},
    {"name": "Augsburger Allgemeine Stellenmarkt", "url": "https://stellenmarkt.augsburger-allgemeine.de/", "category": "Regional Newspaper"},
    {"name": "Jobvector", "url": "https://www.jobvector.de/stellenangebote/", "category": "Science & Tech"},
    {"name": "Bauingenieur24", "url": "https://www.bauingenieur24.de/stellenmarkt", "category": "Engineering"},
    {"name": "Politjobs.de", "url": "https://politjobs.de/?s=Product", "category": "Public & Digital Policy"},
    {"name": "Jobkurier.de", "url": "https://www.jobkurier.de/", "category": "General"},
    {"name": "TN Deutschland", "url": "https://www.tn-deutschland.com/", "category": "Specialist"},
    {"name": "Job.ne.de", "url": "https://www.job.ne.de/", "category": "Regional"},
    {"name": "Jobs.merkur.de", "url": "https://jobs.merkur.de/jobs/suche?q=Product+Manager", "category": "Regional Newspaper (Bavaria)"},
    {"name": "Studentjob.de", "url": "https://www.studentjob.de/stellenangebote?query=Product+Manager", "category": "Young Professionals & Tech"},
    {"name": "Jobs.heise.de", "url": "https://jobs.heise.de/stellenangebote/product-manager/", "category": "IT & Tech Industry"},
    {"name": "Jobs.rheinpfalz.de", "url": "https://jobs.rheinpfalz.de/jobs/suche?q=Product+Manager", "category": "Regional Newspaper"},
    {"name": "TWjobs (TextilWirtschaft)", "url": "https://www.twjobs.de/", "category": "Industry Specialist"},
    {"name": "LZjobs (Lebensmittel Zeitung)", "url": "https://www.lzjobs.de/", "category": "Industry Specialist"},
    {"name": "IZ-Jobs (Immobilien Zeitung)", "url": "https://www.iz-jobs.de/", "category": "Industry Specialist"},
    {"name": "Industriejobs.de", "url": "https://www.industriejobs.de/", "category": "Industry Specialist"},
    {"name": "Mittelbayerische Stellen", "url": "https://www.mittelbayerische-stellen.de/jobs/suche?q=Product+Manager", "category": "Regional Newspaper"},
    {"name": "BZ-Jobs Berlin", "url": "https://www.bz-jobs.de/", "category": "Regional Newspaper (Berlin)"},
    {"name": "Jobs.pz-News.de", "url": "https://jobs.pz-news.de/", "category": "Regional Newspaper"},
    {"name": "Jobs.rnz.de", "url": "https://jobs.rnz.de/", "category": "Regional Newspaper"},
    {"name": "Page Personnel Deutschland", "url": "https://www.pagepersonnel.de/browse/jobs/product-manager", "category": "Recruitment & Staffing"},
    {"name": "Jobleads", "url": "https://www.jobleads.com/de-de/jobs/search?q=Product+Manager", "category": "Executive"},
    {"name": "Jobrapido Deutschland", "url": "https://de.jobrapido.com/?w=Product+Manager&l=Deutschland", "category": "Meta-Search"},
    {"name": "Absolventa", "url": "https://www.absolventa.de/jobs/suche?search%5Bquery%5D=Product+Manager", "category": "Young Professionals"},
    {"name": "AUBI-Plus", "url": "https://www.aubi-plus.de/stellenmarkt/", "category": "Education & Careers"},
    {"name": "Jobinnovator", "url": "https://www.jobinnovator.de/", "category": "Specialist"},
    {"name": "Jobetage", "url": "https://www.jobetage.de/", "category": "Regional"},
    {"name": "Stellenanzeigen.de", "url": "https://www.stellenanzeigen.de/stellenangebote/product-manager/", "category": "General & Tech"},
    {"name": "MetaJob.de", "url": "https://www.metajob.de/jobs?was=Product+Manager&wo=Deutschland", "category": "Meta-Search Engine"},
    {"name": "Uni-Potsdam Stellenportal", "url": "https://uni-potsdam.stellenticket.de/", "category": "University & Research"},
    {"name": "Alleskralle.com", "url": "https://www.alleskralle.com/jobs", "category": "Meta-Search"},
    {"name": "Stark am Markt", "url": "https://www.stark-am-markt.de/", "category": "Company Directory"},
    {"name": "Firmen in Thüringen", "url": "https://www.firmen-in-thueringen.de/", "category": "Company Directory"},
]

# ─────────────────────────────────────────────
# COMPANY CAREER PAGES
# ─────────────────────────────────────────────
COMPANY_CAREER_PAGES = [
    # Germany / European tech hubs
    {"company": "Zalando",       "url": "https://jobs.zalando.com/en/jobs"},
    {"company": "Delivery Hero",  "url": "https://careers.deliveryhero.com/global/en"},
    {"company": "SAP",            "url": "https://jobs.sap.com/"},
    {"company": "N26",            "url": "https://n26.com/en-de/careers"},
    {"company": "Personio",       "url": "https://www.personio.com/careers/"},
    {"company": "HelloFresh",     "url": "https://careers.hellofresh.com/global/en"},
    {"company": "Siemens",        "url": "https://jobs.siemens.com/"},
    # Enterprise & Global Ecosystem
    {"company": "ServiceNow",    "url": "https://careers.servicenow.com/"},
    {"company": "Salesforce",    "url": "https://careers.salesforce.com/"},
    {"company": "NTT DATA",      "url": "https://careers.services.global.ntt/"},
    # India Tech Hubs
    {"company": "Flipkart",      "url": "https://www.flipkartcareers.com/#!/joblist"},
    {"company": "Swiggy",        "url": "https://careers.swiggy.com/#careers"},
    {"company": "Freshworks",    "url": "https://www.freshworks.com/company/careers/"},
    {"company": "Razorpay",      "url": "https://razorpay.com/jobs/"},
]

# ─────────────────────────────────────────────
# VALIDATION SETTINGS
# ─────────────────────────────────────────────
VALID_HTTP_CODES = [200, 201]
INVALID_HTTP_CODES = [404, 403, 410, 400, 500, 503]

LOGIN_REDIRECT_PATTERNS = [
    "login", "signin", "sign-in", "auth/", "session-expired",
    "access-denied", "unauthorized", "not-found", "error404",
]

EXPIRED_PATTERNS = [
    "job no longer available",
    "this job has expired",
    "position has been filled",
    "job listing has been removed",
    "no longer accepting",
    "posting has expired",
    "job is closed",
    "application closed",
    "position closed",
    "this position is no longer",
    "job has been removed",
    "listing is no longer active",
]


# ─────────────────────────────────────────────────────────────────────────────
# RESUME PROFILE (Venus Kondapalli - 13+ Yrs PM & UI UX Design Expert)
# ─────────────────────────────────────────────────────────────────────────────
RESUME_PROFILE = {
    "name": "Venus Kondapalli",
    "title": "Product Manager & UI UX Design Expert",
    "years_of_experience": 13,
    "locations": ["Germany", "Berlin", "Munich", "Frankfurt", "Hamburg", "Remote", "Europe", "Hyderabad", "Bangalore"],
    "notice_period": "Immediate / 1 month",
    "email": "venuskondapalli60@gmail.com",
    "phone": "+91 9618118274",
    "portfolio": "https://venuskondapalli.com",
    "behance": "https://www.behance.net/venusvikondapalli",
    "languages": {
        "German": "B1 Level",
        "English": "Proficient",
        "Hindi": "Proficient",
        "Telugu": "Native",
    },
    "core_skills": [
        "Product Management", "End-to-End Product Lifecycle", "Product Strategy",
        "Roadmap Definition", "User-Centered Design", "Interaction Design",
        "Prototyping & Wireframing", "User Research", "Contextual Inquiry",
        "Heuristic Evaluation", "Usability Testing", "User Interviews",
        "Affinity Diagrams", "User Personas", "Card Sorting", "Storyboarding",
        "Accessibility Testing", "DesignOps", "UX Writing", "Information Architecture",
        "Site Maps", "User Flows", "High-Fidelity UI Design", "Design Systems",
        "Reusable UI Components", "Front-end Governance", "Data-Driven Decision Making",
        "A/B Testing", "Behavioral Analytics", "Usability Benchmarking",
        "Product Telemetry", "AI-Enabled Product Initiatives", "LLM-Based Features",
        "Workflow Automation", "Stakeholder Management", "Agile", "Scrum", "SAFe",
        "Cross-Functional Leadership", "Developer Handoff", "Design Critique",
        "Sprint Planning", "GDPR Compliance", "Data Privacy", "Quality Standards",
        "Design Thinking", "Human Factors", "Mobile Design", "Responsive Web Design",
        "Dashboard Design", "Form Design", "Navigation Design", "Visual Design",
        "Typography", "Color Theory",
    ],
    "design_tools": [
        "Figma", "FigJam", "Adobe XD", "Adobe Illustrator", "Adobe Photoshop",
        "Adobe After Effects", "InVision", "Sketch", "Balsamiq", "Canva",
        "UXPin", "Miro", "Whimsical", "SharePoint",
    ],
    "servicenow_modules": [
        "Employee Center", "Service Portal", "IT Operations Management (ITOM)",
        "ITSM", "Workflows",
    ],
    "ai_tools": [
        "LLM Integration", "Figma AI", "Claude Design", "Intelligent Search",
        "Recommendation Engines", "Workflow Automation AI",
    ],
    "frontend_skills": [
        "React", "Angular", "HTML5", "CSS3", "Design-to-Code Handoff",
        "Front-End Architecture", "Component Design",
    ],
    "standards": [
        "WCAG 2.2", "WCAG 2.1", "EN 301 549", "ADA", "GDPR",
        "Material Design", "Apple HIG", "Section 508", "Keyboard Navigation",
        "Screen Reader Compatibility", "Color Contrast",
    ],
    "research_methods": [
        "User Interviews", "Usability Testing", "A/B Testing", "Heuristic Evaluation",
        "Card Sorting", "Moderated Testing", "Contextual Inquiry", "Surveys",
        "Field Studies", "Analytic Review", "Affinity Diagrams", "Empathy Mapping",
        "User Personas", "Task Success Rate", "SUS Scores",
    ],
    "domains": [
        "SaaS", "B2B SaaS", "Fintech", "E-commerce", "Healthcare", "Pharma",
        "HRMS", "IT Operations", "Enterprise Software", "Banking",
        "Salesforce Ecosystem", "ServiceNow Ecosystem", "Web Applications",
        "Mobile Applications", "Regulated Enterprise", "German Market",
    ],
    "industry_keywords": [
        "Product Management", "Enterprise UX", "Product Leadership",
        "End-to-End Product Lifecycle", "Design System", "Component Library",
        "Digital Transformation", "B2B SaaS", "Mobile App", "Web App",
        "Dashboard Design", "Data-Intensive Applications", "AI Product",
        "GDPR Compliance", "EN 301 549", "ServiceNow UX",
    ],
    "portfolio_keywords": [
        "Behance", "Portfolio", "Case Study", "Design Process", "Problem Solving",
        "User-Centered Design", "Human-Centered Design", "Design Thinking",
    ],
    "target_role_keywords": [
        "Product Manager", "Lead Product Manager", "UI/UX Design Expert",
        "UI/UX Designer", "UX Designer", "UI Designer", "Product Designer",
        "Lead Product Designer", "Senior Product Designer", "Staff UX Designer",
        "UX Design Consultant", "UX Researcher", "Lead UX Researcher",
        "Design Lead", "Head of UX", "Staff Design Engineer", "Enterprise UX Lead",
        "ServiceNow UX Consultant",
    ],
    "experience_highlights": [
        "13+ years spanning UX & digital product leadership",
        "Deep front-end fluency (React/Angular) + applied AI product experience",
        "Experience with regulated enterprise & German market standards (GDPR, EN 301 549)",
        "ServiceNow HRMS, Service Portal, ITOM workflow design expert",
        "Enterprise-scale data-intensive dashboards & responsive web/mobile apps",
        "Cross-functional leadership across product, design, and engineering",
    ],
}

ALL_RESUME_KEYWORDS = list(set(
    [kw.lower() for kw in RESUME_PROFILE["core_skills"]]
    + [kw.lower() for kw in RESUME_PROFILE["design_tools"]]
    + [kw.lower() for kw in RESUME_PROFILE["ai_tools"]]
    + [kw.lower() for kw in RESUME_PROFILE["frontend_skills"]]
    + [kw.lower() for kw in RESUME_PROFILE["standards"]]
    + [kw.lower() for kw in RESUME_PROFILE["research_methods"]]
    + [kw.lower() for kw in RESUME_PROFILE["domains"]]
    + [kw.lower() for kw in RESUME_PROFILE["industry_keywords"]]
    + [kw.lower() for kw in RESUME_PROFILE["target_role_keywords"]]
))

HIGH_WEIGHT_KEYWORDS = [
    "figma", "product manager", "product designer", "ux designer", "ui designer",
    "ui/ux", "lead designer", "design system", "user research", "prototyping",
    "wireframing", "interaction design", "accessibility", "wcag", "servicenow",
    "ai product", "enterprise ux", "agile", "scrum", "b2b saas", "usability testing",
    "information architecture", "staff designer", "german", "english",
]

MEDIUM_WEIGHT_KEYWORDS = [
    "html5", "css3", "react", "angular", "material design", "apple hig",
    "card sorting", "stakeholder", "sprint", "roadmap", "gdpr", "en 301 549",
    "fintech", "healthcare", "pharma", "mobile design", "responsive design",
    "visual design", "designops", "miro", "whimsical", "after effects",
    "illustrator", "photoshop", "sketch", "adobe xd", "berlin", "munich", "germany",
]
