"""
recommend_actions.py
Step 4 of the pipeline: for each qualified company, recommend a concrete
next action -- an outreach call and a tailored set of diligence steps.

Rule-based and deterministic (no API key). Thresholds are read from
config/scoring_weights.json -> "actions" (with sensible defaults if absent).

See skills/05_action_recommendation.md for the logic this implements.
"""

import pandas as pd


def _months_since(date):
    if pd.isna(date):
        return None
    return (pd.Timestamp.now() - pd.Timestamp(date)).days / 30.0


def _outreach_action(score, cfg_actions):
    reach = cfg_actions.get("reach_out_threshold", 0.90)
    review = cfg_actions.get("partner_review_threshold", 0.80)
    if score >= reach:
        return "Reach out now (Tier 1)"
    if score >= review:
        return "Schedule partner review (Tier 2)"
    return "Monitor (Tier 3)"


def _timing_note(months):
    if months is None:
        return "Funding date unknown — confirm last round before engaging."
    m = int(round(months))
    if months < 9:
        return f"Raised ~{m}mo ago — build the relationship now, ahead of the next round."
    if months <= 20:
        return f"~{m}mo since last raise — likely approaching a new round; strong time to engage."
    return f"~{m}mo since last raise — may be raising soon or capital-efficient; worth a direct conversation."


def _diligence_steps(row):
    """Tailor diligence to each company's weak spots and data gaps."""
    steps = ["Validate founder track record and prior exit outcomes."]

    if row.get("sector_score", 1.0) < 1.0:
        steps.append("Confirm core technology and fit with target sectors.")

    if row.get("momentum_score", 1.0) < 0.7:
        steps.append("Investigate soft growth signals (headcount / web traffic).")

    months = _months_since(row.get("Last Funding Date"))
    if months is not None and months > 20:
        steps.append("Confirm current runway, burn rate, and timeline to next raise.")

    web = pd.to_numeric(row.get("Web Visits"), errors="coerce")
    if pd.isna(web) or web == 0:
        steps.append("Pull fresh traction data — web/product usage is sparse in this export.")

    # Standard closers, added until we have a useful set.
    for s in ("Assess market size and competitive landscape.",
              "Review cap table and quality of existing investors."):
        if len(steps) >= 5:
            break
        steps.append(s)

    return steps[:5]


def add_recommendations(ranked, config):
    cfg_actions = config.get("actions", {})
    out = ranked.copy()
    actions, timings, diligence = [], [], []
    for _, row in out.iterrows():
        actions.append(_outreach_action(row["total_score"], cfg_actions))
        timings.append(_timing_note(_months_since(row.get("Last Funding Date"))))
        diligence.append(" | ".join(_diligence_steps(row)))
    out["outreach_action"] = actions
    out["timing_note"] = timings
    out["diligence_steps"] = diligence
    return out


if __name__ == "__main__":
    from clean_data import load_and_clean
    from score_companies import load_config, score_dataframe
    cfg = load_config()
    ranked = score_dataframe(load_and_clean(), cfg)
    enriched = add_recommendations(ranked, cfg)
    print(enriched[["Company Name", "outreach_action", "diligence_steps"]].to_string())