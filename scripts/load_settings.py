"""
load_settings.py
Load and validate config/pipeline_settings.json (single source of truth).
"""

import json
import os

DEFAULT_PATH = os.path.join("config", "pipeline_settings.json")


def load_settings(path=None):
    path = path or DEFAULT_PATH
    with open(path, "r", encoding="utf-8") as f:
        settings = json.load(f)
    validate_settings(settings)
    return settings


def get_section(settings, name):
    if name not in settings:
        raise KeyError(f"Missing section '{name}' in pipeline settings")
    return settings[name]


def validate_settings(settings):
    """Print warnings for common config mistakes (non-fatal)."""
    scoring = settings.get("scoring", {})
    weights = scoring.get("weights", {})
    if weights:
        total = sum(weights.values())
        if abs(total - 1.0) > 0.01:
            raise ValueError(
                f"scoring.weights sum to {total:.4f} — they must sum to 1.0. "
                f"Current values: {weights}"
            )

    momentum = scoring.get("momentum", {})
    m_weight_keys = ("headcount_weight", "web_weight", "recency_weight")
    m_weights = {k: momentum[k] for k in m_weight_keys if k in momentum}
    if len(m_weights) == 3:
        m_total = sum(m_weights.values())
        if abs(m_total - 1.0) > 0.01:
            raise ValueError(
                f"momentum weights sum to {m_total:.4f} — they must sum to 1.0. "
                f"Current values: {m_weights}"
            )

    tiers = scoring.get("score_tiers", [])
    mins = [t.get("min_score", 0) for t in tiers]
    if mins != sorted(mins, reverse=True):
        print("  Warning: score_tiers min_score values should be descending (highest first)")

    actions = settings.get("actions", {})
    reach = actions.get("reach_out_threshold")
    review = actions.get("partner_review_threshold")
    if reach is not None and review is not None and reach <= review:
        print("  Warning: reach_out_threshold should be greater than partner_review_threshold")


def scoring_config(settings):
    return get_section(settings, "scoring")
