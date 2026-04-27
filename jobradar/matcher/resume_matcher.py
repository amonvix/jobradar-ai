from __future__ import annotations

import re
from collections import Counter

from jobradar.models import JobPosting

TOKEN_PATTERN = re.compile(r"[A-Za-z][A-Za-z0-9+.#-]{1,}")


class ResumeMatcher:
    def __init__(self, cv_text: str, keywords: list[str]) -> None:
        self.cv_tokens = self._tokenize(cv_text)
        self.keywords = [keyword.lower() for keyword in keywords]

    @staticmethod
    def _tokenize(text: str) -> Counter:
        return Counter(token.lower() for token in TOKEN_PATTERN.findall(text))

    def score(self, job: JobPosting) -> tuple[float, list[str]]:
        text = f"{job.title} {job.description}".lower()
        job_tokens = self._tokenize(text)

        overlap = set(self.cv_tokens).intersection(job_tokens)
        overlap_score = float(sum(min(self.cv_tokens[token], job_tokens[token]) for token in overlap))
        keyword_hits = [keyword for keyword in self.keywords if keyword in text]

        score = overlap_score + len(keyword_hits) * 2.5
        reasons = []
        if keyword_hits:
            reasons.append(f"keyword hits: {', '.join(sorted(set(keyword_hits)))}")
        if overlap:
            top_terms = sorted(overlap, key=lambda token: job_tokens[token], reverse=True)[:5]
            reasons.append(f"cv overlap: {', '.join(top_terms)}")

        return score, reasons
