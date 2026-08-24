"""
scrapers/instahyre_scraper.py - Instahyre job scraper

Scrapes UI/UX design job listings from instahyre.com using their API.
Instahyre focuses on quality tech/design jobs in India.
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


class InstahyreScraper(BaseScraper):
    """Scrapes UI/UX job listings from Instahyre.com."""

    SOURCE_NAME = "Instahyre"
    API_URL = "https://www.instahyre.com/api/v1/search_jobs/"
    BASE_URL = "https://www.instahyre.com"

    @property
    def SEARCH_QUERIES(self):
        return list(config.ALL_SEARCH_KEYWORDS)

    LOCATIONS = ["Hyderabad", "Bangalore", "Remote"]

    def scrape(self) -> List[Dict]:
        """Main scrape method."""
        logger.info("Instahyre: Starting scrape...")
        raw_jobs = []

        # Try API
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
        """Use Instahyre's search API."""
        raw_jobs = []

        for query in self.SEARCH_QUERIES[:3]:
            for location in self.LOCATIONS[:2]:
                jobs = self._fetch_api(query, location)
                raw_jobs.extend(jobs)

        return raw_jobs

    def _fetch_api(self, query: str, location: str) -> List[Dict]:
        """Fetch from Instahyre API."""
        params = {
            "q": query,
            "location": location,
            "experience_min": 2,
            "experience_max": 6,
            "page": 1,
        }

        headers = self._get_headers({
            "Referer": "https://www.instahyre.com/",
            "X-Requested-With": "XMLHttpRequest",
            "Accept": "application/json",
        })

        resp = self._get(self.API_URL, params=params, headers=headers)
        if not resp:
            return []

        try:
            data = resp.json()
            job_list = (
                data.get("results", [])
                or data.get("jobs", [])
                or data.get("data", [])
            )
            return [self._parse_api_job(j) for j in job_list if j]
        except (json.JSONDecodeError, KeyError) as e:
            logger.debug(f"Instahyre API parse error: {e}")
            return []

    def _parse_api_job(self, job: Dict) -> Dict:
        """Parse a job from Instahyre API response."""
        job_id = str(job.get("id", "") or job.get("job_id", ""))
        title = job.get("designation", "") or job.get("title", "")
        company_data = job.get("employer", {}) or {}
        company = (
            company_data.get("name", "")
            if isinstance(company_data, dict)
            else str(company_data)
        ) or job.get("company", "")

        location = job.get("location", "") or job.get("city", "India")
        if isinstance(location, list):
            location = ", ".join(location)

        posted_raw = job.get("created_at", "") or job.get("posted_date", "")
        slug = job.get("slug", "") or job.get("job_slug", "")

        if slug:
            url = f"https://www.instahyre.com/job/{slug}/"
        elif job_id:
            url = f"https://www.instahyre.com/job/{job_id}/"
        else:
            return {}

        description = job.get("description", "") or job.get("job_description", "")
        if description:
            description = re.sub(r"<[^>]+>", " ", description)
            description = re.sub(r"\s+", " ", description).strip()

        skills = job.get("skills", [])
        if isinstance(skills, list) and skills:
            description += " Skills: " + ", ".join(
                s.get("name", s) if isinstance(s, dict) else str(s)
                for s in skills
            )

        return {
            "job_id": f"instahyre_{job_id}",
            "title": title,
            "company": company or "Unknown",
            "location": location,
            "url": url,
            "apply_url": url,
            "source": self.SOURCE_NAME,
            "posted_date_raw": posted_raw,
            "description": description,
        }

    # ── HTML Scraping ─────────────────────────────────────────────────────────

    def _scrape_via_html(self) -> List[Dict]:
        """Scrape Instahyre HTML search pages."""
        raw_jobs = []

        search_urls = [
            "https://www.instahyre.com/search-jobs/?q=ui+ux+designer&location=Hyderabad",
            "https://www.instahyre.com/search-jobs/?q=ux+designer&location=Hyderabad",
            "https://www.instahyre.com/search-jobs/?q=product+designer&location=Hyderabad",
            "https://www.instahyre.com/search-jobs/?q=ui+ux+designer&location=Bangalore",
        ]

        for url in search_urls:
            jobs = self._scrape_html_page(url)
            raw_jobs.extend(jobs)
            logger.debug(f"Instahyre HTML {url}: {len(jobs)} jobs")

        return raw_jobs

    def _scrape_html_page(self, url: str) -> List[Dict]:
        """Scrape a single Instahyre search page."""
        headers = self._get_headers({
            "Referer": "https://www.instahyre.com/",
        })

        resp = self._get(url, headers=headers)
        if not resp:
            return []

        try:
            soup = BeautifulSoup(resp.text, "html.parser")
            jobs = []

            # Try JSON-LD
            for script in soup.find_all("script", type="application/ld+json"):
                try:
                    data = json.loads(script.string or "")
                    if data.get("@type") == "JobPosting":
                        job = self._parse_json_ld(data)
                        if job:
                            jobs.append(job)
                except (json.JSONDecodeError, AttributeError):
                    pass

            if jobs:
                return jobs

            # HTML cards
            job_cards = soup.find_all(
                "div",
                class_=re.compile(r"job-card|jobCard|job-listing|opportunity")
            )
            for card in job_cards:
                job = self._parse_html_card(card)
                if job:
                    jobs.append(job)

            return jobs
        except Exception as e:
            logger.error(f"Instahyre HTML parse error for {url}: {e}")
            return []

    def _parse_json_ld(self, data: Dict) -> Optional[Dict]:
        """Parse a JobPosting from JSON-LD."""
        try:
            title = data.get("title", "")
            company = data.get("hiringOrganization", {}).get("name", "")
            location_data = data.get("jobLocation", {})
            if isinstance(location_data, list):
                location_data = location_data[0] if location_data else {}
            location = (
                location_data.get("address", {}).get("addressLocality", "India")
                if isinstance(location_data, dict)
                else "India"
            )
            url = data.get("url", "")
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
            logger.debug(f"Instahyre JSON-LD parse error: {e}")
            return None

    def _parse_html_card(self, card) -> Optional[Dict]:
        """Parse a single Instahyre HTML job card."""
        try:
            title_el = (
                card.find(class_=re.compile(r"title|designation|role"))
                or card.find("h2")
                or card.find("h3")
            )
            if not title_el:
                return None
            title = title_el.get_text(strip=True)

            link_el = card.find("a", href=True)
            if not link_el:
                return None
            href = link_el.get("href", "")
            if not href.startswith("http"):
                href = self.BASE_URL + href

            company_el = card.find(class_=re.compile(r"company|employer|org"))
            company = company_el.get_text(strip=True) if company_el else "Unknown"

            loc_el = card.find(class_=re.compile(r"location|city"))
            location = loc_el.get_text(strip=True) if loc_el else "India"

            date_el = card.find(class_=re.compile(r"date|posted|time"))
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
            logger.debug(f"Instahyre card parse error: {e}")
            return None
