from __future__ import annotations

import logging
from pathlib import Path

from jobradar.collectors.web_collector import WebCollector
from jobradar.config import load_cv, load_keywords, load_sites
from jobradar.matcher.resume_matcher import ResumeMatcher
from jobradar.ranking.ranker import JobRanker
from jobradar.reports.markdown_report import generate_markdown_report
from jobradar.storage.sqlite_store import SQLiteStore

LOGGER = logging.getLogger(__name__)


class JobRadarPipeline:
    def __init__(
        self,
        sites_path: Path,
        keywords_path: Path,
        cv_path: Path,
        db_path: Path,
        report_path: Path,
        debug: bool = False,
        debug_html_dir: Path | None = None,
    ) -> None:
        self.sites_path = sites_path
        self.keywords_path = keywords_path
        self.cv_path = cv_path
        self.store = SQLiteStore(db_path)
        self.report_path = report_path
        self.debug = debug
        self.debug_html_dir = debug_html_dir

    def run(self) -> int:
        sites = load_sites(self.sites_path)
        keywords = load_keywords(self.keywords_path)
        cv_text = load_cv(self.cv_path)

        collector = WebCollector(debug=self.debug, debug_html_dir=self.debug_html_dir)
        matcher = ResumeMatcher(cv_text=cv_text, keywords=keywords)
        ranker = JobRanker(matcher=matcher)

        all_jobs = []
        for site in sites:
            all_jobs.extend(collector.collect_from_site(site=site, keywords=keywords))

        LOGGER.info("Collected %s total jobs before deduplication", len(all_jobs))
        self.store.save_raw_jobs(all_jobs)

        deduped_jobs = self.store.deduplicate(all_jobs)
        LOGGER.info("Retained %s jobs after deduplication", len(deduped_jobs))

        ranked_jobs = ranker.rank(deduped_jobs)
        self.store.save_ranked_jobs(ranked_jobs)
        generate_markdown_report(ranked_jobs=ranked_jobs, output_file=self.report_path)

        LOGGER.info("Pipeline completed. Report: %s", self.report_path)
        return len(ranked_jobs)
