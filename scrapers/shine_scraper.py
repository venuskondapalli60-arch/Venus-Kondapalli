"""
scrapers/shine_scraper.py - Shine.com job scraper

Scrapes UI/UX design job listings from shine.com.
Shine is one of India's major job portals with strong design role coverage.
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


class ShineScraper(BaseScraper):
    """Scrapes UI/UX job listings from Shine.com."""

    SOURCE_NAME = "Shine"
    BASE_URL = "https://www.shine.com/job-search/"

    @property
    def SEARCH_QUERIES(self):
        """Generate search URL slugs from config keywords × locations."""
        locations = ["hyderabad", "bangalore", "remote"]
        queries = []
        for kw in config.ALL_SEARCH_KEYWORDS:
            slug = kw.lower().replace(" ", "-").replace("/", "-")
            for loc in locations:
                queries.append((slug, loc))
        return queries

    def scrape(self) -> List[Dict]:
        """Main scrape method."""
        logger.info("Shine: Starting scrape...")
        raw_jobs = []

        for kw_slug, location in self.SEARCH_QUERIES:
            jobs = self._scrape_search_page(kw_slug, location)
            raw_jobs.extend(jobs)
            logger.debug(f"Shine: '{kw_slug}' in {location}: {len(jobs)} jobs")
            if len(raw_jobs) >= 150:
                break

        return self._filter_and_normalize(raw_jobs)

    def _scrape_search_page(self, kw_slug: str, location: str) -> List[Dict]:
        """Scrape one Shine search results page."""
        url = f"{self.BASE_URL}{kw_slug}-jobs-in-{location}/"
        headers = self._get_headers({"Referer": "https://www.shine.com/"})

        resp = self._get(url, headers=headers)
        if not resp:
            # Try alternate URL format
            url2 = f"https://www.shine.com/job-search/{kw_slug}-jobs/"
            resp = self._get(url2, headers=headers)
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
                    elif data.get("@type") == "ItemList":
                        for item in data.get("itemListElement", []):
                            if isinstance(item, dict) and item.get("@type") == "JobPosting":
                                job = self._parse_json_ld(item)
                                if job:
                                    jobs.append(job)
                except (json.JSONDecodeError, AttributeError):
                    pass

            if jobs:
                return jobs

            # Strategy 2: HTML card parsing
            job_cards = soup.find_all(
                "div",
                class_=re.compile(r"job-card|jobCard|job-listing|job_listing|srp-job")
            )
            if not job_cards:
                job_cards = soup.find_all("li", class_=re.compile(r"job|listing"))
            if not job_cards:
                job_cards = soup.find_all("article", class_=re.compile(r"job"))

            for card in job_cards:
                job = self._parse_html_card(card)
                if job:
                    jobs.append(job)

            return jobs
        except Exception as e:
            logger.error(f"Shine parse error for '{kw_slug}' in {location}: {e}")
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

            # Extract job ID from URL
            id_match = re.search(r"/(\d+)/?$", url)
            job_id = f"shine_{id_match.group(1)}" if id_match else ""

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
            logger.debug(f"Shine JSON-LD parse error: {e}")
            return None

    def _parse_html_card(self, card) -> Optional[Dict]:
        """Parse a single Shine HTML job card."""
        try:
            title_el = (
                card.find(class_=re.compile(r"job-title|jobTitle|title|designation"))
                or card.find("h2")
                or card.find("h3")
            )
            if not title_el:
                return None
            title = title_el.get_text(strip=True)
            if not title:
                return None

            link_el = (
                card.find("a", href=re.compile(r"shine\.com"))
                or title_el if title_el and title_el.name == "a" else None
                or card.find("a", href=True)
            )
            if not link_el:
                return None
            href = link_el.get("href", "")
            if not href.startswith("http"):
                href = "https://www.shine.com" + href
            if not href.startswith("http"):
                return None

            company_el = card.find(class_=re.compile(r"company|employer|org"))
            company = company_el.get_text(strip=True) if company_el else "Unknown"

            loc_el = card.find(class_=re.compile(r"location|city|loc"))
            location = loc_el.get_text(strip=True) if loc_el else "India"

            date_el = card.find(class_=re.compile(r"date|posted|ago|time"))
            posted_raw = date_el.get_text(strip=True) if date_el else ""

            desc_el = card.find(class_=re.compile(r"description|snippet|summary|skill"))
            description = desc_el.get_text(strip=True) if desc_el else ""

            id_match = re.search(r"/(\d+)/?$", href)
            job_id = f"shine_{id_match.group(1)}" if id_match else ""

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
            logger.debug(f"Shine card parse error: {e}")
            return None
