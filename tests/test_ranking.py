from __future__ import annotations

import unittest

from jobradar.config import KeywordConfig
from jobradar.matcher.resume_matcher import ResumeMatcher
from jobradar.models import JobPosting
from jobradar.ranking.ranker import JobRanker


class RankingBehaviorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.keyword_config = KeywordConfig(
            positive_keywords=["python", "incident management", "cloud operations"],
            negative_keywords=["sales", "director", "finance"],
            target_role_groups={
                "Incident Management": ["incident management", "sev1", "postmortem"],
                "Cloud Operations": ["cloud operations", "aws", "kubernetes"],
                "Technical Support": ["technical support", "support engineer"],
            },
        )
        self.matcher = ResumeMatcher(
            cv_text="Python support engineer with incident response and cloud operations experience",
            keyword_config=self.keyword_config,
        )

    def test_negative_keywords_are_excluded_by_default(self) -> None:
        ranker = JobRanker(matcher=self.matcher)
        jobs = [
            JobPosting(
                title="Production Support Engineer",
                company="A",
                url="https://example.com/1",
                source="test",
                description="Python incident management on-call support for SaaS platform",
            ),
            JobPosting(
                title="Sales Director",
                company="B",
                url="https://example.com/2",
                source="test",
                description="Lead sales organization and revenue operations",
            ),
        ]

        ranked = ranker.rank(jobs)

        self.assertEqual(len(ranked), 1)
        self.assertEqual(ranked[0].job.title, "Production Support Engineer")
        self.assertEqual(ranked[0].negative_keyword_hits, [])

    def test_negative_keywords_apply_penalty_when_not_excluded(self) -> None:
        ranker = JobRanker(matcher=self.matcher, exclude_negative_matches=False)
        sales_job = JobPosting(
            title="Technical Support Director",
            company="A",
            url="https://example.com/3",
            source="test",
            description="Technical support for enterprise clients with finance workflows",
        )

        result = ranker.rank([sales_job])

        self.assertEqual(len(result), 1)
        self.assertLess(result[0].score, 0)
        self.assertIn("director", result[0].negative_keyword_hits)
        self.assertIn("finance", result[0].negative_keyword_hits)

    def test_target_group_and_positive_hits_are_recorded(self) -> None:
        ranker = JobRanker(matcher=self.matcher)
        job = JobPosting(
            title="Cloud Operations Support Engineer",
            company="A",
            url="https://example.com/4",
            source="test",
            description="Python on-call incident management with AWS and Kubernetes",
        )

        ranked = ranker.rank([job])

        self.assertEqual(len(ranked), 1)
        self.assertIn("Cloud Operations", ranked[0].matched_target_groups)
        self.assertIn("Incident Management", ranked[0].matched_target_groups)
        self.assertIn("python", ranked[0].positive_keyword_hits)
        self.assertGreater(len(ranked[0].cv_overlap_terms), 0)


if __name__ == "__main__":
    unittest.main()
