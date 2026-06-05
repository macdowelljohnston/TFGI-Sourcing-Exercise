# Skill: Qualification Scoring

## Purpose
Score each cleaned company against Friedkin's investment criteria. Produces a
total fit score (0–100), sub-scores per dimension (0–100), and a qualification
tier label.

## Config section
Edit **`config/pipeline_settings.json`** → **`scoring`**

| Key | What it controls |
|-----|------------------|
| `weights` | Relative weight of the four dimensions (must sum to 1.0) |
| `target_stages` | Growth stages that score 100% on stage fit |
| `stage_partial_scores` | Partial credit for non-target stages (e.g. Pre-seed → 0.3) |
| `target_sectors` | Keywords for sector alignment |
| `sector_match` | How many keyword hits map to full / partial / zero sector score |
| `sector_text_columns` | Fields searched for sector keywords |
| `founder_tag_scores` | Points per Specter founder tag (see skill 03) |
| `founder_normaliser` | Divides tag sum to cap founder sub-score at 100% |
| `momentum` | Headcount, web, and funding-recency parameters |
| `min_score_threshold` | Companies below this total are excluded |
| `top_n_companies` | How many companies appear in the investor brief |
| `score_tiers` | Tier labels and minimum total scores |
| `export_all_qualified` | When true, `scored_companies.csv` includes all qualified rows |

## Scoring dimensions

### 1. Stage fit
- Full score if Growth Stage is in `target_stages`.
- Otherwise uses `stage_partial_scores` for that label, or 0.

### 2. Sector alignment
- Keyword match count across `sector_text_columns` vs `target_sectors`.
- Uses `sector_match.full_if_matches` / `partial_if_matches` thresholds.

### 3. Founder signal
- Rule-based sum of `founder_tag_scores` from comma-separated Founder Highlights.
- Capped at 100% after `founder_normaliser`. See skill 03.

### 4. Growth momentum
- Weighted blend of 6-month headcount growth, 6-month web growth, and funding recency (`momentum` section).

## Final score
```
total_score = round(100 × (stage×w1 + sector×w2 + founder×w3 + momentum×w4))
```
Tier = first `score_tiers` entry where `total_score >= min_score` (highest band first).

## Editing this skill
Edit the `scoring` section in `config/pipeline_settings.json`, then re-run the pipeline.
