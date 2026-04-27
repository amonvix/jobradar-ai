from __future__ import annotations

import logging
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from jobradar.models import JobPosting

LOGGER = logging.getLogger(__name__)
DEFAULT_TIMEOUT = 20


class WebCollector:
    """Collects jobs from job sites using lightweight HTML parsing."""

    def __init__(self, user_agent: str = "JobRadarAI/0.1") -> None:
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": user_agent})

    def collect_from_site(self, site: dict, keywords: list[str]) -> list[JobPosting]:
        name = site.get("name", "unknown")
        url = site.get("url", "")
        selector = site.get("job_link_selector", "a")
        company = site.get("default_company", name)

        if not url:
            LOGGER.warning("Skipping site with missing URL: %s", site)
            return []

        try:
            response = self.session.get(url, timeout=DEFAULT_TIMEOUT)
            response.raise_for_status()
        except requests.RequestException as exc:
            LOGGER.exception("Failed to fetch site %s (%s): %s", name, url, exc)
            return []

        soup = BeautifulSoup(response.text, "html.parser")
        jobs: list[JobPosting] = []
        seen_urls: set[str] = set()

        for anchor in soup.select(selector):
            title = anchor.get_text(" ", strip=True)
            href = anchor.get("href", "").strip()
            if not title or not href:
                continue

            full_url = urljoin(url, href)
            if full_url in seen_urls:
                continue

            haystack = f"{title} {anchor.parent.get_text(' ', strip=True)}".lower()
            if keywords and not any(keyword.lower() in haystack for keyword in keywords):
                continue

            seen_urls.add(full_url)
            jobs.append(
                JobPosting(
                    title=title,
                    company=company,
                    url=full_url,
                    source=name,
                    description=anchor.parent.get_text(" ", strip=True),
                )
            )

        LOGGER.info("Collected %s candidate jobs from %s", len(jobs), name)
        return jobs
