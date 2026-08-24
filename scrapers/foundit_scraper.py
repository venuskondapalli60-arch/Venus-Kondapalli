"""
scrapers/foundit_scraper.py - Foundit (formerly Monster India) job scraper

Scrapes UI/UX job listings from foundit.in using their search API and HTML.
"""

import logging
import re
import json
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scrapers.base_scraper import BaseScraper
import config

logger = logging.getLogger(__name__)


class FounditScraper(BaseScraper):
    """Scrapes UI/UX job listings from Foundit.in."""

    SOURCE_NAME = "Foundit"
    BASE_URL = "https://www.foundit.in/srp/results"
    API_URL = "https://www.foundit.in/middleware/jobsearch/v1/search"

    @property
    def SEARCH_QUERIES(self):
        locations = ["Hyderabad", "Bangalore", "India"]
        return [
            (kw.lower(), loc)
            for kw in config.ALL_SEARCH_KEYWORDS
            for loc in locations
        ]

    def scrape(self) -> List[Dict]:
        """Main scrape method."""
        logger.info("Foundit: Starting scrape...")
        raw_jobs = []

        # Try API first
        api_jobs = self._scrape_via_api()
        if api_jobs:
            raw_jobs.extend(api_jobs)
        else:
            # Fallback to HTML
            html_jobs = self._scrape_via_html()
            raw_jobs.extend(html_jobs)

        return self._filter_and_normalize(raw_jobs)

    # ── API Scraping ──────────────────────────────────────────────────────────

    def _scrape_via_api(self) -> List[Dict]:
        """Use Foundit's search API."""
        raw_jobs = []
        for query, location in self.SEARCH_QUERIES[:4]:  # Limit API calls
            jobs = self._fetch_api(query, location)
            raw_jobs.extend(jobs)
        return raw_jobs

    def _fetch_api(self, query: str, location: str) -> List[Dict]:
        """Fetch from Foundit API."""
        payload = {
            "query": query,
            "locations": [location],
            "experienceRanges": ["2|5"],
            "sort": "date",
            "limit": 20,
            "offset": 0,
        }

        headers = self._get_headers({
            "Content-Type": "application/json",
            "Referer": "https://www.foundit.in/",
            "Origin": "https://www.foundit.in",
        })

        resp = self._post(self.API_URL, json_data=payload, headers=headers)
        if not resp:
            return []

        try:
            data = resp.json()
            job_list = data.get("jobSearchResponse", {}).get("data", [])
            if not job_list:
                job_list = data.get("data", [])
            return [self._parse_api_job(j) for j in job_list if j]
        except (json.JSONDecodeError, KeyError) as e:
            logger.debug(f"Foundit API parse error: {e}")
            return []

    def _parse_api_job(self, job: Dict) -> Dict:
        """Parse a job from Foundit API response."""
        job_id = str(job.get("jobId", "") or job.get("id", ""))
        title = job.get("designation", "") or job.get("title", "")
        company = job.get("companyName", "") or job.get("company", "")
        location = job.get("location", "") or job.get("city", "India")
        posted_raw = job.get("freshness", "") or job.get("postedDate", "")

        # Build URL
        title_slug = re.sub(r"[^\w\s-]", "", title.lower()).strip()
        title_slug = re.sub(r"\s+", "-", title_slug)
        url = f"https://www.foundit.in/job/{title_slug}-{job_id}"

        # Description
        description = job.get("jobDescription", "") or job.get("description", "")
        if description:
            description = re.sub(r"<[^>]+>", " ", description)
            description = re.sub(r"\s+", " ", description).strip()

        # Skills
        skills = job.get("keySkills", [])
        if isinstance(skills, list):
            description += " Skills: " + ", ".join(skills)
        elif isinstance(skills, str):
            description += f" Skills: {skills}"

        return {
            "job_id": f"foundit_{job_id}",
            "title": title,
            "company": company,
            "location": location,
            "url": url,
            "apply_url": url,
            "source": self.SOURCE_NAME,
            "posted_date_raw": posted_raw,
            "description": description,
        }

    # ── HTML Scraping ─────────────────────────────────────────────────────────

    def _scrape_via_html(self) -> List[Dict]:
        """Scrape Foundit HTML search pages."""
        raw_jobs = []
        for query, location in self.SEARCH_QUERIES:
            jobs = self._scrape_html_page(query, location)
            raw_jobs.extend(jobs)
        return raw_jobs

    def _scrape_html_page(self, query: str, location: str) -> List[Dict]:
        """Scrape one Foundit search results page."""
        params = {
            "query": query,
            "locations": location,
            "sort": "date",
        }

        headers = self._get_headers({
            "Referer": "https://www.foundit.in/",
        })

        resp = self._get(self.BASE_URL, params=params, headers=headers)
        if not resp:
            return []

        try:
            soup = BeautifulSoup(resp.text, "html.parser")
            jobs = []

            # Try JSON-LD structured data first
            json_ld = soup.find_all("script", type="application/ld+json")
            for script in json_ld:
                try:
                    data = json.loads(script.string or "")
                    if isinstance(data, list):
                        for item in data:
                            if item.get("@type") == "JobPosting":
                                job = self._parse_json_ld(item)
                                if job:
                                    jobs.append(job)
                    elif data.get("@type") == "JobPosting":
                        job = self._parse_json_ld(data)
                        if job:
                            jobs.append(job)
                except (json.JSONDecodeError, AttributeError):
                    pass

            if jobs:
                return jobs

            # HTML card fallback
            job_cards = soup.find_all(
                "div",
                class_=re.compile(r"jobCard|job-card|card-apply|srpResultCardContainer")
            )
            for card in job_cards:
                job = self._parse_html_card(card)
                if job:
                    jobs.append(job)

            return jobs
        except Exception as e:
            logger.error(f"Foundit HTML parse error: {e}")
            return []

    def _parse_json_ld(self, data: Dict) -> Optional[Dict]:
        """Parse a JobPosting from JSON-LD structured data."""
        try:
            title = data.get("title", "")
            company = data.get("hiringOrganization", {}).get("name", "")
            location_data = data.get("jobLocation", {})
            if isinstance(location_data, list):
                location_data = location_data[0] if location_data else {}
            location = (
                location_data.get("address", {}).get("addressLocality", "")
                or location_data.get("name", "India")
            )
            url = data.get("url", "") or data.get("identifier", {}).get("value", "")
            posted_raw = data.get("datePosted", "")
            description = data.get("description", "")
            if description:
                description = re.sub(r"<[^>]+>", " ", description)
                description = re.sub(r"\s+", " ", description).strip()[:2000]

            if not title or not url:
                return None

            return {
                "title": title,
                "company": company or "Unknown",
                "location": location,
                "url": url,
                "apply_url": url,
                "source": self.SOURCE_NAME,
                "posted_date_raw": posted_raw,
                "description": description,
            }
        except Exception as e:
            logger.debug(f"Foundit JSON-LD parse error: {e}")
            return None

    def _parse_html_card(self, card) -> Optional[Dict]:
        """Parse a single Foundit HTML job card."""
        try:
            title_el = (
                card.find(class_=re.compile(r"jobTitle|designation|title"))
                or card.find("h3")
                or card.find("h2")
            )
            if not title_el:
                return None
            title = title_el.get_text(strip=True)

            link_el = card.find("a", href=True)
            if not link_el:
                return None
            href = link_el.get("href", "")
            if not href.startswith("http"):
                href = "https://www.foundit.in" + href

            company_el = card.find(class_=re.compile(r"companyName|company"))
            company = company_el.get_text(strip=True) if company_el else "Unknown"

            loc_el = card.find(class_=re.compile(r"location|city"))
            location = loc_el.get_text(strip=True) if loc_el else "India"

            date_el = card.find(class_=re.compile(r"date|posted|freshness"))
            posted_raw = date_el.get_text(strip=True) if date_el else ""

            desc_el = card.find(class_=re.compile(r"description|snippet|summary"))
            description = desc_el.get_text(strip=True) if desc_el else ""

            return {
                "title": title,
                "company": company,
                "location": location,
                "url": href,
                "apply_url": href,
                "source": self.SOURCE_NAME,
                "posted_date_raw": posted_raw,
                "description": description,
            }
        except Exception as e:
            logger.debug(f"Foundit card parse error: {e}")
            return None
