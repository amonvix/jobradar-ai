from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from jobradar.config import load_keywords


class KeywordConfigLoadTests(unittest.TestCase):
    def test_loads_positive_and_negative_keywords_schema(self) -> None:
        payload = {
            "positive_keywords": ["python", "production support"],
            "negative_keywords": ["sales", "finance"],
            "target_role_groups": {
                "Production Support": ["on-call", "runbook"],
            },
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "keywords.json"
            path.write_text(json.dumps(payload), encoding="utf-8")

            cfg = load_keywords(path)

        self.assertEqual(cfg.positive_keywords, ["python", "production support"])
        self.assertEqual(cfg.negative_keywords, ["sales", "finance"])
        self.assertIn("Production Support", cfg.target_role_groups)


if __name__ == "__main__":
    unittest.main()
