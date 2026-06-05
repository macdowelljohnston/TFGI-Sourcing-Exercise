# Skill: Qualification Scoring

## Purpose
Score each cleaned company against Friedkin's investment criteria.
Produces a total fit score (0–100), sub-scores per dimension (0–100),
and a qualification tier label for the investor brief.

## Scoring Dimensions

### 1. Stage Fit (weight: see config)
- Maps to target_stages in config/scoring_weights.json
- "Early Stage" / "Series A/B" → 1.0
- "Growth Stage" / "Series B/C" → 1.0
- "Pre-Seed" → 0.3
- "Series D+" → 0.2
- Unknown → 0.0

### 2. Sector Alignment (weight: see config)
- Checks Industry + Tech Vertical + Sub-industry for keywords
- Keywords drawn from target_sectors in config
- 2+ keyword matches → 1.0
- 1 keyword match → 0.6
- 0 matches → 0.0

### 3. Founder Signal (weight: see config)
- Parsed from Founder Highlights free-text via Claude API
- Prior exit or founding experience → +0.4
- Deep domain/operator background → +0.3
- Top-tier university or employer → +0.2
- Multiple founders → +0.1
- Capped at 1.0

### 4. Growth Momentum (weight: see config)
- Employee 6-month growth (40% of sub-score)
- Web visits 6-month growth (30% of sub-score)
- Recency of last funding (30% of sub-score):
  - Under 12 months ago → 1.0
  - 12–24 months ago → 0.6
  - Over 24 months ago → 0.2
  - Unknown → 0.1

## Final Score Formula
Internally each dimension is scored 0–1, then combined:

    total = (stage_fit × w1) + (sector_alignment × w2)
          + (founder_signal × w3) + (growth_momentum × w4)

The pipeline stores `total_score` and sub-scores as integers **0–100**
(`round(total × 100)`). Weights in config are still fractions (e.g. 0.25).

## Qualification Tiers
After computing the 0–100 total, assign the first matching tier from
`score_tiers` in config (highest `min_score` first). Default bands:
- Tier 1 — Priority: 92+
- Tier 2 — Strong: 88–91
- Tier 3 — Qualified: 40–87

Companies below `min_score_threshold` (default 40) are excluded.

## Editing This Skill
- To change weights: edit config/scoring_weights.json — no code change needed.
- To add a scoring dimension: add logic to scripts/score_companies.py
  and a new weight key to the config file.
- To change sector keywords: edit target_sectors in the config file.