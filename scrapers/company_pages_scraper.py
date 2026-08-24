"""
scrapers/company_pages_scraper.py - Company career pages scraper

Scrapes UI/UX job listings directly from company career pages.
Uses JSON-LD structured data, sitemap parsing, and HTML extraction.
Covers major Indian tech companies and startups.

URL POLICY: Every job returned MUST have a specific job-listing URL.
Jobs whose only URL is the career-page homepage are silently dropped.
"""

import logging
import re
import json
from urllib.parse import urljoin
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scrapers.base_scraper import BaseScraper
import config

logger = logging.getLogger(__name__)

# ── Design-related keywords to filter relevant jobs ──────────────────────────
# Includes role titles + key skills from the resume (Figma, design systems, etc.)
DESIGN_KEYWORDS = [
    "ui", "ux", "designer", "design", "product designer", "interaction",
    "visual designer", "experience designer", "interface", "figma",
    "user experience", "user interface", "hci", "usability",
    "design system", "wireframe", "prototype", "accessibility",
    "information architecture", "user research", "figma ai",
]


def _is_design_job(title: str) -> bool:
    """Return True if the job title is design-related."""
    title_lower = title.lower()
    return any(kw in title_lower for kw in DESIGN_KEYWORDS)


def _is_specific_job_url(url: str, page_url: str) -> bool:
    """
    Return True only if `url` looks like a specific job listing URL,
    not the career-page homepage.

    Rules:
      - Must start with http/https
      - Must NOT be the same as (or a trivial variant of) page_url
      - Must have a path that is longer than the page_url path
        OR contain a job-specific token (id, slug, jl=, jk=, /job/, /jobs/, /view/)
    """
    if not url or not url.startswith(("http://", "https://")):
        return False

    # Normalise trailing slashes for comparison
    norm_url = url.rstrip("/").lower()
    norm_page = page_url.rstrip("/").lower()

    if norm_url == norm_page:
        return False

    # Must contain at least one job-specific path segment or query param
    job_signals = [
        "/job/", "/jobs/", "/view/", "/opening/", "/position/",
        "/career/", "/listing/", "jl=", "jk=", "jobid=", "job_id=",
        "jobdetail", "job-detail", "job-listing",
    ]
    url_lower = url.lower()
    return any(sig in url_lower for sig in job_signals)


class CompanyPagesScraper(BaseScraper):
    """
    Scrapes job listings directly from company career pages.
    Highest priority source — direct company postings are most reliable.
    """

    SOURCE_NAME = "Company Career Pages"

    COMPANY_PAGES = [
        # ── Indian Unicorns & Startups ────────────────────────────────────────
        {"company": "Flipkart",      "url": "https://www.flipkartcareers.com/#!/joblist"},
        {"company": "Swiggy",        "url": "https://careers.swiggy.com/"},
        {"company": "Zomato",        "url": "https://www.zomato.com/careers"},
        {"company": "Meesho",        "url": "https://meesho.io/jobs"},
        {"company": "PhonePe",       "url": "https://careers.phonepe.com/"},
        {"company": "Razorpay",      "url": "https://razorpay.com/jobs/"},
        {"company": "CRED",          "url": "https://careers.cred.club/"},
        {"company": "Groww",         "url": "https://groww.in/careers"},
        {"company": "Zepto",         "url": "https://www.zeptonow.com/careers"},
        {"company": "Ola",           "url": "https://ola.careers/"},
        {"company": "Paytm",         "url": "https://paytm.com/careers"},
        {"company": "Freshworks",    "url": "https://www.freshworks.com/company/careers/"},
        {"company": "Zoho",          "url": "https://careers.zohocorp.com/jobs/Careers"},
        {"company": "Byju's",        "url": "https://byjus.com/careers/"},
        {"company": "Nykaa",         "url": "https://careers.nykaa.com/"},
        {"company": "Urban Company", "url": "https://www.urbancompany.com/careers"},
        {"company": "Lenskart",      "url": "https://www.lenskart.com/careers"},
        {"company": "Jupiter",       "url": "https://jupiter.money/careers/"},
        # ── IT Services ───────────────────────────────────────────────────────
        {"company": "Infosys",       "url": "https://career.infosys.com/joblist"},
        {"company": "Wipro",         "url": "https://careers.wipro.com/careers-home/jobs"},
        {"company": "HCL Technologies", "url": "https://www.hcltech.com/careers"},
        {"company": "Tech Mahindra", "url": "https://careers.techmahindra.com/"},
        # ── Design-focused ────────────────────────────────────────────────────
        {"company": "Hotstar",       "url": "https://careers.hotstar.com/"},
        {"company": "ShareChat",     "url": "https://sharechat.com/careers"},
        {"company": "Dream11",       "url": "https://www.dream11.com/careers"},
        {"company": "Juspay",        "url": "https://juspay.in/careers"},
        {"company": "Setu",          "url": "https://setu.co/careers"},
        {"company": "Darwinbox",     "url": "https://darwinbox.com/careers"},
    ]

    def scrape(self) -> List[Dict]:
        """Main scrape method — iterates over all company pages."""
        logger.info("Company Pages: Starting scrape...")
        raw_jobs = []

        for company_config in self.COMPANY_PAGES:
            try:
                jobs = self._scrape_company(company_config)
                raw_jobs.extend(jobs)
                if jobs:
                    logger.info(
                        f"Company Pages: {company_config['company']}: "
                        f"{len(jobs)} design jobs found"
                    )
            except Exception as e:
                logger.error(
                    f"Company Pages: Error scraping {company_config['company']}: {e}"
                )

        return self._filter_and_normalize(raw_jobs)

    def _scrape_company(self, company_config: Dict) -> List[Dict]:
        """Scrape a single company's career page."""
        company = company_config["company"]
        url = company_config["url"]

        resp = self._get(url, headers=self._get_headers({"Referer": url}))
        if not resp:
            logger.debug(f"Company Pages: Could not reach {company} ({url})")
            return []

        try:
            soup = BeautifulSoup(resp.text, "html.parser")
            jobs = []

            # Strategy 1: JSON-LD structured data (most reliable)
            json_ld_jobs = self._extract_json_ld(soup, company, url)
            if json_ld_jobs:
                jobs.extend(json_ld_jobs)

            # Strategy 2: Next.js / React embedded data
            if not jobs:
                next_jobs = self._extract_next_data(resp.text, company, url)
                if next_jobs:
                    jobs.extend(next_jobs)

            # Strategy 3: HTML card parsing
            if not jobs:
                html_jobs = self._extract_html_cards(soup, company, url)
                jobs.extend(html_jobs)

            # Keep only design jobs with specific (non-homepage) URLs
            design_jobs = [
                j for j in jobs
                if _is_design_job(j.get("title", ""))
                and _is_specific_job_url(j.get("url", ""), url)
            ]

            skipped = len(jobs) - len(design_jobs)
            if skipped:
                logger.debug(
                    f"Company Pages: {company}: dropped {skipped} jobs "
                    f"(homepage URL or non-design title)"
                )
            return design_jobs

        except Exception as e:
            logger.error(f"Company Pages: Parse error for {company}: {e}")
            return []

    # ── JSON-LD Extraction ────────────────────────────────────────────────────

    def _extract_json_ld(self, soup: BeautifulSoup, company: str,
                          page_url: str) -> List[Dict]:
        """Extract jobs from JSON-LD structured data."""
        jobs = []
        for script in soup.find_all("script", type="application/ld+json"):
            try:
                data = json.loads(script.string or "")
                if isinstance(data, list):
                    for item in data:
                        job = self._parse_json_ld_item(item, company, page_url)
                        if job:
                            jobs.append(job)
                elif isinstance(data, dict):
                    if data.get("@type") == "JobPosting":
                        job = self._parse_json_ld_item(data, company, page_url)
                        if job:
                            jobs.append(job)
                    elif data.get("@type") in ["ItemList", "WebPage"]:
                        for item in data.get("itemListElement", []):
                            job = self._parse_json_ld_item(item, company, page_url)
                            if job:
                                jobs.append(job)
            except (json.JSONDecodeError, AttributeError):
                pass
        return jobs

    def _parse_json_ld_item(self, data: Dict, company: str,
                             page_url: str) -> Optional[Dict]:
        """
        Parse a single JSON-LD JobPosting item.
        Returns None if no specific job URL is available.
        """
        if not isinstance(data, dict):
            return None
        if data.get("@type") != "JobPosting":
            return None

        try:
            title = data.get("title", "")
            if not title:
                return None

            # ── URL: must be a specific job listing, not the homepage ─────────
            url = data.get("url", "").strip()
            if not url:
                # Try identifier field (some schemas use this)
                identifier = data.get("identifier", {})
                if isinstance(identifier, dict):
                    url = identifier.get("value", "").strip()
            if not url or not url.startswith(("http://", "https://")):
                logger.debug(
                    f"JSON-LD: no specific URL for '{title}' @ {company} — skipped"
                )
                return None

            org = data.get("hiringOrganization", {})
            company_name = (
                org.get("name", company) if isinstance(org, dict) else company
            )

            location_data = data.get("jobLocation", {})
            if isinstance(location_data, list):
                location_data = location_data[0] if location_data else {}
            if isinstance(location_data, dict):
                addr = location_data.get("address", {})
                location = (
                    addr.get("addressLocality", "")
                    or addr.get("addressRegion", "India")
                    if isinstance(addr, dict)
                    else "India"
                )
            else:
                location = "India"

            posted_raw = data.get("datePosted", "")
            description = data.get("description", "")
            if description:
                description = re.sub(r"<[^>]+>", " ", description)
                description = re.sub(r"\s+", " ", description).strip()[:2000]

            return {
                "title": title,
                "company": company_name,
                "location": location,
                "url": url,
                "apply_url": url,
                "source": self.SOURCE_NAME,
                "posted_date_raw": posted_raw,
                "description": description,
            }
        except Exception as e:
            logger.debug(f"JSON-LD item parse error: {e}")
            return None

    # ── Next.js Data Extraction ───────────────────────────────────────────────

    def _extract_next_data(self, html: str, company: str,
                            page_url: str) -> List[Dict]:
        """
        Extract jobs from Next.js __NEXT_DATA__ JSON.
        Only jobs with a specific (non-homepage) URL are included.
        """
        try:
            soup = BeautifulSoup(html, "html.parser")
            script = soup.find("script", id="__NEXT_DATA__")
            if not script:
                return []

            data = json.loads(script.string or "")
            props = data.get("props", {}).get("pageProps", {})

            job_list = (
                props.get("jobs", [])
                or props.get("openings", [])
                or props.get("positions", [])
                or props.get("jobListings", [])
                or props.get("careers", [])
            )

            jobs = []
            for item in job_list:
                if not isinstance(item, dict):
                    continue
                title = (
                    item.get("title", "")
                    or item.get("name", "")
                    or item.get("role", "")
                )
                if not title:
                    continue

                location = (
                    item.get("location", "")
                    or item.get("city", "")
                    or item.get("office", "India")
                )
                if isinstance(location, list):
                    location = ", ".join(str(loc) for loc in location)

                job_id = str(item.get("id", "") or item.get("jobId", ""))
                slug = item.get("slug", "") or item.get("url", "")

                # Build a specific URL — skip if we can't
                if slug and not slug.startswith("http"):
                    url = urljoin(page_url, slug)
                elif slug:
                    url = slug
                elif job_id:
                    url = f"{page_url.rstrip('/')}/{job_id}"
                else:
                    logger.debug(
                        f"Next.js: no slug/id for '{title}' @ {company} — skipped"
                    )
                    continue  # No specific URL available — skip

                # Final guard: must not be the career homepage
                if url.rstrip("/") == page_url.rstrip("/"):
                    logger.debug(
                        f"Next.js: URL equals homepage for '{title}' @ {company} — skipped"
                    )
                    continue

                posted_raw = (
                    item.get("createdAt", "")
                    or item.get("postedAt", "")
                    or item.get("datePosted", "")
                )
                description = (
                    item.get("description", "")
                    or item.get("jobDescription", "")
                    or item.get("content", "")
                )
                if description:
                    description = re.sub(r"<[^>]+>", " ", str(description))
                    description = re.sub(r"\s+", " ", description).strip()[:2000]

                jobs.append({
                    "title": title,
                    "company": company,
                    "location": str(location),
                    "url": url,
                    "apply_url": url,
                    "source": self.SOURCE_NAME,
                    "posted_date_raw": posted_raw,
                    "description": description,
                })

            return jobs
        except (json.JSONDecodeError, AttributeError, KeyError) as e:
            logger.debug(f"Next.js data parse error for {company}: {e}")
            return []

    # ── HTML Card Extraction ──────────────────────────────────────────────────

    def _extract_html_cards(self, soup: BeautifulSoup, company: str,
                             page_url: str) -> List[Dict]:
        """
        Extract jobs from HTML job cards.
        Cards without a specific job-listing URL are skipped.
        """
        jobs = []

        selectors = [
            ("div",     re.compile(r"job-card|jobCard|job-listing|opening|position|career-item")),
            ("li",      re.compile(r"job|opening|position|career")),
            ("article", re.compile(r"job|opening|position")),
            ("tr",      re.compile(r"job|opening")),
        ]

        job_cards = []
        for tag, class_pattern in selectors:
            cards = soup.find_all(tag, class_=class_pattern)
            if cards:
                job_cards = cards
                break

        for card in job_cards:
            try:
                # Title
                title_el = (
                    card.find(class_=re.compile(r"title|role|position|designation"))
                    or card.find("h2")
                    or card.find("h3")
                    or card.find("h4")
                )
                if not title_el:
                    continue
                title = title_el.get_text(strip=True)
                if not title or not _is_design_job(title):
                    continue

                # URL — must be a specific job listing link
                link_el = card.find("a", href=True)
                if not link_el:
                    logger.debug(
                        f"HTML card: no <a> link for '{title}' @ {company} — skipped"
                    )
                    continue

                href = link_el.get("href", "").strip()
                if not href:
                    continue
                if not href.startswith("http"):
                    href = urljoin(page_url, href)

                # Reject if it resolves back to the career homepage
                if href.rstrip("/") == page_url.rstrip("/"):
                    logger.debug(
                        f"HTML card: URL is homepage for '{title}' @ {company} — skipped"
                    )
                    continue

                # Location
                loc_el = card.find(class_=re.compile(r"location|city|office"))
                location = loc_el.get_text(strip=True) if loc_el else "India"

                # Date
                date_el = card.find(class_=re.compile(r"date|posted|time"))
                posted_raw = date_el.get_text(strip=True) if date_el else ""

                # Description
                desc_el = card.find(class_=re.compile(r"description|summary|snippet"))
                description = desc_el.get_text(strip=True) if desc_el else ""

                jobs.append({
                    "title": title,
                    "company": company,
                    "location": location,
                    "url": href,
                    "apply_url": href,
                    "source": self.SOURCE_NAME,
                    "posted_date_raw": posted_raw,
                    "description": description,
                })
            except Exception as e:
                logger.debug(f"HTML card parse error for {company}: {e}")

        return jobs
