from __future__ import annotations

import argparse
import logging
from pathlib import Path

from jobradar.config import ConfigError
from jobradar.logging_utils import setup_logging
from jobradar.pipeline import JobRadarPipeline


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="JobRadar AI CLI")
    parser.add_argument("--sites", default="config/sites.json", type=Path)
    parser.add_argument("--keywords", default="config/keywords.json", type=Path)
    parser.add_argument("--cv", default="config/cv.txt", type=Path)
    parser.add_argument("--db", default="data/jobradar.sqlite", type=Path)
    parser.add_argument("--report", default="reports/jobs_report.md", type=Path)
    parser.add_argument("--log-level", default="INFO")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging and tracebacks")
    parser.add_argument(
        "--debug-html",
        action="store_true",
        help="Save fetched site HTML into debug/{site}.html for troubleshooting selectors",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    effective_log_level = "DEBUG" if args.debug else args.log_level
    setup_logging(effective_log_level)

    pipeline = JobRadarPipeline(
        sites_path=args.sites,
        keywords_path=args.keywords,
        cv_path=args.cv,
        db_path=args.db,
        report_path=args.report,
        debug=args.debug,
        debug_html_dir=Path("debug") if args.debug_html else None,
    )

    try:
        total = pipeline.run()
        logging.getLogger(__name__).info("Ranked %s jobs", total)
        return 0
    except ConfigError as exc:
        logging.getLogger(__name__).error("Configuration error: %s", exc)
        return 2
    except Exception as exc:  # noqa: BLE001 - CLI guardrail
        logging.getLogger(__name__).exception("Unexpected error: %s", exc)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
