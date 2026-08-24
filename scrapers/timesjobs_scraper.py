"""
scrapers/timesjobs_scraper.py - TimesJobs job scraper

Scrapes UI/UX design job listings from timesjobs.com.
TimesJobs is one of India's largest job portals (Times of India group).
Uses HTML parsing with JSON-LD and structured data extraction.
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


class TimesJobsScraper(BaseScraper):
    """Scrapes UI/UX job listings from TimesJobs.com."""

    SOURCE_NAME = "TimesJobs"
    BASE_URL = "https://www.timesjobs.com/candidate/job-search.html"

    @property
    def SEARCH_QUERIES(self):
        """Generate (keyword, location) pairs from config."""
        locations = ["Hyderabad", "Bangalore", "Remote"]
        return [
            (kw, loc)
            for kw in config.ALL_SEARCH_KEYWORDS
            for loc in locations
        ]

    def scrape(self) -> List[Dict]:
        """Main scrape method."""
        logger.info("TimesJobs: Starting scrape...")
        raw_jobs = []

        for keyword, location in self.SEARCH_QUERIES:
            jobs = self._scrape_search_page(keyword, location)
            raw_jobs.extend(jobs)
            logger.debug(f"TimesJobs: '{keyword}' in {location}: {len(jobs)} jobs")
            if len(raw_jobs) >= 150:
                break

        return self._filter_and_normalize(raw_jobs)

    def _scrape_search_page(self, keyword: str, location: str) -> List[Dict]:
        """Scrape one TimesJobs search results page."""
        params = {
            "searchType": "personalizedSearch",
            "from": "submit",
            "txtKeywords": keyword,
            "txtLocation": location,
            "sequence": "1",
            "startPage": "1",
        }

        headers = self._get_headers({
            "Referer": "https://www.timesjobs.com/",
            "Accept-Language": "en-IN,en;q=0.9",
        })

        resp = self._get(self.BASE_URL, params=params, headers=headers)
        if not resp:
            return []

        try:
            soup = BeautifulSoup(resp.text, "html.parser")
            jobs = []

            # Strategy 1: JSON-LD structured data
            for script in soup.find_all("script", type="application/ld+json"):
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

            # Strategy 2: TimesJobs-specific HTML structure
            # TimesJobs uses <li class="clearfix job-bx wht-shd-bx"> for job cards
            job_cards = soup.find_all("li", class_=re.compile(r"job-bx|clearfix"))
            if not job_cards:
                job_cards = soup.find_all(
                    "div",
                    class_=re.compile(r"job-bx|jobCard|job-listing|srp-job")
                )

            for card in job_cards:
                job = self._parse_html_card(card)
                if job:
                    jobs.append(job)

            return jobs
        except Exception as e:
            logger.error(f"TimesJobs parse error for '{keyword}' in {location}: {e}")
            return []

    def _parse_json_ld(self, data: Dict) -> Optional[Dict]:
        """Parse a JobPosting from JSON-LD structured data."""
        try:
            title = data.get("title", "")
            if not title:
                return None

            company = data.get("hiringOrganization", {})
            if isinstance(company, dict):
                company = company.get("name", "Unknown")
            else:
                company = str(company) or "Unknown"

            location_data = data.get("jobLocation", {})
            if isinstance(location_data, list):
                location_data = location_data[0] if location_data else {}
            if isinstance(location_data, dict):
                addr = location_data.get("address", {})
                location = (
                    addr.get("addressLocality", "India")
                    if isinstance(addr, dict) else "India"
                )
            else:
                location = "India"

            url = data.get("url", "")
            if not url or not url.startswith("http"):
                return None

            posted_raw = data.get("datePosted", "")
            description = data.get("description", "")
            if description:
                description = re.sub(r"<[^>]+>", " ", description)
                description = re.sub(r"\s+", " ", description).strip()[:2000]

            id_match = re.search(r"[?&](?:jobId|job_id|jId)=(\d+)", url)
            job_id = f"timesjobs_{id_match.group(1)}" if id_match else ""

            return {
                "job_id": job_id,
                "title": title,
                "company": company,
                "location": location,
                "url": url,
                "apply_url": url,
                "source": self.SOURCE_NAME,
                "posted_date_raw": posted_raw,
                "description": description,
            }
        except Exception as e:
            logger.debug(f"TimesJobs JSON-LD parse error: {e}")
            return None

    def _parse_html_card(self, card) -> Optional[Dict]:
        """Parse a single TimesJobs HTML job card."""
        try:
            # TimesJobs title is usually in <h2> with a link
            title_el = (
                card.find("h2")
                or card.find(class_=re.compile(r"job-title|jobTitle|title|heading"))
            )
            if not title_el:
                return None

            link_el = title_el.find("a") if title_el else None
            if not link_el:
                link_el = card.find("a", href=re.compile(r"timesjobs\.com"))
            if not link_el:
                link_el = card.find("a", href=True)
            if not link_el:
                return None

            title = link_el.get_text(strip=True) or title_el.get_text(strip=True)
            if not title:
                return None

            href = link_el.get("href", "")
            if not href.startswith("http"):
                href = "https://www.timesjobs.com" + href
            if not href.startswith("http"):
                return None

            # Company name — TimesJobs uses <h3 class="joblist-comp-name">
            company_el = (
                card.find("h3", class_=re.compile(r"comp-name|company"))
                or card.find(class_=re.compile(r"comp-name|company|employer"))
            )
            company = company_el.get_text(strip=True) if company_el else "Unknown"
            # Clean up "More jobs by this company" text
            company = re.sub(r"\s*More jobs.*$", "", company, flags=re.IGNORECASE).strip()

            # Location
            loc_el = card.find(class_=re.compile(r"location|loc|city"))
            if not loc_el:
                # TimesJobs sometimes puts location in <ul class="top-jd-dtl">
                ul = card.find("ul", class_=re.compile(r"top-jd|jd-dtl"))
                if ul:
                    loc_el = ul.find("li")
            location = loc_el.get_text(strip=True) if loc_el else "India"

            # Posted date
            date_el = (
                card.find(class_=re.compile(r"sim-posted|posted|date|ago"))
                or card.find("span", string=re.compile(r"day|week|month|ago", re.I))
            )
            posted_raw = date_el.get_text(strip=True) if date_el else ""

            # Description / skills
            desc_el = card.find(class_=re.compile(r"list-job-dtl|description|skill|snippet"))
            description = desc_el.get_text(strip=True) if desc_el else ""

            # Extract job ID from URL
            id_match = re.search(r"[?&](?:jobId|job_id|jId)=(\d+)", href)
            job_id = f"timesjobs_{id_match.group(1)}" if id_match else ""

            return {
                "job_id": job_id,
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
            logger.debug(f"TimesJobs card parse error: {e}")
            return None
