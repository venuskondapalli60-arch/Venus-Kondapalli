"""
scrapers/arbeitsagentur_scraper.py - Scraper for Jobbörse der Bundesagentur für Arbeit
Official German Federal Employment Agency job search engine.
"""

import re
import logging
from typing import List, Dict, Optional
from bs4 import BeautifulSoup

import config
from scrapers.base_scraper import BaseScraper

logger = logging.getLogger(__name__)


class ArbeitsagenturScraper(BaseScraper):
    """Scrapes official German listings from Jobbörse der Bundesagentur für Arbeit."""

    SOURCE_NAME = "Bundesagentur für Arbeit"
    SEARCH_URL = "https://www.arbeitsagentur.de/jobsuche/suche"

    TARGET_ROLES = [
        "Product Manager",
        "Product Designer",
        "UI UX Designer",
        "UX Designer",
        "Lead Designer",
        "ServiceNow",
    ]

    TARGET_LOCATIONS = [
        "Berlin",
        "München",
        "Frankfurt am Main",
        "Hamburg",
        "Deutschland",
    ]

    def scrape(self) -> List[Dict]:
        """Main scrape method."""
        logger.info("Bundesagentur für Arbeit: Starting scrape...")
        raw_jobs = []

        headers = self._get_headers({
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7",
            "Referer": "https://www.arbeitsagentur.de/jobsuche/",
        })

        for role in self.TARGET_ROLES:
            for location in self.TARGET_LOCATIONS:
                params = {
                    "angebotsart": "1",  # 1 = Arbeit (regular employment)
                    "was": role,
                    "wo": location,
                }
                resp = self._get(self.SEARCH_URL, params=params, headers=headers)
                if not resp:
                    continue

                try:
                    soup = BeautifulSoup(resp.text, "html.parser")
                    page_jobs = self._parse_results(soup, role, location)
                    raw_jobs.extend(page_jobs)
                    logger.debug(
                        f"Arbeitsagentur: '{role}' in {location}: {len(page_jobs)} jobs"
                    )
                except Exception as e:
                    logger.error(f"Arbeitsagentur parse error for '{role}' in {location}: {e}")

        logger.info(f"Bundesagentur für Arbeit: Scraped {len(raw_jobs)} raw jobs")
        return self._filter_and_normalize(raw_jobs)

    def _parse_results(self, soup: BeautifulSoup, query_role: str, query_loc: str) -> List[Dict]:
        """Parse job detail links and surrounding metadata from search page."""
        jobs = []

        # Arbeitsagentur uses links matching /jobsuche/jobdetail/
        detail_links = soup.find_all("a", href=re.compile(r"/jobsuche/jobdetail/"))
        seen_urls = set()

        for a in detail_links:
            href = a.get("href", "")
            if not href or href in seen_urls:
                continue
            seen_urls.add(href)

            url = href if href.startswith("http") else f"https://www.arbeitsagentur.de{href}"

            raw_text = a.get_text(strip=True)
            # Remove leading numeric numbering like "1: Product Manager..."
            clean_title = re.sub(r"^\d+\s*:\s*", "", raw_text)

            # Look for company in "bei <Company>"
            company = "Arbeitsagentur Listing"
            if " bei " in clean_title:
                parts = clean_title.split(" bei ", 1)
                title = parts[0].strip()
                company = parts[1].strip()
            else:
                title = clean_title

            # Look at parent container for location & description context
            parent = a.find_parent(["li", "div", "article"])
            context_text = parent.get_text(" ", strip=True) if parent else ""

            location = query_loc
            loc_match = re.search(r"Arbeitsort:\s*([^,\n\r\t]+)", context_text)
            if loc_match:
                parsed_loc = loc_match.group(1).strip()
                # Clean up distance notes and German metadata tags
                parsed_loc = re.sub(r"\(\d+\s*km\)", "", parsed_loc)
                parsed_loc = re.split(r"Anstellungsart|Befristung|Kennzeichnungen", parsed_loc, flags=re.IGNORECASE)[0].strip()
                if parsed_loc:
                    location = f"{parsed_loc}, Germany"

            # Clean job ID from url or hash
            id_match = re.search(r"/jobdetail/([^/?#]+)", url)
            job_id = f"ba_{id_match.group(1)}" if id_match else self._generate_job_id(title, company, url)

            jobs.append({
                "job_id": job_id,
                "title": title,
                "company": company,
                "location": location,
                "url": url,
                "apply_url": url,
                "source": self.SOURCE_NAME,
                "posted_date_raw": "Today",
                "description": f"{title} at {company}. {context_text[:500]}",
            })

        return jobs
