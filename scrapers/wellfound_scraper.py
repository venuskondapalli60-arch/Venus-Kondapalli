"""
scrapers/wellfound_scraper.py - Wellfound (AngelList Talent) job scraper

Scrapes UI/UX design job listings from wellfound.com.
Wellfound is startup-focused and has many product/UX design roles.
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


class WellfoundScraper(BaseScraper):
    """Scrapes UI/UX job listings from Wellfound.com."""

    SOURCE_NAME = "Wellfound"
    BASE_URL = "https://wellfound.com/jobs"
    API_URL = "https://wellfound.com/graphql"

    SEARCH_PARAMS = [
        {"role": "Designer", "location": "India"},
        {"role": "UX Designer", "location": "India"},
        {"role": "Product Designer", "location": "India"},
        {"role": "UI Designer", "location": "India"},
    ]

    def scrape(self) -> List[Dict]:
        """Main scrape method."""
        logger.info("Wellfound: Starting scrape...")
        raw_jobs = []

        # Try HTML scraping (Wellfound is mostly client-side rendered)
        html_jobs = self._scrape_via_html()
        raw_jobs.extend(html_jobs)

        return self._filter_and_normalize(raw_jobs)

    def _scrape_via_html(self) -> List[Dict]:
        """Scrape Wellfound job search pages."""
        raw_jobs = []

        # Build URLs from config keywords (role-based + skill-based)
        base = "https://wellfound.com/jobs"
        search_urls = []
        for kw in config.ALL_SEARCH_KEYWORDS:
            slug = kw.lower().replace(" ", "-").replace("/", "-")
            search_urls.append(f"{base}?role={slug}&location=india")
        # Add location-specific queries for top roles
        for role in ["product-manager", "designer", "ux-designer", "product-designer", "lead-designer"]:
            for loc in ["germany", "berlin", "remote", "hyderabad", "bangalore"]:
                search_urls.append(f"{base}?role={role}&location={loc}")

        for url in search_urls:
            jobs = self._scrape_page(url)
            raw_jobs.extend(jobs)
            logger.debug(f"Wellfound {url}: {len(jobs)} jobs")

        return raw_jobs

    def _scrape_page(self, url: str) -> List[Dict]:
        """Scrape a single Wellfound search page."""
        headers = self._get_headers({
            "Referer": "https://wellfound.com/",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        })

        resp = self._get(url, headers=headers)
        if not resp:
            return []

        try:
            soup = BeautifulSoup(resp.text, "html.parser")
            jobs = []

            # Try JSON-LD structured data
            json_ld_scripts = soup.find_all("script", type="application/ld+json")
            for script in json_ld_scripts:
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

            # Try Next.js __NEXT_DATA__ JSON
            next_data_script = soup.find("script", id="__NEXT_DATA__")
            if next_data_script:
                next_jobs = self._parse_next_data(next_data_script.string or "")
                if next_jobs:
                    return next_jobs

            # HTML card fallback
            job_cards = soup.find_all(
                "div",
                class_=re.compile(r"job-listing|styles_component|JobListing|job-card")
            )
            if not job_cards:
                job_cards = soup.find_all("div", attrs={"data-test": re.compile(r"job")})

            for card in job_cards:
                job = self._parse_html_card(card)
                if job:
                    jobs.append(job)

            return jobs
        except Exception as e:
            logger.error(f"Wellfound page parse error for {url}: {e}")
            return []

    def _parse_next_data(self, json_str: str) -> List[Dict]:
        """Parse jobs from Next.js __NEXT_DATA__ JSON blob."""
        try:
            data = json.loads(json_str)
            # Navigate the Next.js data structure
            props = data.get("props", {}).get("pageProps", {})

            # Try different paths
            job_list = (
                props.get("jobs", [])
                or props.get("jobListings", [])
                or props.get("searchResults", {}).get("jobs", [])
            )

            jobs = []
            for item in job_list:
                job = self._parse_next_job(item)
                if job:
                    jobs.append(job)
            return jobs
        except (json.JSONDecodeError, KeyError, AttributeError) as e:
            logger.debug(f"Wellfound Next.js data parse error: {e}")
            return []

    def _parse_next_job(self, item: Dict) -> Optional[Dict]:
        """Parse a job from Next.js data."""
        try:
            title = item.get("title", "") or item.get("role", "")
            company_data = item.get("startup", {}) or item.get("company", {})
            company = (
                company_data.get("name", "")
                if isinstance(company_data, dict)
                else str(company_data)
            )
            location = item.get("locationNames", ["India"])[0] if item.get("locationNames") else "India"
            job_id = str(item.get("id", "") or item.get("jobId", ""))
            slug = item.get("slug", "") or item.get("jobSlug", "")
            company_slug = (
                company_data.get("slug", "")
                if isinstance(company_data, dict)
                else ""
            )

            if slug and company_slug:
                url = f"https://wellfound.com/jobs/{company_slug}/{slug}"
            elif job_id:
                url = f"https://wellfound.com/jobs/{job_id}"
            else:
                return None

            posted_raw = item.get("createdAt", "") or item.get("postedAt", "")
            description = item.get("description", "") or item.get("jobDescription", "")
            if description:
                description = re.sub(r"<[^>]+>", " ", description)
                description = re.sub(r"\s+", " ", description).strip()[:2000]

            return {
                "job_id": f"wellfound_{job_id}",
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
            logger.debug(f"Wellfound Next.js job parse error: {e}")
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
            logger.debug(f"Wellfound JSON-LD parse error: {e}")
            return None

    def _parse_html_card(self, card) -> Optional[Dict]:
        """Parse a single Wellfound HTML job card."""
        try:
            title_el = (
                card.find(class_=re.compile(r"title|role|jobTitle"))
                or card.find("h2")
                or card.find("h3")
            )
            if not title_el:
                return None
            title = title_el.get_text(strip=True)

            link_el = card.find("a", href=re.compile(r"wellfound\.com/jobs|/jobs/"))
            if not link_el:
                link_el = card.find("a", href=True)
            if not link_el:
                return None

            href = link_el.get("href", "")
            if not href.startswith("http"):
                href = "https://wellfound.com" + href

            company_el = card.find(class_=re.compile(r"company|startup|employer"))
            company = company_el.get_text(strip=True) if company_el else "Unknown"

            loc_el = card.find(class_=re.compile(r"location|city|remote"))
            location = loc_el.get_text(strip=True) if loc_el else "India"

            date_el = card.find(class_=re.compile(r"date|posted|time|ago"))
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
            logger.debug(f"Wellfound card parse error: {e}")
            return None
