"""
recommend_actions.py
Step 3 of the pipeline: outreach action, timing note, and diligence steps.

See skills/05_action_recommendation.md. Tunable values: pipeline_settings.json -> actions.
"""

import pandas as pd

from load_settings import get_section


def _months_since(date):
    if pd.isna(date):
        return None
    return (pd.Timestamp.now() - pd.Timestamp(date)).days / 30.0


def _outreach_action(score, cfg):
    labels = cfg.get("outreach_labels", {})
    reach = cfg.get("reach_out_threshold", 92)
    review = cfg.get("partner_review_threshold", 88)
    if score >= reach:
        return labels.get("tier1", "Reach out now (Tier 1)")
    if score >= review:
        return labels.get("tier2", "Schedule partner review (Tier 2)")
    return labels.get("tier3", "Monitor (Tier 3)")


def _timing_note(months, cfg):
    if months is None:
        return cfg.get("timing_unknown_message",
                       "Funding date unknown — confirm last round before engaging.")
    m = int(round(months))
    for band in cfg.get("timing_bands", []):
        max_m = band.get("max_months")
        if max_m is None or months <= max_m:
            return band["message"].format(months=m)
    return cfg.get("timing_bands", [{}])[-1].get("message", "").format(months=m)


def _rule_context(row):
    """Build field values for diligence rule evaluation."""
    months = _months_since(row.get("Last Funding Date"))
    web = pd.to_numeric(row.get("Web Visits"), errors="coerce")
    return {
        "sector_score": row.get("sector_score"),
        "momentum_score": row.get("momentum_score"),
        "months_since_funding": months,
        "web_visits": None if pd.isna(web) or web == 0 else float(web),
    }


def _eval_rule(rule, ctx):
    if rule.get("always"):
        return True
    field = rule.get("field")
    op = rule.get("op")
    value = rule.get("value")
    actual = ctx.get(field)

    if op == "missing":
        return actual is None
    if actual is None:
        return False
    if op in ("less_than", "lt"):
        return actual < value
    if op in ("greater_than", "gt"):
        return actual > value
    if op in ("less_than_or_equal", "lte"):
        return actual <= value
    if op in ("greater_than_or_equal", "gte"):
        return actual >= value
    if op == "eq":
        return actual == value
    return False


def _diligence_steps(row, cfg):
    steps = []
    ctx = _rule_context(row)
    for rule in cfg.get("diligence_rules", []):
        if _eval_rule(rule, ctx):
            steps.append(rule["step"])

    max_steps = cfg.get("max_diligence_steps", 5)
    for s in cfg.get("diligence_closers", []):
        if len(steps) >= max_steps:
            break
        if s not in steps:
            steps.append(s)

    return steps[:max_steps]


def add_recommendations(ranked, settings):
    cfg = get_section(settings, "actions")
    out = ranked.copy()
    actions, timings, diligence = [], [], []
    for _, row in out.iterrows():
        actions.append(_outreach_action(row["total_score"], cfg))
        timings.append(_timing_note(_months_since(row.get("Last Funding Date")), cfg))
        diligence.append(" | ".join(_diligence_steps(row, cfg)))
    out["outreach_action"] = actions
    out["timing_note"] = timings
    out["diligence_steps"] = diligence
    return out


if __name__ == "__main__":
    from clean_data import load_and_clean
    from score_companies import score_dataframe
    from load_settings import load_settings

    settings = load_settings()
    ranked = score_dataframe(load_and_clean(settings=settings), settings)
    enriched = add_recommendations(ranked, settings)
    print(enriched[["Company Name", "outreach_action", "diligence_steps"]].head(10).to_string())
