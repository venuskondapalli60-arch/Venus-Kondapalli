"""
scrapers/glassdoor_scraper.py - Glassdoor job scraper

Scrapes UI/UX design job listings from glassdoor.co.in.
Uses HTML parsing with JSON-LD extraction.
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


class GlassdoorScraper(BaseScraper):
    """Scrapes UI/UX job listings from Glassdoor India."""

    SOURCE_NAME = "Glassdoor"
    BASE_URL = "https://www.glassdoor.co.in/Job/jobs.htm"

    @property
    def SEARCH_QUERIES(self):
        locations = ["Hyderabad, Telangana, India", "Bangalore, Karnataka, India", "India"]
        return [
            (kw, loc)
            for kw in config.ALL_SEARCH_KEYWORDS
            for loc in locations
        ]

    # Glassdoor location IDs
    LOCATION_IDS = {
        "Hyderabad, Telangana, India": "2940586",
        "Bangalore, Karnataka, India": "2211",
        "India": "115",
    }

    def scrape(self) -> List[Dict]:
        """Main scrape method."""
        logger.info("Glassdoor: Starting scrape...")
        raw_jobs = []

        for query, location in self.SEARCH_QUERIES:
            jobs = self._scrape_search_page(query, location)
            raw_jobs.extend(jobs)
            logger.debug(f"Glassdoor: '{query}' in {location}: {len(jobs)} jobs")

        return self._filter_and_normalize(raw_jobs)

    def _scrape_search_page(self, query: str, location: str) -> List[Dict]:
        """Scrape one Glassdoor search results page."""
        loc_id = self.LOCATION_IDS.get(location, "115")

        params = {
            "sc.keyword": query,
            "locT": "C",
            "locId": loc_id,
            "jobType": "",
            "fromAge": "7",
            "minSalary": "0",
            "includeNoSalaryJobs": "true",
            "radius": "25",
            "cityId": loc_id,
            "minRating": "0.0",
            "industryId": "",
            "sgocId": "",
            "seniorityType": "",
            "companyId": "",
            "employerSizes": "0",
            "applicationType": "0",
            "remoteWorkType": "0",
        }

        headers = self._get_headers({
            "Referer": "https://www.glassdoor.co.in/",
            "Accept-Language": "en-IN,en;q=0.9",
        })

        resp = self._get(self.BASE_URL, params=params, headers=headers)
        if not resp:
            return []

        try:
            soup = BeautifulSoup(resp.text, "html.parser")
            jobs = []

            # Try JSON-LD structured data
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
                            if item.get("@type") == "JobPosting":
                                job = self._parse_json_ld(item)
                                if job:
                                    jobs.append(job)
                except (json.JSONDecodeError, AttributeError):
                    pass

            if jobs:
                return jobs

            # Try embedded Apollo/React state
            apollo_jobs = self._extract_apollo_state(resp.text)
            if apollo_jobs:
                return apollo_jobs

            # HTML card fallback
            job_cards = soup.find_all(
                "li",
                class_=re.compile(r"react-job-listing|JobsList_jobListItem|jl")
            )
            if not job_cards:
                job_cards = soup.find_all(
                    "div",
                    class_=re.compile(r"jobCard|job-listing|JobCard")
                )

            for card in job_cards:
                job = self._parse_html_card(card)
                if job:
                    jobs.append(job)

            return jobs
        except Exception as e:
            logger.error(f"Glassdoor parse error for '{query}': {e}")
            return []

    def _extract_apollo_state(self, html: str) -> List[Dict]:
        """Extract jobs from Glassdoor's Apollo GraphQL state."""
        try:
            # Look for Apollo state
            pattern = r'window\.__APOLLO_STATE__\s*=\s*(\{.*?\});'
            match = re.search(pattern, html, re.DOTALL)
            if not match:
                return []

            data = json.loads(match.group(1))
            jobs = []

            for key, value in data.items():
                if isinstance(value, dict) and value.get("__typename") == "JobListing":
                    job = self._parse_apollo_job(value)
                    if job:
                        jobs.append(job)

            return jobs
        except (json.JSONDecodeError, AttributeError) as e:
            logger.debug(f"Glassdoor Apollo state parse error: {e}")
            return []

    def _parse_apollo_job(self, item: Dict) -> Optional[Dict]:
        """Parse a job from Apollo state."""
        try:
            job_id = str(item.get("jobListingId", "") or item.get("listingId", ""))
            title = item.get("jobTitleText", "") or item.get("title", "")
            company = item.get("employerName", "") or item.get("company", "")
            location = item.get("locationName", "") or item.get("location", "India")
            posted_raw = item.get("listingDateText", "") or item.get("postedDate", "")

            if not title or not job_id:
                return None

            url = f"https://www.glassdoor.co.in/job-listing/j?jl={job_id}"

            description = item.get("jobDescriptionText", "") or ""
            if description:
                description = re.sub(r"<[^>]+>", " ", description)
                description = re.sub(r"\s+", " ", description).strip()[:2000]

            return {
                "job_id": f"glassdoor_{job_id}",
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
            logger.debug(f"Glassdoor Apollo job parse error: {e}")
            return None

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

            # Extract job ID from URL
            jl_match = re.search(r"jl=(\d+)", url)
            job_id = f"glassdoor_{jl_match.group(1)}" if jl_match else ""

            return {
                "job_id": job_id,
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
            logger.debug(f"Glassdoor JSON-LD parse error: {e}")
            return None

    def _parse_html_card(self, card) -> Optional[Dict]:
        """Parse a single Glassdoor HTML job card."""
        try:
            title_el = (
                card.find(class_=re.compile(r"job-title|jobTitle|JobCard_jobTitle"))
                or card.find("a", {"data-test": "job-title"})
                or card.find("h3")
                or card.find("h2")
            )
            if not title_el:
                return None
            title = title_el.get_text(strip=True)

            link_el = (
                card.find("a", {"data-test": "job-title"})
                or card.find("a", href=re.compile(r"glassdoor|job-listing"))
                or title_el if title_el and title_el.name == "a" else None
            )
            if not link_el:
                link_el = card.find("a", href=True)
            if not link_el:
                return None

            href = link_el.get("href", "")
            if not href.startswith("http"):
                href = "https://www.glassdoor.co.in" + href

            company_el = (
                card.find(class_=re.compile(r"employer-name|companyName|JobCard_companyName"))
                or card.find("div", {"data-test": "employer-name"})
            )
            company = company_el.get_text(strip=True) if company_el else "Unknown"

            loc_el = (
                card.find(class_=re.compile(r"location|JobCard_location"))
                or card.find("div", {"data-test": "emp-location"})
            )
            location = loc_el.get_text(strip=True) if loc_el else "India"

            date_el = card.find(class_=re.compile(r"date|posted|listing-age"))
            posted_raw = date_el.get_text(strip=True) if date_el else ""

            # Extract job ID from href
            jl_match = re.search(r"jl=(\d+)", href)
            job_id = f"glassdoor_{jl_match.group(1)}" if jl_match else ""

            return {
                "job_id": job_id,
                "title": title,
                "company": company,
                "location": location,
                "url": href,
                "apply_url": href,
                "source": self.SOURCE_NAME,
                "posted_date_raw": posted_raw,
                "description": "",
            }
        except Exception as e:
            logger.debug(f"Glassdoor card parse error: {e}")
            return None
