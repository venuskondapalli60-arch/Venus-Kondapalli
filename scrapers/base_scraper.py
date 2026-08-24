"""
scrapers/base_scraper.py - Abstract base class for all job scrapers.

All scrapers inherit from BaseScraper and implement the `scrape()` method.
Provides shared utilities: HTTP session, date parsing, job ID generation,
rate limiting, and raw job dict normalization.
"""

import re
import time
import random
import hashlib
import logging
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import urllib3
import sys
import os

# Suppress SSL warnings on corporate networks with SSL inspection proxies
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

logger = logging.getLogger(__name__)


class BaseScraper(ABC):
    """
    Abstract base class for all job board scrapers.

    Subclasses must implement:
        scrape() -> List[Dict]

    Each returned job dict must contain at minimum:
        job_id, title, company, location, url, apply_url,
        source, posted_date, posted_date_raw, description
    """

    SOURCE_NAME = "Unknown"

    def __init__(self):
        self.session = self._build_session()
        self.existing_urls: set = set()
        self.existing_job_ids: set = set()
        logger.debug(f"{self.__class__.__name__} initialized.")

    # ── Session ───────────────────────────────────────────────────────────────

    def _build_session(self) -> requests.Session:
        """Build a resilient requests Session."""
        session = requests.Session()
        # Disable SSL verification — required on corporate networks that use
        # SSL inspection proxies (e.g. Qualcomm / Zscaler / Cisco Umbrella).
        session.verify = False
        retry = Retry(
            total=config.MAX_RETRIES,
            backoff_factor=config.RETRY_DELAY,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST", "HEAD"],
            raise_on_status=False,
        )
        adapter = HTTPAdapter(
            max_retries=retry,
            pool_connections=5,
            pool_maxsize=10,
        )
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        return session

    def _get_headers(self, extra: Dict = None) -> Dict:
        """Return request headers with random User-Agent."""
        headers = dict(config.DEFAULT_HEADERS)
        headers["User-Agent"] = random.choice(config.USER_AGENTS)
        if extra:
            headers.update(extra)
        return headers

    def _get(self, url: str, params: Dict = None, headers: Dict = None,
             timeout: int = None) -> Optional[requests.Response]:
        """
        Perform a GET request with error handling.
        Returns Response or None on failure.
        """
        try:
            time.sleep(random.uniform(0.5, config.RATE_LIMIT_DELAY))
            resp = self.session.get(
                url,
                params=params,
                headers=headers or self._get_headers(),
                timeout=timeout or config.REQUEST_TIMEOUT,
                allow_redirects=True,
            )
            if resp.status_code == 200:
                return resp
            elif resp.status_code == 429:
                logger.warning(f"Rate limited by {url[:50]}. Sleeping 30s...")
                time.sleep(30)
                return None
            else:
                logger.debug(f"HTTP {resp.status_code} from {url[:60]}")
                return None
        except requests.exceptions.Timeout:
            logger.warning(f"Timeout: {url[:60]}")
            return None
        except requests.exceptions.ConnectionError:
            logger.warning(f"Connection error: {url[:60]}")
            return None
        except Exception as e:
            logger.error(f"GET error for {url[:60]}: {e}")
            return None

    def _post(self, url: str, json_data: Dict = None, data: Dict = None,
              headers: Dict = None) -> Optional[requests.Response]:
        """Perform a POST request with error handling."""
        try:
            time.sleep(random.uniform(0.5, config.RATE_LIMIT_DELAY))
            resp = self.session.post(
                url,
                json=json_data,
                data=data,
                headers=headers or self._get_headers(),
                timeout=config.REQUEST_TIMEOUT,
                allow_redirects=True,
            )
            if resp.status_code in [200, 201]:
                return resp
            else:
                logger.debug(f"POST HTTP {resp.status_code} from {url[:60]}")
                return None
        except Exception as e:
            logger.error(f"POST error for {url[:60]}: {e}")
            return None

    # ── Date Parsing ──────────────────────────────────────────────────────────

    def _parse_posted_date(self, raw_date: str) -> Optional[str]:
        """
        Parse various date formats into YYYY-MM-DD.
        Handles: "2 days ago", "today", "yesterday", "2024-01-15", etc.
        Returns None if date is older than MAX_DAYS_OLD.
        """
        if not raw_date:
            return datetime.now().strftime("%Y-%m-%d")

        raw_lower = raw_date.lower().strip()
        today = datetime.now()

        # "just now", "today", "few hours ago"
        if any(x in raw_lower for x in ["just now", "today", "few hours", "hour ago",
                                          "hours ago", "minute", "second"]):
            return today.strftime("%Y-%m-%d")

        # "yesterday"
        if "yesterday" in raw_lower:
            return (today - timedelta(days=1)).strftime("%Y-%m-%d")

        # "X days ago"
        days_match = re.search(r"(\d+)\s+day", raw_lower)
        if days_match:
            days = int(days_match.group(1))
            if days > config.MAX_DAYS_OLD:
                return None  # Too old
            return (today - timedelta(days=days)).strftime("%Y-%m-%d")

        # "X weeks ago"
        weeks_match = re.search(r"(\d+)\s+week", raw_lower)
        if weeks_match:
            weeks = int(weeks_match.group(1))
            days = weeks * 7
            if days > config.MAX_DAYS_OLD:
                return None
            return (today - timedelta(days=days)).strftime("%Y-%m-%d")

        # "X months ago" — always too old
        if "month" in raw_lower:
            return None

        # ISO format: 2024-01-15
        iso_match = re.search(r"(\d{4})-(\d{2})-(\d{2})", raw_date)
        if iso_match:
            try:
                dt = datetime.strptime(iso_match.group(0), "%Y-%m-%d")
                if (today - dt).days > config.MAX_DAYS_OLD:
                    return None
                return dt.strftime("%Y-%m-%d")
            except ValueError:
                pass

        # DD/MM/YYYY, DD-MM-YYYY, MM/DD/YYYY, or MM-DD-YYYY
        slash_match = re.search(r"(\d{1,2})([/-])(\d{1,2})[/-](\d{2,4})", raw_date)
        if slash_match:
            sep = slash_match.group(2)          # '/' or '-'
            matched_str = slash_match.group(0)  # e.g. "21/08/2026" or "21-08-2026"
            try:
                # Try DD/MM/YYYY or DD-MM-YYYY first (Indian format)
                dt = datetime.strptime(matched_str, f"%d{sep}%m{sep}%Y")
                if (today - dt).days > config.MAX_DAYS_OLD:
                    return None
                return dt.strftime("%Y-%m-%d")
            except ValueError:
                try:
                    dt = datetime.strptime(matched_str, f"%m{sep}%d{sep}%Y")
                    if (today - dt).days > config.MAX_DAYS_OLD:
                        return None
                    return dt.strftime("%Y-%m-%d")
                except ValueError:
                    pass

        # Month name formats: "Jan 15, 2024" or "15 Jan 2024"
        month_patterns = [
            r"(\d{1,2})\s+(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\w*\s+(\d{4})",
            r"(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\w*\s+(\d{1,2}),?\s+(\d{4})",
        ]
        month_map = {
            "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
            "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
        }
        for pattern in month_patterns:
            m = re.search(pattern, raw_lower)
            if m:
                try:
                    groups = m.groups()
                    if groups[0].isdigit():
                        day, month_str, year = int(groups[0]), groups[1][:3], int(groups[2])
                    else:
                        month_str, day, year = groups[0][:3], int(groups[1]), int(groups[2])
                    month = month_map.get(month_str, 1)
                    dt = datetime(year, month, day)
                    if (today - dt).days > config.MAX_DAYS_OLD:
                        return None
                    return dt.strftime("%Y-%m-%d")
                except (ValueError, IndexError):
                    pass

        # Default: assume today if we can't parse
        return today.strftime("%Y-%m-%d")

    def _is_date_fresh(self, posted_date: str) -> bool:
        """Return True if posted_date is within MAX_DAYS_OLD."""
        if not posted_date:
            return True  # Assume fresh if unknown
        try:
            dt = datetime.strptime(posted_date, "%Y-%m-%d")
            return (datetime.now() - dt).days <= config.MAX_DAYS_OLD
        except ValueError:
            return True

    # ── Job ID Generation ─────────────────────────────────────────────────────

    def _generate_job_id(self, title: str, company: str, url: str) -> str:
        """
        Generate a stable unique job ID from title + company + URL.
        Uses MD5 hash for consistency.
        """
        raw = f"{title.lower().strip()}|{company.lower().strip()}|{url.strip()}"
        return hashlib.md5(raw.encode()).hexdigest()[:16]

    # ── Job Dict Normalization ────────────────────────────────────────────────

    def _normalize_job(self, raw: Dict) -> Optional[Dict]:
        """
        Normalize a raw scraped job dict into the standard format.
        Returns None if required fields are missing.
        """
        title = (raw.get("title") or "").strip()
        company = (raw.get("company") or "").strip()
        url = (raw.get("url") or "").strip()

        # Required fields
        if not title or not company or not url:
            return None

        # Validate URL starts with http
        if not url.startswith(("http://", "https://")):
            return None

        posted_date_raw = (raw.get("posted_date_raw") or raw.get("posted_date") or "")
        posted_date = self._parse_posted_date(posted_date_raw)

        # Reject if too old
        if posted_date is None:
            return None

        job_id = raw.get("job_id") or self._generate_job_id(title, company, url)

        return {
            "job_id": job_id,
            "title": title,
            "company": company,
            "location": (raw.get("location") or "India").strip(),
            "url": url,
            "apply_url": (raw.get("apply_url") or url).strip(),
            "source": raw.get("source", self.SOURCE_NAME),
            "posted_date": posted_date,
            "posted_date_raw": posted_date_raw,
            "description": (raw.get("description") or "").strip()[:2000],
            "match_score": 0.0,
            "validation_status": "PENDING",
            "http_status_code": 0,
        }

    def _is_duplicate(self, job_id: str, url: str) -> bool:
        """Check against in-memory sets (pre-loaded from DB)."""
        return job_id in self.existing_job_ids or url in self.existing_urls

    def set_existing_data(self, urls: set, job_ids: set):
        """Load existing URLs and job IDs for duplicate detection."""
        self.existing_urls = urls
        self.existing_job_ids = job_ids

    # ── Abstract Method ───────────────────────────────────────────────────────

    @abstractmethod
    def scrape(self) -> List[Dict]:
        """
        Scrape job listings from the source.
        Returns a list of normalized job dicts.
        """
        raise NotImplementedError

    # ── Shared Post-Processing ────────────────────────────────────────────────

    def _filter_and_normalize(self, raw_jobs: List[Dict]) -> List[Dict]:
        """
        Normalize, deduplicate, and filter a list of raw job dicts.
        Returns clean list ready for validation and scoring.
        """
        seen_in_batch = set()
        results = []

        for raw in raw_jobs:
            try:
                job = self._normalize_job(raw)
                if not job:
                    continue

                # Dedup within this batch
                if job["url"] in seen_in_batch:
                    continue
                seen_in_batch.add(job["url"])

                # Dedup against database
                if self._is_duplicate(job["job_id"], job["url"]):
                    logger.debug(f"Duplicate skipped: {job['title']} @ {job['company']}")
                    continue

                results.append(job)
            except Exception as e:
                logger.error(f"Normalization error: {e} | raw={raw}")

        logger.info(f"{self.SOURCE_NAME}: {len(results)} new jobs after dedup (from {len(raw_jobs)} raw)")
        return results
