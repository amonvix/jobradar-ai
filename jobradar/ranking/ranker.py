from __future__ import annotations

from jobradar.matcher.resume_matcher import ResumeMatcher
from jobradar.models import JobPosting, RankedJob


class JobRanker:
    def __init__(self, matcher: ResumeMatcher, exclude_negative_matches: bool = True) -> None:
        self.matcher = matcher
        self.exclude_negative_matches = exclude_negative_matches

    def rank(self, jobs: list[JobPosting]) -> list[RankedJob]:
        ranked: list[RankedJob] = []
        for job in jobs:
            match = self.matcher.score(job)
            if self.exclude_negative_matches and match["negative_keyword_hits"]:
                continue
            ranked.append(
                RankedJob(
                    job=job,
                    score=float(match["score"]),
                    match_reasons=match["reasons"],
                    matched_target_groups=match["matched_target_groups"],
                    positive_keyword_hits=match["positive_keyword_hits"],
                    negative_keyword_hits=match["negative_keyword_hits"],
                    cv_overlap_terms=match["cv_overlap_terms"],
                )
            )
        return sorted(ranked, key=lambda item: item.score, reverse=True)
