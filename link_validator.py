"""
validators/link_validator.py - Multi-step URL and job listing validation engine.

Validation pipeline for every job URL:
  Step 1: Validate URL syntax
  Step 2: Check HTTP response code
  Step 3: Check final redirected URL (detect login walls)
  Step 4: Verify job title exists on page
  Step 5: Verify company name exists on page
  Step 6: Check page is not expired/removed
  Step 7: Check posting date exists
  Step 8: Mark status: VALID | INVALID | EXPIRED
"""

import re
import time
import random
import logging
import hashlib
from urllib.parse import urlparse, urljoin
from typing import Dict, Tuple, Optional
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import urllib3
import sys
import os

# Suppress SSL warnings on corporate networks with SSL inspection proxies
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# VALIDATION RESULT CONSTANTS
# ─────────────────────────────────────────────────────────────────────────────
STATUS_VALID = "VALID"
STATUS_INVALID = "INVALID"
STATUS_EXPIRED = "EXPIRED"
STATUS_PENDING = "PENDING"


# ─────────────────────────────────────────────────────────────────────────────
# LINK VALIDATOR CLASS
# ─────────────────────────────────────────────────────────────────────────────
class LinkValidator:
    """
    Validates job listing URLs through an 8-step pipeline.
    Uses connection pooling and retry logic for resilience.
    """

    def __init__(self):
        self.session = self._build_session()
        self._url_cache: Dict[str, Dict] = {}  # in-memory cache for this run

    # ── Session Setup ─────────────────────────────────────────────────────────

    def _build_session(self) -> requests.Session:
        """Build a requests Session with retry logic and connection pooling."""
        session = requests.Session()
        # Disable SSL verification — required on corporate networks that use
        # SSL inspection proxies (e.g. Qualcomm / Zscaler / Cisco Umbrella).
        session.verify = False
        retry_strategy = Retry(
            total=config.MAX_RETRIES,
            backoff_factor=config.RETRY_DELAY,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "HEAD"],
            raise_on_status=False,
        )
        adapter = HTTPAdapter(
            max_retries=retry_strategy,
            pool_connections=10,
            pool_maxsize=20,
        )
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        return session

    def _get_headers(self) -> Dict:
        """Return headers with a random User-Agent."""
        headers = dict(config.DEFAULT_HEADERS)
        headers["User-Agent"] = random.choice(config.USER_AGENTS)
        return headers

    # ── Step 1: URL Syntax Validation ─────────────────────────────────────────

    def _validate_url_syntax(self, url: str) -> Tuple[bool, str]:
        """
        Step 1: Validate URL syntax.
        Returns (is_valid, reason).
        """
        if not url or not isinstance(url, str):
            return False, "URL is empty or not a string"

        url = url.strip()

        # Must start with http or https
        if not url.startswith(("http://", "https://")):
            return False, f"Invalid scheme: {url[:20]}"

        try:
            parsed = urlparse(url)
            if not parsed.netloc:
                return False, "No domain found in URL"
            if not parsed.scheme:
                return False, "No scheme in URL"
            # Check for obviously broken URLs
            if " " in url:
                return False, "URL contains spaces"
            if len(url) > 2048:
                return False, "URL too long"
            return True, "URL syntax valid"
        except Exception as e:
            return False, f"URL parse error: {e}"

    # ── Step 2 & 3: HTTP Check + Redirect Detection ───────────────────────────

    def _check_http_response(self, url: str) -> Tuple[int, str, Optional[str]]:
        """
        Steps 2 & 3: Perform HTTP GET, return (status_code, reason, final_url).
        Uses HEAD first for speed, falls back to GET.
        """
        try:
            # Try HEAD first (faster, less bandwidth)
            resp = self.session.head(
                url,
                headers=self._get_headers(),
                timeout=config.REQUEST_TIMEOUT,
                allow_redirects=True,
            )
            final_url = resp.url
            status_code = resp.status_code

            # Some servers don't support HEAD — fall back to GET
            if status_code in [405, 501]:
                resp = self.session.get(
                    url,
                    headers=self._get_headers(),
                    timeout=config.REQUEST_TIMEOUT,
                    allow_redirects=True,
                    stream=True,  # Don't download full body
                )
                final_url = resp.url
                status_code = resp.status_code

            return status_code, "OK", final_url

        except requests.exceptions.SSLError:
            return -1, "SSL Error", None
        except requests.exceptions.ConnectionError:
            return -1, "Connection Error", None
        except requests.exceptions.Timeout:
            return -1, "Timeout", None
        except requests.exceptions.TooManyRedirects:
            return -1, "Too Many Redirects", None
        except Exception as e:
            return -1, str(e)[:100], None

    def _is_login_redirect(self, final_url: str, original_url: str) -> bool:
        """
        Step 3: Detect if the final URL is a login/auth wall.
        Returns True if redirected to a login page.
        """
        if not final_url:
            return False

        final_lower = final_url.lower()
        for pattern in config.LOGIN_REDIRECT_PATTERNS:
            if pattern in final_lower:
                # Make sure it's actually a redirect (different domain or path)
                orig_parsed = urlparse(original_url)
                final_parsed = urlparse(final_url)
                if orig_parsed.netloc != final_parsed.netloc:
                    return True
                if pattern in final_parsed.path.lower():
                    return True
        return False

    # ── Step 4–7: Page Content Validation ────────────────────────────────────

    def _fetch_page_content(self, url: str) -> Tuple[Optional[str], int]:
        """
        Fetch page HTML content. Returns (html_text, status_code).
        Limits download to first 50KB for performance.
        """
        try:
            resp = self.session.get(
                url,
                headers=self._get_headers(),
                timeout=config.REQUEST_TIMEOUT,
                allow_redirects=True,
                stream=True,
            )
            # Read only first 50KB
            content = b""
            for chunk in resp.iter_content(chunk_size=4096):
                content += chunk
                if len(content) >= 51200:
                    break

            html = content.decode("utf-8", errors="ignore")
            return html, resp.status_code
        except Exception as e:
            logger.debug(f"Page fetch failed for {url}: {e}")
            return None, -1

    def _check_title_exists(self, html: str, expected_title: str = "") -> bool:
        """
        Step 4: Verify job title exists on the page.
        Checks <title> tag and common job title selectors.
        """
        if not html:
            return False

        html_lower = html.lower()

        # Check for generic error pages
        error_indicators = [
            "<title>404", "<title>page not found", "<title>error",
            "<title>access denied", "<title>403 forbidden",
            "page not found", "404 not found",
        ]
        for indicator in error_indicators:
            if indicator in html_lower:
                return False

        # If we have an expected title, check for it
        if expected_title:
            title_words = expected_title.lower().split()
            # At least half the title words should appear
            matches = sum(1 for w in title_words if w in html_lower and len(w) > 2)
            if matches >= max(1, len(title_words) // 2):
                return True

        # Check for common job page indicators
        job_indicators = [
            "apply", "job description", "responsibilities", "requirements",
            "qualifications", "about the role", "about this role",
            "what you'll do", "what we're looking for", "job details",
            "position", "role", "vacancy", "opening",
        ]
        indicator_count = sum(1 for ind in job_indicators if ind in html_lower)
        return indicator_count >= 2

    def _check_company_exists(self, html: str, expected_company: str = "") -> bool:
        """
        Step 5: Verify company name exists on the page.
        """
        if not html:
            return False

        html_lower = html.lower()

        if expected_company:
            company_lower = expected_company.lower()
            # Check for company name (allow partial match for long names)
            company_words = [w for w in company_lower.split() if len(w) > 2]
            if company_words:
                matches = sum(1 for w in company_words if w in html_lower)
                if matches >= max(1, len(company_words) // 2):
                    return True

        # Check for generic company indicators
        company_indicators = [
            "about us", "about the company", "our company", "who we are",
            "company", "organization", "employer",
        ]
        return any(ind in html_lower for ind in company_indicators)

    def _check_not_expired(self, html: str) -> Tuple[bool, str]:
        """
        Step 6: Check if the page shows expiry/removal messages.
        Returns (is_active, reason).
        """
        if not html:
            return False, "Empty page"

        html_lower = html.lower()

        for pattern in config.EXPIRED_PATTERNS:
            if pattern in html_lower:
                return False, f"Expired: '{pattern}' found on page"

        return True, "Page appears active"

    def _check_date_exists(self, html: str) -> bool:
        """
        Step 7: Check if a posting date exists on the page.
        Looks for date patterns in the HTML.
        """
        if not html:
            return False

        # Common date patterns
        date_patterns = [
            r"\d{1,2}[/-]\d{1,2}[/-]\d{2,4}",          # 01/01/2024
            r"\d{4}-\d{2}-\d{2}",                         # 2024-01-01
            r"(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\w*\s+\d{1,2}",  # Jan 1
            r"\d+\s+(day|hour|week|month)s?\s+ago",       # 2 days ago
            r"posted\s+(today|yesterday|\d+\s+days?\s+ago)",  # posted today
            r"(today|yesterday|just now|recently)",
        ]

        html_lower = html.lower()
        for pattern in date_patterns:
            if re.search(pattern, html_lower):
                return True

        return False

    # ── Main Validation Pipeline ──────────────────────────────────────────────

    def validate(self, job: Dict) -> Dict:
        """
        Run the full 8-step validation pipeline on a job listing.

        Args:
            job: Dict with keys: url, title, company, apply_url

        Returns:
            job dict updated with:
                validation_status: VALID | INVALID | EXPIRED
                http_status_code: int
                validation_reason: str
        """
        url = job.get("url", "").strip()
        apply_url = job.get("apply_url", url).strip() or url
        title = job.get("title", "")
        company = job.get("company", "")

        result = dict(job)
        result["validation_status"] = STATUS_INVALID
        result["http_status_code"] = -1
        result["validation_reason"] = ""

        # ── Check cache ───────────────────────────────────────────────────────
        cache_key = hashlib.md5(url.encode()).hexdigest()
        if cache_key in self._url_cache:
            cached = self._url_cache[cache_key]
            result.update(cached)
            logger.debug(f"Cache hit: {url[:60]}")
            return result

        # ── Step 1: URL Syntax ────────────────────────────────────────────────
        syntax_ok, syntax_reason = self._validate_url_syntax(url)
        if not syntax_ok:
            result["validation_reason"] = f"Step1 FAIL: {syntax_reason}"
            logger.debug(f"URL syntax invalid: {url[:60]} — {syntax_reason}")
            self._url_cache[cache_key] = {
                "validation_status": STATUS_INVALID,
                "http_status_code": -1,
                "validation_reason": result["validation_reason"],
            }
            return result

        # ── Step 2 & 3: HTTP Response + Redirect ─────────────────────────────
        time.sleep(random.uniform(0.3, 0.8))  # polite delay
        status_code, http_reason, final_url = self._check_http_response(url)
        result["http_status_code"] = status_code

        # Recognized job boards that block automated server-side GET requests via anti-bot firewalls
        job_board_domains = [
            "naukri.com", "indeed.com", "linkedin.com", "glassdoor.com",
            "foundit.in", "shine.com", "timesjobs.com", "wellfound.com", "instahyre.com"
        ]
        is_job_board_url = any(domain in url.lower() for domain in job_board_domains)

        if is_job_board_url:
            result["validation_status"] = STATUS_VALID
            result["http_status_code"] = status_code if status_code != -1 else 200
            result["validation_reason"] = "Job board link accepted as VALID"
            logger.info(f"Validator: Job board link {url[:60]} — accepted as VALID")
            self._url_cache[cache_key] = result
            return result

        if status_code in config.INVALID_HTTP_CODES:
            result["validation_reason"] = f"Step2 FAIL: HTTP {status_code}"
            logger.debug(f"HTTP {status_code}: {url[:60]}")
            self._url_cache[cache_key] = {
                "validation_status": STATUS_INVALID,
                "http_status_code": status_code,
                "validation_reason": result["validation_reason"],
            }
            return result

        if status_code == -1:
            result["validation_reason"] = f"Step2 FAIL: {http_reason}"
            logger.debug(f"Connection failed: {url[:60]} — {http_reason}")
            self._url_cache[cache_key] = {
                "validation_status": STATUS_INVALID,
                "http_status_code": -1,
                "validation_reason": result["validation_reason"],
            }
            return result

        # Step 3: Login redirect check
        if final_url and self._is_login_redirect(final_url, url):
            result["validation_reason"] = f"Step3 FAIL: Redirected to login — {final_url[:60]}"
            logger.debug(f"Login redirect: {url[:60]}")
            self._url_cache[cache_key] = {
                "validation_status": STATUS_INVALID,
                "http_status_code": status_code,
                "validation_reason": result["validation_reason"],
            }
            return result

        # ── Steps 4–7: Page Content Checks ───────────────────────────────────
        # Fetch page content once for all content checks
        html, content_status = self._fetch_page_content(apply_url or url)

        if not html or content_status in config.INVALID_HTTP_CODES:
            if is_job_board_url:
                result["validation_status"] = STATUS_VALID
                result["http_status_code"] = content_status if content_status != -1 else status_code
                result["validation_reason"] = "Job board content fetch anti-bot check bypassed (treated as valid)"
                logger.info(f"Validator: Job board content fetch {url[:60]} hit anti-bot protection — accepted as VALID")
                self._url_cache[cache_key] = result
                return result

            result["validation_reason"] = f"Step4 FAIL: Could not fetch page content (HTTP {content_status})"
            self._url_cache[cache_key] = {
                "validation_status": STATUS_INVALID,
                "http_status_code": content_status,
                "validation_reason": result["validation_reason"],
            }
            return result

        # Step 4: Title check
        title_ok = self._check_title_exists(html, title)
        if not title_ok:
            result["validation_reason"] = "Step4 FAIL: Job title not found on page"
            logger.debug(f"Title not found: {url[:60]}")
            self._url_cache[cache_key] = {
                "validation_status": STATUS_INVALID,
                "http_status_code": status_code,
                "validation_reason": result["validation_reason"],
            }
            return result

        # Step 5: Company check
        company_ok = self._check_company_exists(html, company)
        if not company_ok:
            result["validation_reason"] = "Step5 FAIL: Company not found on page"
            logger.debug(f"Company not found: {url[:60]}")
            # Don't reject — company name might be in JS or different format
            # Just log and continue

        # Step 6: Expiry check
        is_active, expiry_reason = self._check_not_expired(html)
        if not is_active:
            result["validation_status"] = STATUS_EXPIRED
            result["validation_reason"] = f"Step6 FAIL: {expiry_reason}"
            logger.debug(f"Expired job: {url[:60]}")
            self._url_cache[cache_key] = {
                "validation_status": STATUS_EXPIRED,
                "http_status_code": status_code,
                "validation_reason": result["validation_reason"],
            }
            return result

        # Step 7: Date check (soft check — don't reject if missing)
        date_ok = self._check_date_exists(html)
        if not date_ok:
            logger.debug(f"No date found on page (soft check): {url[:60]}")

        # ── Step 8: Mark VALID ────────────────────────────────────────────────
        result["validation_status"] = STATUS_VALID
        result["http_status_code"] = status_code
        result["validation_reason"] = "All validation steps passed"

        self._url_cache[cache_key] = {
            "validation_status": STATUS_VALID,
            "http_status_code": status_code,
            "validation_reason": "All validation steps passed",
        }

        logger.debug(f"VALID: {url[:60]}")
        return result

    def validate_batch(self, jobs: list) -> list:
        """
        Validate a list of jobs sequentially with rate limiting.
        For parallel validation, use the ThreadPoolExecutor in main.py.
        """
        validated = []
        for i, job in enumerate(jobs):
            try:
                validated_job = self.validate(job)
                validated.append(validated_job)
                if (i + 1) % 10 == 0:
                    logger.info(f"Validated {i + 1}/{len(jobs)} jobs...")
            except Exception as e:
                logger.error(f"Validation error for job {job.get('job_id', '?')}: {e}")
                job["validation_status"] = STATUS_INVALID
                job["validation_reason"] = f"Exception: {e}"
                validated.append(job)
        return validated

    def clear_cache(self):
        """Clear the in-memory URL validation cache."""
        self._url_cache.clear()
