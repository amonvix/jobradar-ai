from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass(slots=True)
class JobPosting:
    title: str
    company: str
    url: str
    source: str
    location: str = ""
    description: str = ""
    collected_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


@dataclass(slots=True)
class RankedJob:
    job: JobPosting
    score: float
    match_reasons: list[str] = field(default_factory=list)
    matched_target_groups: list[str] = field(default_factory=list)
    positive_keyword_hits: list[str] = field(default_factory=list)
    negative_keyword_hits: list[str] = field(default_factory=list)
    cv_overlap_terms: list[str] = field(default_factory=list)
