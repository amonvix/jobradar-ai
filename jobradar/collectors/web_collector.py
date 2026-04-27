from __future__ import annotations

import json
import logging
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from jobradar.models import JobPosting

LOGGER = logging.getLogger(__name__)
DEFAULT_TIMEOUT = 20

BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Connection": "keep-alive",
    "Cache-Control": "no-cache",
}


class WebCollector:
    """Collects jobs from job sites using lightweight HTML parsing."""

    def __init__(self, debug: bool = False, debug_html_dir: Path | None = None) -> None:
        self.debug = debug
        self.debug_html_dir = debug_html_dir
        self.session = requests.Session()
        self.session.headers.update(BROWSER_HEADERS)

        retry = Retry(
            total=3,
            connect=3,
            read=3,
            backoff_factor=0.8,
            status_forcelist=(408, 429, 500, 502, 503, 504),
            allowed_methods=frozenset(["GET"]),
            raise_on_status=False,
        )
        adapter = HTTPAdapter(max_retries=retry)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    def collect_from_site(self, site: dict, keywords: list[str]) -> list[JobPosting]:
        name = site.get("name", "unknown")

        if "remoteok" in name.casefold():
            jobs = self._collect_remoteok(site, keywords)
        else:
            jobs = self._collect_generic_site(site, keywords)

        return jobs

    def _collect_generic_site(self, site: dict, keywords: list[str]) -> list[JobPosting]:
        name = site.get("name", "unknown")
        url = site.get("url", "")
        selector = site.get("job_link_selector", "a")
        company = site.get("default_company", name)

        if not url:
            LOGGER.warning("Skipping site with missing URL: %s", site)
            return []

        response = self._safe_get(url, site_name=name)
        if response is None:
            return []

        soup = BeautifulSoup(response.text, "html.parser")
        self._save_debug_html(name, response.text)
        jobs = self._extract_jobs_from_html(
            soup=soup,
            selector=selector,
            source_url=url,
            source_name=name,
            default_company=company,
            keywords=keywords,
        )

        if not jobs:
            page_title = soup.title.get_text(strip=True) if soup.title else "<missing>"
            LOGGER.info(
                "No jobs found for %s (status=%s, title=%s, selector=%s)",
                name,
                response.status_code,
                page_title,
                selector,
            )
        else:
            LOGGER.info("Collected %s candidate jobs from %s", len(jobs), name)

        return jobs

    def _collect_remoteok(self, site: dict, keywords: list[str]) -> list[JobPosting]:
        name = site.get("name", "RemoteOK")
        url = site.get("url", "https://remoteok.com/remote-dev-jobs")

        api_url = site.get("api_url", "https://remoteok.com/api")
        jobs = self._collect_remoteok_api(name=name, api_url=api_url, keywords=keywords)
        if jobs:
            LOGGER.info("Collected %s candidate jobs from %s API", len(jobs), name)
            return jobs

        response = self._safe_get(url, site_name=name)
        if response is None:
            return []

        soup = BeautifulSoup(response.text, "html.parser")
        self._save_debug_html(name, response.text)

        embedded_jobs = self._extract_remoteok_embedded_json(soup=soup, source_name=name, keywords=keywords)
        if embedded_jobs:
            LOGGER.info("Collected %s candidate jobs from %s embedded JSON", len(embedded_jobs), name)
            return embedded_jobs

        selector = site.get("job_link_selector", "a.preventLink")
        html_jobs = self._extract_jobs_from_html(
            soup=soup,
            selector=selector,
            source_url=url,
            source_name=name,
            default_company=site.get("default_company", name),
            keywords=keywords,
        )

        if not html_jobs:
            page_title = soup.title.get_text(strip=True) if soup.title else "<missing>"
            LOGGER.info(
                "No jobs found for %s (status=%s, title=%s, selector=%s)",
                name,
                response.status_code,
                page_title,
                selector,
            )
        return html_jobs

    def _collect_remoteok_api(self, name: str, api_url: str, keywords: list[str]) -> list[JobPosting]:
        response = self._safe_get(api_url, site_name=name)
        if response is None or response.status_code >= 400:
            return []

        try:
            payload = response.json()
        except ValueError:
            return []

        if not isinstance(payload, list):
            return []

        jobs: list[JobPosting] = []
        for item in payload:
            if not isinstance(item, dict):
                continue
            title = str(item.get("position") or item.get("title") or "").strip()
            company = str(item.get("company") or name).strip()
            slug = str(item.get("slug") or "").strip()
            canonical_url = str(item.get("url") or "").strip()
            if not canonical_url and slug:
                canonical_url = f"https://remoteok.com/remote-jobs/{slug}"
            description = str(item.get("description") or item.get("tags") or "")

            if not title or not canonical_url:
                continue

            haystack = f"{title} {company} {description}".lower()
            if keywords and not any(keyword.lower() in haystack for keyword in keywords):
                continue

            jobs.append(
                JobPosting(
                    title=title,
                    company=company,
                    url=canonical_url,
                    source=name,
                    description=description,
                    location=str(item.get("location") or "").strip(),
                )
            )
        return jobs

    def _extract_remoteok_embedded_json(
        self,
        soup: BeautifulSoup,
        source_name: str,
        keywords: list[str],
    ) -> list[JobPosting]:
        jobs: list[JobPosting] = []
        scripts = soup.select("script[type='application/ld+json']")
        for script in scripts:
            raw_json = script.string or script.get_text(strip=True)
            if not raw_json:
                continue
            try:
                payload = json.loads(raw_json)
            except json.JSONDecodeError:
                continue

            items = payload if isinstance(payload, list) else [payload]
            for item in items:
                if not isinstance(item, dict):
                    continue
                if item.get("@type") != "JobPosting":
                    continue
                title = str(item.get("title") or "").strip()
                company = ""
                hiring_org = item.get("hiringOrganization")
                if isinstance(hiring_org, dict):
                    company = str(hiring_org.get("name") or "").strip()
                company = company or source_name
                job_url = str(item.get("url") or "").strip()
                description = str(item.get("description") or "")

                if not title or not job_url:
                    continue
                haystack = f"{title} {company} {description}".lower()
                if keywords and not any(keyword.lower() in haystack for keyword in keywords):
                    continue

                jobs.append(
                    JobPosting(
                        title=title,
                        company=company,
                        url=job_url,
                        source=source_name,
                        description=description,
                    )
                )
        return jobs

    def _extract_jobs_from_html(
        self,
        soup: BeautifulSoup,
        selector: str,
        source_url: str,
        source_name: str,
        default_company: str,
        keywords: list[str],
    ) -> list[JobPosting]:
        jobs: list[JobPosting] = []
        seen_urls: set[str] = set()

        for anchor in soup.select(selector):
            title = anchor.get_text(" ", strip=True)
            href = anchor.get("href", "").strip()
            if not title or not href:
                continue

            full_url = urljoin(source_url, href)
            if full_url in seen_urls:
                continue

            haystack = f"{title} {anchor.parent.get_text(' ', strip=True)}".lower()
            if keywords and not any(keyword.lower() in haystack for keyword in keywords):
                continue

            seen_urls.add(full_url)
            jobs.append(
                JobPosting(
                    title=title,
                    company=default_company,
                    url=full_url,
                    source=source_name,
                    description=anchor.parent.get_text(" ", strip=True),
                )
            )

        return jobs

    def _safe_get(self, url: str, site_name: str) -> requests.Response | None:
        try:
            response = self.session.get(url, timeout=DEFAULT_TIMEOUT)
        except requests.RequestException as exc:
            if self.debug:
                LOGGER.exception("Failed to fetch %s (%s): %s", site_name, url, exc)
            else:
                LOGGER.warning("Failed to fetch %s (%s): %s", site_name, url, exc)
            return None

        if response.status_code == 403 and "weworkremotely" in site_name.casefold():
            if self.debug:
                LOGGER.debug("WeWorkRemotely returned 403 for %s", url)
            else:
                LOGGER.warning("Skipping WeWorkRemotely due to HTTP 403 on %s", url)
            return None

        if response.status_code >= 400:
            if self.debug:
                LOGGER.debug(
                    "HTTP error from %s (%s): status=%s",
                    site_name,
                    url,
                    response.status_code,
                )
            else:
                LOGGER.warning(
                    "HTTP error from %s: status=%s url=%s",
                    site_name,
                    response.status_code,
                    url,
                )
            return None

        return response

    def _save_debug_html(self, site_name: str, html: str) -> None:
        if not self.debug_html_dir:
            return
        self.debug_html_dir.mkdir(parents=True, exist_ok=True)
        safe_name = "".join(char.lower() if char.isalnum() else "_" for char in site_name).strip("_")
        output_path = self.debug_html_dir / f"{safe_name or 'site'}.html"
        output_path.write_text(html, encoding="utf-8")
        LOGGER.debug("Saved debug HTML for %s to %s", site_name, output_path)
