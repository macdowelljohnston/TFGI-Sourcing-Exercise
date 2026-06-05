"""
score_companies.py
Step 2 of the pipeline: score each cleaned company against Friedkin's
investment criteria, using weights from config/scoring_weights.json.
Outputs fit scores as integers 0-100 plus a qualification tier.

See skills/02_qualification_scoring.md and skills/03_founder_assessment.md
for the logic this implements. All tunable values live in the config file.
"""

import json
import pandas as pd


def load_config(path="config/scoring_weights.json"):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _stage_fit(stage, target_stages):
    s = str(stage).strip()
    if s in target_stages:
        return 1.0
    if s == "Pre-seed / Seed":
        return 0.3
    if s == "Late Stage":
        return 0.2
    return 0.0


def _sector_alignment(row, target_sectors):
    text = " ".join(str(row.get(c, "")) for c in
                    ["Industry", "Tech Vertical", "Sub-industry",
                     "Description", "Tagline"]).lower()
    matches = sum(1 for kw in target_sectors if kw.lower() in text)
    if matches >= 2:
        return 1.0
    if matches == 1:
        return 0.6
    return 0.0


def _founder_signal(highlights, tag_scores, normaliser):
    if not highlights:
        return 0.0
    tags = [t.strip() for t in str(highlights).split(",")]
    score = sum(tag_scores.get(t, 0.0) for t in tags)
    return min(score / normaliser, 1.0)


def _clamp01(x):
    return max(0.0, min(1.0, x))


def _growth_momentum(row, m):
    # Employee 6-month growth (percent) -> 0-1.
    emp = pd.to_numeric(row.get("Employee Monthly Growth6"), errors="coerce")
    emp = 0.0 if pd.isna(emp) else emp
    emp_score = _clamp01(emp / m["employee_growth_full_score_pct"])

    # Web visits 6-month growth (percent) -> 0-1.
    web = pd.to_numeric(row.get("Web Visits Monthly Growth6"), errors="coerce")
    web = 0.0 if pd.isna(web) else web
    web_score = _clamp01(web / m["web_growth_full_score_pct"])

    # Funding recency -> 0-1.
    lfd = row.get("Last Funding Date")
    if pd.isna(lfd):
        recency = 0.1
    else:
        months = (pd.Timestamp.now() - pd.Timestamp(lfd)).days / 30.0
        if months <= m["funding_recent_months"]:
            recency = 1.0
        elif months <= m["funding_mid_months"]:
            recency = 0.6
        else:
            recency = 0.2

    return 0.4 * emp_score + 0.3 * web_score + 0.3 * recency


def _to_pct(x):
    return int(round(max(0.0, min(1.0, x)) * 100))


def _assign_tier(pct, tiers):
    for tier in tiers:
        if pct >= tier["min_score"]:
            return tier["label"]
    return tiers[-1]["label"] if tiers else "Unranked"


def score_dataframe(df, config):
    w = config["weights"]
    target_stages = config["target_stages"]
    target_sectors = config["target_sectors"]
    tag_scores = config["founder_tag_scores"]
    normaliser = config.get("founder_normaliser", 1.5)
    m = config["momentum"]
    tiers = config.get("score_tiers", [])

    rows = []
    for _, row in df.iterrows():
        stage = _stage_fit(row.get("Growth Stage"), target_stages)
        sector = _sector_alignment(row, target_sectors)
        founder = _founder_signal(row.get("Founder Highlights"), tag_scores, normaliser)
        momentum = _growth_momentum(row, m)
        total = (stage * w["stage_fit"] + sector * w["sector_alignment"] +
                 founder * w["founder_signal"] + momentum * w["growth_momentum"])
        total_pct = _to_pct(total)
        rows.append({
            "stage_score": _to_pct(stage),
            "sector_score": _to_pct(sector),
            "founder_score": _to_pct(founder),
            "momentum_score": _to_pct(momentum),
            "total_score": total_pct,
            "qualification_tier": _assign_tier(total_pct, tiers),
        })

    scores = pd.DataFrame(rows, index=df.index)
    out = pd.concat([df, scores], axis=1)

    out = out[out["total_score"] >= config["min_score_threshold"]]
    out = out.sort_values("total_score", ascending=False)
    out = out.head(config["top_n_companies"]).reset_index(drop=True)
    return out


if __name__ == "__main__":
    from clean_data import load_and_clean
    cfg = load_config()
    cleaned = load_and_clean()
    ranked = score_dataframe(cleaned, cfg)
    print(ranked[["Company Name", "total_score", "qualification_tier"]].to_string())