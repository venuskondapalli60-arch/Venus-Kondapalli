"""
scrapers/naukri_scraper.py - Naukri.com job scraper

Uses Naukri's internal search API (v3) to fetch UI/UX job listings.
Falls back to HTML scraping if API is unavailable.
"""

import json
import logging
import re
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scrapers.base_scraper import BaseScraper
import config

logger = logging.getLogger(__name__)


class NaukriScraper(BaseScraper):
    """Scrapes UI/UX job listings from Naukri.com."""

    SOURCE_NAME = "Naukri"

    # Naukri API endpoint
    API_URL = "https://www.naukri.com/jobapi/v3/search"

    # HTML fallback URLs
    HTML_URLS = [
        "https://www.naukri.com/ui-ux-designer-jobs-in-hyderabad",
        "https://www.naukri.com/ux-designer-jobs-in-hyderabad",
        "https://www.naukri.com/ui-designer-jobs-in-hyderabad",
        "https://www.naukri.com/product-designer-jobs-in-hyderabad",
        "https://www.naukri.com/ui-ux-designer-jobs-in-bangalore",
        "https://www.naukri.com/ux-designer-jobs-in-bangalore",
    ]

    def scrape(self) -> List[Dict]:
        """Main scrape method — tries API first, then HTML fallback."""
        logger.info("Naukri: Starting scrape...")
        raw_jobs = []

        # Try API approach
        api_jobs = self._scrape_via_api()
        if api_jobs:
            raw_jobs.extend(api_jobs)
            logger.info(f"Naukri API: {len(api_jobs)} raw jobs fetched")
        else:
            # Fallback to HTML scraping
            logger.info("Naukri: API failed, trying HTML scraping...")
            html_jobs = self._scrape_via_html()
            raw_jobs.extend(html_jobs)
            logger.info(f"Naukri HTML: {len(html_jobs)} raw jobs fetched")

        return self._filter_and_normalize(raw_jobs)

    # ── API Scraping ──────────────────────────────────────────────────────────

    def _scrape_via_api(self) -> List[Dict]:
        """Use Naukri's internal search API."""
        raw_jobs = []
        keywords = [kw.lower() for kw in config.ALL_SEARCH_KEYWORDS]

        for keyword in keywords:
            for location in ["hyderabad", "bangalore", "remote"]:
                jobs = self._fetch_api_page(keyword, location)
                raw_jobs.extend(jobs)
                if len(raw_jobs) >= 100:
                    break
            if len(raw_jobs) >= 100:
                break

        return raw_jobs

    def _fetch_api_page(self, keyword: str, location: str,
                        page: int = 1) -> List[Dict]:
        """Fetch one page from Naukri API."""
        params = {
            "noOfResults": 20,
            "urlType": "search_by_key_loc",
            "searchType": "adv",
            "keyword": keyword,
            "location": location,
            "pageNo": page,
            "sort": "1",       # Sort by date (newest first)
            "bucketId": "1",
            "seoKey": f"{keyword.replace(' ', '-')}-jobs-in-{location}",
            "src": "jobsearchDesk",
            "latLong": "",
        }

        headers = self._get_headers({
            "appid": "109",
            "systemid": "Naukri",
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Referer": "https://www.naukri.com/",
        })

        resp = self._get(self.API_URL, params=params, headers=headers)
        if not resp:
            return []

        try:
            data = resp.json()
            job_list = data.get("jobDetails", [])
            return [self._parse_api_job(j) for j in job_list if j]
        except (json.JSONDecodeError, KeyError) as e:
            logger.debug(f"Naukri API parse error: {e}")
            return []

    def _parse_api_job(self, job: Dict) -> Dict:
        """Parse a single job from Naukri API response."""
        # Extract job URL
        job_id = str(job.get("jobId", ""))
        title = job.get("title", "")
        company = job.get("companyName", "")

        # Build URL
        title_slug = re.sub(r"[^\w\s-]", "", title.lower()).strip()
        title_slug = re.sub(r"\s+", "-", title_slug)
        company_slug = re.sub(r"[^\w\s-]", "", company.lower()).strip()
        company_slug = re.sub(r"\s+", "-", company_slug)
        url = f"https://www.naukri.com/{title_slug}-{company_slug}-{job_id}"

        # Location
        locations = job.get("placeholders", [])
        location_str = ""
        for ph in locations:
            if ph.get("type") == "location":
                location_str = ph.get("label", "")
                break

        # Posted date
        posted_raw = job.get("footerPlaceholderLabel", "") or job.get("createdDate", "")

        # Description
        desc_parts = []
        for ph in job.get("placeholders", []):
            if ph.get("type") in ["experience", "salary", "skills"]:
                desc_parts.append(ph.get("label", ""))
        description = " | ".join(filter(None, desc_parts))

        # Skills from tags
        tags = job.get("tagsAndSkills", "")
        if tags:
            description += f" Skills: {tags}"

        return {
            "job_id": f"naukri_{job_id}",
            "title": title,
            "company": company,
            "location": location_str or "India",
            "url": url,
            "apply_url": url,
            "source": self.SOURCE_NAME,
            "posted_date_raw": posted_raw,
            "description": description,
        }

    # ── HTML Scraping (Fallback) ───────────────────────────────────────────────

    def _scrape_via_html(self) -> List[Dict]:
        """Scrape Naukri HTML search result pages."""
        raw_jobs = []

        for url in self.HTML_URLS:
            jobs = self._scrape_html_page(url)
            raw_jobs.extend(jobs)
            logger.debug(f"Naukri HTML {url}: {len(jobs)} jobs")

        return raw_jobs

    def _scrape_html_page(self, url: str) -> List[Dict]:
        """Parse a single Naukri HTML search results page."""
        headers = self._get_headers({
            "Referer": "https://www.naukri.com/",
        })
        resp = self._get(url, headers=headers)
        if not resp:
            return []

        try:
            soup = BeautifulSoup(resp.text, "html.parser")
            jobs = []

            # Naukri job cards
            job_cards = soup.find_all("article", class_=re.compile(r"jobTuple|job-tuple|jobCard"))
            if not job_cards:
                # Try alternate selectors
                job_cards = soup.find_all("div", class_=re.compile(r"jobTuple|srp-jobtuple"))

            for card in job_cards:
                job = self._parse_html_card(card)
                if job:
                    jobs.append(job)

            return jobs
        except Exception as e:
            logger.error(f"Naukri HTML parse error for {url}: {e}")
            return []

    def _parse_html_card(self, card) -> Optional[Dict]:
        """Parse a single Naukri HTML job card."""
        try:
            # Title
            title_el = (
                card.find("a", class_=re.compile(r"title|jobTitle"))
                or card.find("h2")
                or card.find("a", {"data-ga-track": True})
            )
            if not title_el:
                return None
            title = title_el.get_text(strip=True)
            job_url = title_el.get("href", "")

            if not job_url.startswith("http"):
                job_url = "https://www.naukri.com" + job_url

            # Company
            company_el = card.find(class_=re.compile(r"companyInfo|company-name|subTitle"))
            company = company_el.get_text(strip=True) if company_el else "Unknown"

            # Location
            loc_el = card.find(class_=re.compile(r"location|loc"))
            location = loc_el.get_text(strip=True) if loc_el else "India"

            # Posted date
            date_el = card.find(class_=re.compile(r"date|posted|freshness"))
            posted_raw = date_el.get_text(strip=True) if date_el else ""

            # Description / skills
            desc_el = card.find(class_=re.compile(r"job-description|desc|skill"))
            description = desc_el.get_text(strip=True) if desc_el else ""

            return {
                "title": title,
                "company": company,
                "location": location,
                "url": job_url,
                "apply_url": job_url,
                "source": self.SOURCE_NAME,
                "posted_date_raw": posted_raw,
                "description": description,
            }
        except Exception as e:
            logger.debug(f"Naukri card parse error: {e}")
            return None
