from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path


class ConfigError(Exception):
    """Raised when config files are missing or invalid."""


@dataclass(slots=True)
class KeywordConfig:
    positive_keywords: list[str] = field(default_factory=list)
    negative_keywords: list[str] = field(default_factory=list)
    target_role_groups: dict[str, list[str]] = field(default_factory=dict)


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


def _normalize_keywords(values: list[object]) -> list[str]:
    return [str(item).strip().lower() for item in values if str(item).strip()]


def _parse_keyword_dict(payload: dict) -> KeywordConfig:
    raw_positive = payload.get("positive_keywords", payload.get("keywords", []))
    raw_negative = payload.get("negative_keywords", [])
    raw_groups = payload.get("target_role_groups", {})

    if not isinstance(raw_positive, list):
        raise ConfigError("positive_keywords must be a JSON array")
    if not isinstance(raw_negative, list):
        raise ConfigError("negative_keywords must be a JSON array")
    if not isinstance(raw_groups, dict):
        raise ConfigError("target_role_groups must be a JSON object")

    groups: dict[str, list[str]] = {}
    for group_name, group_keywords in raw_groups.items():
        if not isinstance(group_keywords, list):
            raise ConfigError(f"target_role_groups.{group_name} must be a JSON array")
        groups[str(group_name)] = _normalize_keywords(group_keywords)

    return KeywordConfig(
        positive_keywords=_normalize_keywords(raw_positive),
        negative_keywords=_normalize_keywords(raw_negative),
        target_role_groups=groups,
    )


def load_keywords(path: Path) -> KeywordConfig:
    payload = load_json(path)

    if isinstance(payload, list):
        return KeywordConfig(positive_keywords=_normalize_keywords(payload))
    if isinstance(payload, dict):
        return _parse_keyword_dict(payload)

    raise ConfigError("keywords.json must contain either an array or object")


def load_cv(path: Path) -> str:
    if not path.exists():
        raise ConfigError(f"Missing CV file: {path}")
    return path.read_text(encoding="utf-8")
