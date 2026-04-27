from __future__ import annotations

import re
from collections import Counter

from jobradar.config import KeywordConfig
from jobradar.models import JobPosting

TOKEN_PATTERN = re.compile(r"[A-Za-z][A-Za-z0-9+.#-]{1,}")


class ResumeMatcher:
    def __init__(self, cv_text: str, keyword_config: KeywordConfig) -> None:
        self.cv_tokens = self._tokenize(cv_text)
        self.positive_keywords = [keyword.lower() for keyword in keyword_config.positive_keywords]
        self.negative_keywords = [keyword.lower() for keyword in keyword_config.negative_keywords]
        self.target_role_groups = {
            group: [keyword.lower() for keyword in keywords]
            for group, keywords in keyword_config.target_role_groups.items()
        }

    @staticmethod
    def _tokenize(text: str) -> Counter:
        return Counter(token.lower() for token in TOKEN_PATTERN.findall(text))

    def score(self, job: JobPosting) -> dict:
        text = f"{job.title} {job.description}".lower()
        job_tokens = self._tokenize(text)

        overlap = set(self.cv_tokens).intersection(job_tokens)
        overlap_score = float(sum(min(self.cv_tokens[token], job_tokens[token]) for token in overlap))
        cv_overlap_terms = sorted(overlap, key=lambda token: job_tokens[token], reverse=True)[:7]

        positive_hits = sorted({keyword for keyword in self.positive_keywords if keyword in text})
        negative_hits = sorted({keyword for keyword in self.negative_keywords if keyword in text})

        matched_groups = sorted(
            {
                group_name
                for group_name, group_keywords in self.target_role_groups.items()
                if any(keyword in text for keyword in group_keywords)
            }
        )

        score = overlap_score + len(positive_hits) * 3.0 + len(matched_groups) * 4.0
        if negative_hits:
            score -= 40.0 + len(negative_hits) * 10.0

        reasons = [
            f"target groups: {', '.join(matched_groups) if matched_groups else 'none'}",
            f"positive keyword hits: {', '.join(positive_hits) if positive_hits else 'none'}",
            f"negative keyword hits: {', '.join(negative_hits) if negative_hits else 'none'}",
            f"cv overlap: {', '.join(cv_overlap_terms) if cv_overlap_terms else 'none'}",
        ]

        return {
            "score": score,
            "reasons": reasons,
            "matched_target_groups": matched_groups,
            "positive_keyword_hits": positive_hits,
            "negative_keyword_hits": negative_hits,
            "cv_overlap_terms": cv_overlap_terms,
        }
