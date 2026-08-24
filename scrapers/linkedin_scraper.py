"""
scrapers/linkedin_scraper.py - LinkedIn Jobs scraper

Uses LinkedIn's public guest jobs API (no login required) to fetch
UI/UX job listings. Scrapes the public search results page as fallback.
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


class LinkedInScraper(BaseScraper):
    """Scrapes UI/UX job listings from LinkedIn Jobs (public, no login)."""

    SOURCE_NAME = "LinkedIn"

    # LinkedIn guest jobs API (public, no auth required)
    GUEST_API = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"

    # Public search page
    SEARCH_URL = "https://www.linkedin.com/jobs/search/"

    # GeoIDs for Indian cities
    GEO_IDS = {
        "Hyderabad": "105556991",
        "Bangalore": "105214831",
        "India": "102713980",
        "Remote": "",
    }

    def scrape(self) -> List[Dict]:
        """Main scrape method."""
        logger.info("LinkedIn: Starting scrape...")
        raw_jobs = []

        keywords = config.ALL_SEARCH_KEYWORDS

        for keyword in keywords:
            for location, geo_id in self.GEO_IDS.items():
                jobs = self._fetch_jobs(keyword, location, geo_id)
                raw_jobs.extend(jobs)
                logger.debug(f"LinkedIn: '{keyword}' in {location}: {len(jobs)} jobs")

        return self._filter_and_normalize(raw_jobs)

    # ── Guest API ─────────────────────────────────────────────────────────────

    def _fetch_jobs(self, keyword: str, location: str,
                    geo_id: str, start: int = 0) -> List[Dict]:
        """Fetch jobs from LinkedIn guest API."""
        params = {
            "keywords": keyword,
            "location": location,
            "geoId": geo_id,
            "f_TPR": "r604800",   # Last 7 days
            "f_JT": "F,C,P",      # Full-time, Contract, Part-time
            "sortBy": "DD",        # Sort by date
            "start": start,
            "count": 25,
        }

        headers = self._get_headers({
            "Referer": "https://www.linkedin.com/jobs/search/",
            "X-Requested-With": "XMLHttpRequest",
        })

        resp = self._get(self.GUEST_API, params=params, headers=headers)
        if not resp:
            # Try public search page as fallback
            return self._scrape_public_page(keyword, location, geo_id)

        try:
            soup = BeautifulSoup(resp.text, "html.parser")
            job_cards = soup.find_all("div", class_=re.compile(r"base-card|job-search-card"))
            jobs = []
            for card in job_cards:
                job = self._parse_card(card)
                if job:
                    jobs.append(job)
            return jobs
        except Exception as e:
            logger.error(f"LinkedIn guest API parse error: {e}")
            return []

    def _scrape_public_page(self, keyword: str, location: str,
                             geo_id: str) -> List[Dict]:
        """Fallback: scrape LinkedIn public search results page."""
        params = {
            "keywords": keyword,
            "location": location,
            "geoId": geo_id,
            "f_TPR": "r604800",
            "sortBy": "DD",
        }

        headers = self._get_headers({
            "Referer": "https://www.linkedin.com/",
        })

        resp = self._get(self.SEARCH_URL, params=params, headers=headers)
        if not resp:
            return []

        try:
            soup = BeautifulSoup(resp.text, "html.parser")
            job_cards = soup.find_all(
                "div",
                class_=re.compile(r"base-card|job-search-card|jobs-search__results-list")
            )
            jobs = []
            for card in job_cards:
                job = self._parse_card(card)
                if job:
                    jobs.append(job)
            return jobs
        except Exception as e:
            logger.error(f"LinkedIn public page parse error: {e}")
            return []

    # ── Card Parser ───────────────────────────────────────────────────────────

    def _parse_card(self, card) -> Optional[Dict]:
        """Parse a single LinkedIn job card."""
        try:
            # Job title and URL
            title_el = (
                card.find("h3", class_=re.compile(r"base-search-card__title|job-title"))
                or card.find("a", class_=re.compile(r"base-card__full-link|job-title"))
                or card.find("h3")
            )
            if not title_el:
                return None

            title = title_el.get_text(strip=True)

            # URL from anchor tag
            link_el = (
                card.find("a", class_=re.compile(r"base-card__full-link"))
                or card.find("a", href=re.compile(r"linkedin\.com/jobs/view"))
                or title_el if title_el.name == "a" else None
            )

            if link_el:
                job_url = link_el.get("href", "")
            else:
                # Try data attributes
                job_url = card.get("data-entity-urn", "")
                if job_url:
                    # Extract job ID from URN
                    job_id_match = re.search(r":(\d+)$", job_url)
                    if job_id_match:
                        jid = job_id_match.group(1)
                        job_url = f"https://www.linkedin.com/jobs/view/{jid}/"

            if not job_url or not job_url.startswith("http"):
                return None

            # Clean URL (remove tracking params)
            job_url = re.sub(r"\?.*$", "", job_url)
            if not job_url.endswith("/"):
                job_url += "/"

            # Company
            company_el = (
                card.find("h4", class_=re.compile(r"base-search-card__subtitle|company"))
                or card.find("a", class_=re.compile(r"hidden-nested-link"))
                or card.find("h4")
            )
            company = company_el.get_text(strip=True) if company_el else "Unknown"

            # Location
            loc_el = (
                card.find("span", class_=re.compile(r"job-search-card__location|location"))
                or card.find("span", class_=re.compile(r"base-search-card__metadata"))
            )
            location = loc_el.get_text(strip=True) if loc_el else "India"

            # Posted date
            date_el = (
                card.find("time")
                or card.find("span", class_=re.compile(r"date|posted|listdate"))
            )
            if date_el:
                posted_raw = date_el.get("datetime", "") or date_el.get_text(strip=True)
            else:
                posted_raw = ""

            # Extract job ID from URL
            job_id_match = re.search(r"/jobs/view/(\d+)", job_url)
            job_id = f"linkedin_{job_id_match.group(1)}" if job_id_match else ""

            # Description snippet
            desc_el = card.find(class_=re.compile(r"job-result-card__snippet|description"))
            description = desc_el.get_text(strip=True) if desc_el else ""

            return {
                "job_id": job_id,
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
            logger.debug(f"LinkedIn card parse error: {e}")
            return None
