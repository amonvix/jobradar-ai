from __future__ import annotations

import json
from pathlib import Path


class ConfigError(Exception):
    """Raised when config files are missing or invalid."""


def load_json(path: Path) -> dict | list:
    if not path.exists():
        raise ConfigError(f"Missing config file: {path}")
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def load_sites(path: Path) -> list[dict]:
    sites = load_json(path)
    if not isinstance(sites, list):
        raise ConfigError("sites.json must contain a JSON array")
    return sites


def load_keywords(path: Path) -> list[str]:
    keywords = load_json(path)
    if not isinstance(keywords, list):
        raise ConfigError("keywords.json must contain a JSON array")
    return [str(item).strip() for item in keywords if str(item).strip()]


def load_cv(path: Path) -> str:
    if not path.exists():
        raise ConfigError(f"Missing CV file: {path}")
    return path.read_text(encoding="utf-8")
