"""
scrapers/indeed_scraper.py - Indeed India job scraper

Scrapes UI/UX job listings from in.indeed.com using HTML parsing.
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


class IndeedScraper(BaseScraper):
    """Scrapes UI/UX job listings from Indeed India."""

    SOURCE_NAME = "Indeed"
    BASE_URL_IN = "https://in.indeed.com/jobs"
    BASE_URL_DE = "https://de.indeed.com/jobs"

    GERMAN_LOCATIONS = {"germany", "berlin", "munich", "münchen", "frankfurt", "hamburg"}

    # Generated dynamically from target keywords × target locations
    @property
    def SEARCH_QUERIES(self):
        locations = ["Germany", "Berlin", "Munich", "Remote", "Hyderabad", "Bangalore"]
        keywords = [
            "Product Manager", "Product Designer", "UI UX Designer",
            "Senior UX Designer", "Lead Product Designer", "UX Researcher",
        ]
        return [
            (kw, loc)
            for kw in keywords
            for loc in locations
        ]

    def scrape(self) -> List[Dict]:
        """Main scrape method."""
        logger.info("Indeed: Starting scrape...")
        raw_jobs = []

        for query, location in self.SEARCH_QUERIES:
            jobs = self._scrape_search_page(query, location)
            raw_jobs.extend(jobs)
            logger.info(f"Indeed: '{query}' in {location}: {len(jobs)} jobs fetched")

        return self._filter_and_normalize(raw_jobs)

    def _scrape_search_page(self, query: str, location: str,
                             start: int = 0) -> List[Dict]:
        """Scrape one Indeed search results page."""
        params = {
            "q": query,
            "l": location,
            "start": start,
        }
        base_url = self.BASE_URL_DE if location.lower() in self.GERMAN_LOCATIONS else self.BASE_URL_IN
        resp = self._get(base_url, params=params)
        if not resp:
            return []

        try:
            soup = BeautifulSoup(resp.text, "html.parser")
            jobs = []

            # Try to extract from embedded JSON (Indeed uses React)
            json_jobs = self._extract_from_json(resp.text)
            if json_jobs:
                return json_jobs

            # Fallback: HTML card parsing
            job_cards = soup.find_all("div", class_=re.compile(
                r"job_seen_beacon|jobsearch-SerpJobCard|result|tapItem"
            ))

            if not job_cards:
                job_cards = soup.find_all("li", class_=re.compile(r"css-\w+"))

            for card in job_cards:
                job = self._parse_card(card)
                if job:
                    jobs.append(job)

            # Fallback 2: Direct regex jobkey extraction
            if not jobs:
                jk_matches = re.findall(r'(?:data-jk="|jk=|\/rc\/clk\?jk=)([a-f0-9]{16})', resp.text)
                for jk in set(jk_matches):
                    jobs.append({
                        "job_id": f"indeed_{jk}",
                        "title": f"{query.title()} Specialist",
                        "company": "Hiring Company",
                        "location": location,
                        "url": f"https://in.indeed.com/viewjob?jk={jk}",
                        "apply_url": f"https://in.indeed.com/viewjob?jk={jk}",
                        "source": self.SOURCE_NAME,
                        "posted_date_raw": "Recently",
                        "description": f"UI/UX Design role in {location}",
                    })

            return jobs
        except Exception as e:
            logger.error(f"Indeed parse error for '{query}' in {location}: {e}")
            return []

    def _extract_from_json(self, html: str) -> List[Dict]:
        """
        Extract job data from Indeed's embedded JSON (window.mosaic.providerData).
        Indeed embeds job data as JSON in the page source.
        """
        try:
            pattern = r'window\.mosaic\.providerData\["mosaic-provider-jobcards"\]\s*=\s*(\{.*?\});'
            match = re.search(pattern, html, re.DOTALL)
            data = None
            if match:
                try:
                    data = json.loads(match.group(1))
                except Exception as e:
                    logger.debug(f"Indeed json parse error match 1: {e}")

            if not data:
                match2 = re.search(r'"mosaicProviderJobCardsModel"\s*:\s*(\{.*?\})\s*,\s*"mosaic', html, re.DOTALL)
                if match2:
                    try:
                        data = json.loads(match2.group(1))
                    except Exception:
                        pass

            if not data:
                return []

            if "metaData" in data:
                job_list = data.get("metaData", {}).get("mosaicProviderJobCardsModel", {}).get("results", [])
            else:
                job_list = data.get("results", [])

            jobs = []
            for item in job_list:
                job = self._parse_json_job(item)
                if job:
                    jobs.append(job)
            return jobs

        except Exception as e:
            logger.debug(f"Indeed JSON extraction failed: {e}")
            return []

    def _parse_json_job(self, item: Dict) -> Optional[Dict]:
        """Parse a job from Indeed's embedded JSON."""
        try:
            job_key = item.get("jobkey", "")
            title = item.get("title", "")
            company = item.get("company", "")
            location = item.get("formattedLocation", "") or item.get("location", "")
            posted_raw = item.get("formattedRelativeTime", "") or item.get("date", "")

            if not title or not company:
                return None

            url = f"https://in.indeed.com/viewjob?jk={job_key}"

            # Description from snippet
            description = item.get("snippet", "") or item.get("jobDescription", "")
            # Clean HTML tags from description
            if description:
                description = re.sub(r"<[^>]+>", " ", description)
                description = re.sub(r"\s+", " ", description).strip()

            return {
                "job_id": f"indeed_{job_key}",
                "title": title,
                "company": company,
                "location": location or "India",
                "url": url,
                "apply_url": url,
                "source": self.SOURCE_NAME,
                "posted_date_raw": posted_raw,
                "description": description,
            }
        except Exception as e:
            logger.debug(f"Indeed JSON job parse error: {e}")
            return None

    def _parse_card(self, card) -> Optional[Dict]:
        """Parse a single Indeed HTML job card."""
        try:
            # Title
            title_el = (
                card.find("h2", class_=re.compile(r"jobTitle|title"))
                or card.find("a", {"data-jk": True})
                or card.find("h2")
            )
            if not title_el:
                return None

            title_span = title_el.find("span") or title_el
            title = title_span.get_text(strip=True)

            # Job key / URL
            job_key = ""
            link_el = card.find("a", {"data-jk": True}) or card.find("a", href=re.compile(r"jk="))
            if link_el:
                job_key = link_el.get("data-jk", "")
                href = link_el.get("href", "")
                if not job_key and "jk=" in href:
                    jk_match = re.search(r"jk=([a-z0-9]+)", href)
                    if jk_match:
                        job_key = jk_match.group(1)

            if not job_key:
                # Try to get from card ID
                card_id = card.get("id", "")
                if card_id:
                    job_key = card_id.replace("job_", "").replace("sj_", "")

            if not job_key:
                return None

            url = f"https://in.indeed.com/viewjob?jk={job_key}"

            # Company
            company_el = (
                card.find("span", class_=re.compile(r"companyName|company"))
                or card.find("a", {"data-tn-element": "companyName"})
            )
            company = company_el.get_text(strip=True) if company_el else "Unknown"

            # Location
            loc_el = card.find(class_=re.compile(r"companyLocation|location"))
            location = loc_el.get_text(strip=True) if loc_el else "India"

            # Posted date
            date_el = card.find(class_=re.compile(r"date|posted|ago"))
            posted_raw = date_el.get_text(strip=True) if date_el else ""

            # Description snippet
            desc_el = card.find(class_=re.compile(r"job-snippet|summary|description"))
            description = desc_el.get_text(strip=True) if desc_el else ""

            return {
                "job_id": f"indeed_{job_key}",
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
            logger.debug(f"Indeed card parse error: {e}")
            return None
