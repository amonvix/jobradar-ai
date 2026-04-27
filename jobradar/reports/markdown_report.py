from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from jobradar.models import RankedJob


def _build_notes(ranked: RankedJob) -> str:
    groups = ", ".join(ranked.matched_target_groups) if ranked.matched_target_groups else "none"
    positive_hits = ", ".join(ranked.positive_keyword_hits) if ranked.positive_keyword_hits else "none"
    negative_hits = ", ".join(ranked.negative_keyword_hits) if ranked.negative_keyword_hits else "none"
    overlap = ", ".join(ranked.cv_overlap_terms) if ranked.cv_overlap_terms else "none"

    return "<br>".join(
        [
            f"target groups: {groups}",
            f"positive keyword hits: {positive_hits}",
            f"negative keyword hits: {negative_hits}",
            f"cv overlap: {overlap}",
        ]
    )


def generate_markdown_report(ranked_jobs: list[RankedJob], output_file: Path) -> None:
    output_file.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        "# JobRadar AI - Ranked Job Opportunities",
        "",
        f"Generated at: {datetime.now(timezone.utc).isoformat()}",
        "",
    ]

    if not ranked_jobs:
        lines.append("No jobs found for the configured keywords.")
    else:
        lines.extend(
            [
                "| Rank | Title | Company | Source | Score | URL | Notes |",
                "|---:|---|---|---|---:|---|---|",
            ]
        )
        for idx, ranked in enumerate(ranked_jobs, start=1):
            notes = _build_notes(ranked)
            lines.append(
                "| {rank} | {title} | {company} | {source} | {score:.2f} | [Link]({url}) | {notes} |".format(
                    rank=idx,
                    title=ranked.job.title.replace("|", "\\|"),
                    company=ranked.job.company.replace("|", "\\|"),
                    source=ranked.job.source.replace("|", "\\|"),
                    score=ranked.score,
                    url=ranked.job.url,
                    notes=notes.replace("|", "\\|"),
                )
            )

    output_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
