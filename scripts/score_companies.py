"""
score_companies.py
Step 2 of the pipeline: score each cleaned company against Friedkin's criteria.

See skills/02_qualification_scoring.md and skills/03_founder_assessment.md.
Tunable values: pipeline_settings.json -> scoring.
"""

import pandas as pd

from load_settings import scoring_config


def _stage_fit(stage, config):
    s = str(stage).strip()
    if s in config["target_stages"]:
        return 1.0
    partial = config.get("stage_partial_scores", {})
    return float(partial.get(s, 0.0))


def _sector_alignment(row, config):
    cols = config.get("sector_text_columns",
                       ["Industry", "Tech Vertical", "Sub-industry",
                        "Description", "Tagline"])
    text = " ".join(str(row.get(c, "")) for c in cols).lower()
    matches = sum(1 for kw in config["target_sectors"] if kw.lower() in text)
    sm = config.get("sector_match", {})
    if matches >= sm.get("full_if_matches", 2):
        return sm.get("full_score", 1.0)
    if matches >= sm.get("partial_if_matches", 1):
        return sm.get("partial_score", 0.6)
    return sm.get("no_match_score", 0.0)


def _founder_signal(highlights, config):
    tag_scores = config["founder_tag_scores"]
    normaliser = config.get("founder_normaliser", 1.5)
    if not highlights:
        return 0.0
    tags = [t.strip() for t in str(highlights).split(",")]
    score = sum(tag_scores.get(t, 0.0) for t in tags)
    return min(score / normaliser, 1.0)


def _clamp01(x):
    return max(0.0, min(1.0, x))


def _growth_momentum(row, m):
    emp = pd.to_numeric(row.get("Employee Monthly Growth6"), errors="coerce")
    emp = 0.0 if pd.isna(emp) else emp
    emp_score = _clamp01(emp / m["employee_growth_full_score_pct"])

    web = pd.to_numeric(row.get("Web Visits Monthly Growth6"), errors="coerce")
    web = 0.0 if pd.isna(web) else web
    web_score = _clamp01(web / m["web_growth_full_score_pct"])

    lfd = row.get("Last Funding Date")
    if pd.isna(lfd):
        recency = m.get("unknown_funding_recency", 0.1)
    else:
        months = (pd.Timestamp.now() - pd.Timestamp(lfd)).days / 30.0
        if months <= m["funding_recent_months"]:
            recency = 1.0
        elif months <= m["funding_mid_months"]:
            recency = 0.6
        else:
            recency = 0.2

    ew = m.get("employee_weight", 0.4)
    ww = m.get("web_weight", 0.3)
    rw = m.get("recency_weight", 0.3)
    return ew * emp_score + ww * web_score + rw * recency


def _to_pct(x):
    return int(round(max(0.0, min(1.0, x)) * 100))


def _assign_tier(pct, tiers):
    for tier in tiers:
        if pct >= tier["min_score"]:
            return tier["label"]
    return tiers[-1]["label"] if tiers else "Unranked"


def score_dataframe(df, settings):
    config = scoring_config(settings) if isinstance(settings, dict) and "scoring" in settings else settings
    w = config["weights"]
    m = config["momentum"]
    tiers = config.get("score_tiers", [])

    rows = []
    for _, row in df.iterrows():
        stage = _stage_fit(row.get("Growth Stage"), config)
        sector = _sector_alignment(row, config)
        founder = _founder_signal(row.get("Founder Highlights"), config)
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
    out = out.sort_values("total_score", ascending=False).reset_index(drop=True)
    return out


def brief_shortlist(ranked, settings):
    """Top N companies for the investor brief (full scored set may be larger)."""
    config = scoring_config(settings) if isinstance(settings, dict) and "scoring" in settings else settings
    n = config.get("top_n_companies", 15)
    return ranked.head(n).reset_index(drop=True)


if __name__ == "__main__":
    from clean_data import load_and_clean
    from load_settings import load_settings

    settings = load_settings()
    cleaned = load_and_clean(settings=settings)
    ranked = score_dataframe(cleaned, settings)
    print(ranked[["Company Name", "total_score", "qualification_tier"]].head(15).to_string())
