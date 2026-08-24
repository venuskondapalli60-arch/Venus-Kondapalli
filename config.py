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
SEARCH_LOCATIONS = ["Hyderabad", "Bangalore", "Remote", "India"]
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
    "UI/UX Designer",
    "UI Designer",
    "UX Designer",
    "Product Designer",
    "UX Researcher",
    "UI Researcher",
    "Senior UI/UX Designer",
    "Interaction Designer",
    "UX Consultant",
    "Visual Designer",
    "Web Designer",
    "Design System Designer",
    "Experience Designer",
    "User Experience Specialist",
    "User Interface Specialist",
    "Digital Designer",
    "Human-Centered Designer",
    "UX Strategist",
    "Mobile App Designer",
    "Responsive Web Designer",
    "Design Lead",
    "Product Experience Designer",
]

SEARCH_KEYWORDS = [
    "UI UX Designer",
    "UX Designer",
    "UI Designer",
    "Product Designer",
    "UX Researcher",
    "Interaction Designer",
    "Visual Designer",
    "Design Lead",
    "Web Designer",
]

# Skill-based search queries derived from resume profile
# These expand search beyond job titles to catch roles that emphasise
# specific tools/skills the candidate has (Figma, design systems, etc.)
SKILL_SEARCH_KEYWORDS = [
    "Figma Designer",
    "Design System Designer",
    "User Research Designer",
    "Accessibility UX Designer",
    "Enterprise UX Designer",
    "Mobile UX Designer",
    "B2B SaaS Designer",
    "Wireframing Prototyping Designer",
    "UX Researcher",
    "Information Architecture Designer",
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
    "Accept-Language": "en-US,en;q=0.9",
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
    "Company Career Pages": 1,
    "LinkedIn": 2,
    "Naukri": 3,
    "Wellfound": 4,
    "Indeed": 5,
    "Foundit": 6,
    "Glassdoor": 7,
    "Instahyre": 8,
}

# ─────────────────────────────────────────────
# SCRAPER ENDPOINTS
# ─────────────────────────────────────────────
SCRAPER_URLS = {
    "naukri_api": "https://www.naukri.com/jobapi/v3/search",
    "naukri_base": "https://www.naukri.com",
    "indeed_base": "https://in.indeed.com/jobs",
    "linkedin_guest": "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search",
    "linkedin_search": "https://www.linkedin.com/jobs/search/",
    "foundit_base": "https://www.foundit.in/srp/results",
    "glassdoor_base": "https://www.glassdoor.co.in/Job/jobs.htm",
    "wellfound_base": "https://wellfound.com/jobs",
    "instahyre_api": "https://www.instahyre.com/api/v1/search_jobs/",
}

# ─────────────────────────────────────────────
# COMPANY CAREER PAGES
# ─────────────────────────────────────────────
COMPANY_CAREER_PAGES = [
    {"company": "Flipkart",  "url": "https://www.flipkartcareers.com/#!/joblist"},
    {"company": "Swiggy",    "url": "https://careers.swiggy.com/#careers"},
    {"company": "Zomato",    "url": "https://www.zomato.com/careers"},
    {"company": "Meesho",    "url": "https://meesho.io/jobs"},
    {"company": "PhonePe",   "url": "https://careers.phonepe.com/"},
    {"company": "Razorpay",  "url": "https://razorpay.com/jobs/"},
    {"company": "CRED",      "url": "https://careers.cred.club/"},
    {"company": "Groww",     "url": "https://groww.in/careers"},
    {"company": "Ola",       "url": "https://ola.careers/"},
    {"company": "Paytm",     "url": "https://paytm.com/careers"},
    {"company": "Byju's",    "url": "https://byjus.com/careers/"},
    {"company": "Freshworks", "url": "https://www.freshworks.com/company/careers/"},
    {"company": "Zoho",      "url": "https://careers.zohocorp.com/"},
    {"company": "Infosys",   "url": "https://www.infosys.com/careers/"},
    {"company": "Wipro",     "url": "https://careers.wipro.com/"},
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
# RESUME PROFILE  (merged from resume_data.py)
# ─────────────────────────────────────────────────────────────────────────────
RESUME_PROFILE = {
    "name": "Srikar Jupudi",
    "title": "UI/UX Designer",
    "years_of_experience": 4,
    "locations": ["Hyderabad", "Bangalore"],
    "notice_period": "2 months",
    "core_skills": [
        "User Research","Usability Testing","Wireframing","Interaction Design",
        "High-Fidelity Prototyping","Information Architecture","Design Systems",
        "UI Components","Accessibility","WCAG 2.1","ADA","Section 508",
        "AI-Assisted Prototyping","Agile","Scrum","Cross-functional Collaboration",
        "Stakeholder Management","Developer Handoff","Design Critique","Sprint Planning",
        "User Flows","Sitemaps","Heuristic Evaluation","Card Sorting","A/B Testing",
        "UX Metrics","Task Success Rate","SUS Scores","Design Specifications",
        "Pixel-accurate Implementation","Moderated Usability Testing",
        "Stakeholder Interviews","Pain Point Analysis","Design Validation",
        "Product Roadmap","UX Strategy","Visual Design","Typography","Color Theory",
        "Layout Design","Responsive Design","Mobile Design","Web Design",
    ],
    "design_tools": [
        "Figma","Adobe XD","Sketch","Illustrator","Photoshop","InDesign",
        "InVision","Miro","Balsamiq","Zeplin","Maze","UserTesting",
    ],
    "ai_tools": ["Stitch","Claude Design","Figma AI","Relume","Galileo AI"],
    "frontend_skills": ["HTML5","CSS3","Design-to-Code Handoff","Developer Collaboration"],
    "standards": [
        "WCAG 2.0","WCAG 2.1","ADA","Section 508","Material Design","Apple HIG",
        "Keyboard Navigation","Screen Reader Compatibility","Color Contrast",
    ],
    "research_methods": [
        "User Interviews","Usability Testing","A/B Testing","Heuristic Evaluation",
        "Card Sorting","Moderated Testing","Participant Recruitment","Test Scripting",
        "Results Analysis","Design Iteration",
    ],
    "domains": [
        "HealthTech","EHR","Electronic Health Records","HRMS",
        "Human Resource Management","Environmental Services","EVS",
        "Fintech","Healthcare","B2B SaaS","Enterprise Software",
        "Web Applications","Mobile Applications",
    ],
    "industry_keywords": [
        "Enterprise UX","Product Design","End-to-End Design","Design Leadership",
        "Design System","Component Library","Prototype","Wireframe","User Journey",
        "Customer Experience","Digital Transformation","SaaS","B2B","B2C",
        "Mobile App","Web App","Dashboard Design","Form Design",
        "Navigation Design","Onboarding Design",
    ],
    "portfolio_keywords": [
        "Behance","Portfolio","Case Study","Design Process","Problem Solving",
        "User-Centered Design","Human-Centered Design","Design Thinking",
    ],
    "target_role_keywords": [
        "UI/UX Designer","UX Designer","UI Designer","Product Designer",
        "UX Researcher","Interaction Designer","Visual Designer","Design Lead",
        "Senior Designer","Web Designer","Mobile Designer","Experience Designer",
        "Digital Designer","Design Consultant","UX Strategist","Design System Designer",
    ],
    "experience_highlights": [
        "4+ years UI/UX experience","Enterprise-grade digital experiences",
        "10,000+ users served","20+ product modules","End-to-end product design",
        "Agile embedded design lead","Multiple concurrent projects",
        "Cross-functional team collaboration","Design system maintenance",
        "Accessibility champion",
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
    "figma","ux designer","ui designer","ui/ux","product designer",
    "user research","usability testing","wireframing","prototyping",
    "interaction design","design system","accessibility","wcag",
    "information architecture","agile","figma ai","adobe xd","sketch",
    "heuristic evaluation","a/b testing","user flows","high-fidelity",
    "developer handoff","zeplin","invision","miro",
]

MEDIUM_WEIGHT_KEYWORDS = [
    "html5","css3","material design","apple hig","card sorting",
    "stakeholder","sprint","scrum","b2b saas","enterprise",
    "healthtech","fintech","mobile design","responsive design",
    "visual design","typography","color theory","balsamiq","maze",
]
