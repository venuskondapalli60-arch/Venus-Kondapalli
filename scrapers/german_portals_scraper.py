"""
scrapers/german_portals_scraper.py - Multi-portal scraper for specialized German job sites:
Connecticum, Jobrapido DE, Rheinpfalz Jobs Network, Politjobs, Studentjob, and Firmen in Thüringen.
"""

import re
import logging
from typing import List, Dict, Optional
from bs4 import BeautifulSoup

import config
from scrapers.base_scraper import BaseScraper

logger = logging.getLogger(__name__)


class GermanPortalsScraper(BaseScraper):
    """Aggregated scraper across specialized German career portals and networks."""

    SOURCE_NAME = "German Job Portals"

    TARGET_QUERIES = [
        "Product Manager",
        "Product Designer",
        "UI UX Designer",
        "UX Designer",
    ]

    TARGET_LOCATIONS = [
        "Berlin",
        "München",
        "Frankfurt",
        "Hamburg",
        "Deutschland",
    ]

    def scrape(self) -> List[Dict]:
        """Main scrape method across German job engines."""
        logger.info("German Job Portals: Starting scrape...")
        raw_jobs = []

        headers = self._get_headers({
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7",
        })

        for query in self.TARGET_QUERIES:
            # 1. Connecticum (Germany tech & careers)
            try:
                c_jobs = self._scrape_connecticum(query, headers)
                raw_jobs.extend(c_jobs)
                logger.debug(f"Connecticum: '{query}' -> {len(c_jobs)} jobs")
            except Exception as e:
                logger.debug(f"Connecticum scrape error: {e}")

            # 2. Rheinpfalz / Regional Media Network
            try:
                rp_jobs = self._scrape_rheinpfalz(query, headers)
                raw_jobs.extend(rp_jobs)
                logger.debug(f"Rheinpfalz: '{query}' -> {len(rp_jobs)} jobs")
            except Exception as e:
                logger.debug(f"Rheinpfalz scrape error: {e}")

            # 3. Studentjob DE (tech/creative jobs)
            try:
                sj_jobs = self._scrape_studentjob(query, headers)
                raw_jobs.extend(sj_jobs)
                logger.debug(f"Studentjob: '{query}' -> {len(sj_jobs)} jobs")
            except Exception as e:
                logger.debug(f"Studentjob scrape error: {e}")

            # 4. Politjobs DE (digital & public policy)
            try:
                pj_jobs = self._scrape_politjobs(query, headers)
                raw_jobs.extend(pj_jobs)
                logger.debug(f"Politjobs: '{query}' -> {len(pj_jobs)} jobs")
            except Exception as e:
                logger.debug(f"Politjobs scrape error: {e}")

        logger.info(f"German Job Portals: Collected {len(raw_jobs)} raw jobs")
        return self._filter_and_normalize(raw_jobs)

    def _scrape_connecticum(self, query: str, headers: Dict) -> List[Dict]:
        """Scrape Connecticum.de."""
        url = "https://www.connecticum.de/jobsuche"
        resp = self._get(url, params={"q": query}, headers=headers)
        if not resp:
            return []

        soup = BeautifulSoup(resp.text, "html.parser")
        jobs = []
        for a in soup.find_all("a", href=True):
            href = a.get("href", "")
            title = a.get_text(strip=True)
            if not title or len(title) < 5:
                continue

            if ("job" in href or "stellenanzeige" in href) and any(
                w in title.lower() for w in ["manager", "designer", "ux", "ui", "product", "lead", "engineer"]
            ):
                full_url = href if href.startswith("http") else f"https://www.connecticum.de{href}"
                company = "Connecticum Partner"
                parent = a.find_parent(["div", "li", "article"])
                desc = parent.get_text(" ", strip=True) if parent else title

                jobs.append({
                    "job_id": self._generate_job_id(title, company, full_url),
                    "title": title,
                    "company": company,
                    "location": "Germany",
                    "url": full_url,
                    "apply_url": full_url,
                    "source": "Connecticum.de",
                    "posted_date_raw": "Today",
                    "description": desc[:500],
                })
        return jobs

    def _scrape_rheinpfalz(self, query: str, headers: Dict) -> List[Dict]:
        """Scrape regional newspaper job network (Rheinpfalz, Merkur, etc.)."""
        url = "https://jobs.rheinpfalz.de/jobs/suche"
        resp = self._get(url, params={"q": query}, headers=headers)
        if not resp:
            return []

        soup = BeautifulSoup(resp.text, "html.parser")
        jobs = []
        for a in soup.find_all("a", href=True):
            href = a.get("href", "")
            title = a.get_text(strip=True)
            if not title or len(title) < 5:
                continue

            if ("/job/" in href or "stelle" in href.lower()) and "rheinpfalz.de" in href:
                parent = a.find_parent(["div", "li", "article"])
                desc = parent.get_text(" ", strip=True) if parent else title

                company = "Regional Partner"
                comp_match = re.search(r"bei\s+([A-Za-z0-9\s&.-]+)", desc)
                if comp_match:
                    company = comp_match.group(1).strip()[:40]

                jobs.append({
                    "job_id": self._generate_job_id(title, company, href),
                    "title": title,
                    "company": company,
                    "location": "Rhineland-Palatinate / Germany",
                    "url": href,
                    "apply_url": href,
                    "source": "Regional Media Network",
                    "posted_date_raw": "Today",
                    "description": desc[:500],
                })
        return jobs

    def _scrape_studentjob(self, query: str, headers: Dict) -> List[Dict]:
        """Scrape Studentjob.de."""
        url = "https://www.studentjob.de/stellenangebote"
        resp = self._get(url, params={"query": query}, headers=headers)
        if not resp:
            return []

        soup = BeautifulSoup(resp.text, "html.parser")
        jobs = []
        for a in soup.find_all("a", href=True):
            href = a.get("href", "")
            title = a.get_text(strip=True)
            if not title or len(title) < 5:
                continue

            if href.startswith("/stellenangebote/") and not href.endswith("/stellenangebote/"):
                full_url = f"https://www.studentjob.de{href}"
                company = "StudentJob Employer"
                parent = a.find_parent(["div", "li", "article"])
                desc = parent.get_text(" ", strip=True) if parent else title

                jobs.append({
                    "job_id": self._generate_job_id(title, company, full_url),
                    "title": title,
                    "company": company,
                    "location": "Germany",
                    "url": full_url,
                    "apply_url": full_url,
                    "source": "Studentjob.de",
                    "posted_date_raw": "Today",
                    "description": desc[:500],
                })
        return jobs

    def _scrape_politjobs(self, query: str, headers: Dict) -> List[Dict]:
        """Scrape Politjobs.de."""
        url = "https://politjobs.de/"
        resp = self._get(url, params={"s": query}, headers=headers)
        if not resp:
            return []

        soup = BeautifulSoup(resp.text, "html.parser")
        jobs = []
        for h2 in soup.find_all(["h2", "h3"]):
            a = h2.find("a", href=True)
            if not a:
                continue
            title = a.get_text(strip=True)
            href = a["href"]

            if any(w in title.lower() for w in ["manager", "director", "lead", "designer", "consultant", "strategy"]):
                parent = h2.find_parent(["div", "article", "section"])
                desc = parent.get_text(" ", strip=True) if parent else title

                jobs.append({
                    "job_id": self._generate_job_id(title, "Politjobs Organization", href),
                    "title": title,
                    "company": "Public / Digital Policy Org",
                    "location": "Berlin, Germany",
                    "url": href,
                    "apply_url": href,
                    "source": "Politjobs.de",
                    "posted_date_raw": "Today",
                    "description": desc[:500],
                })
        return jobs
