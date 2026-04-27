from __future__ import annotations

from jobradar.matcher.resume_matcher import ResumeMatcher
from jobradar.models import JobPosting, RankedJob


class JobRanker:
    def __init__(self, matcher: ResumeMatcher) -> None:
        self.matcher = matcher

    def rank(self, jobs: list[JobPosting]) -> list[RankedJob]:
        ranked: list[RankedJob] = []
        for job in jobs:
            score, reasons = self.matcher.score(job)
            ranked.append(RankedJob(job=job, score=score, match_reasons=reasons))
        return sorted(ranked, key=lambda item: item.score, reverse=True)
