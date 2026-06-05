# Pipeline configuration

All tunable business rules live in **`pipeline_settings.json`**. The Python scripts
read this file only — edit JSON, save, re-run the pipeline. No code changes needed.

```powershell
python scripts/run_pipeline.py
```

For a live interview walkthrough (weight / sector / filter levers), see the "Live demo" section in the main [README.md](../README.md).

## Sections

| Section | Skill | What you can change |
|---------|-------|---------------------|
| `cleaning` | 01 | Columns kept, active-only filter, dedupe, stage labels |
| `scoring` | 02, 03 | Weights, sectors, stages, founder tags, tiers, top N, threshold |
| `actions` | 05 | Outreach thresholds, timing messages, diligence rules |
| `rationale` | 04 | Default brief paragraph content |
| `report` | 06 | Title, fonts, colours, summary toggles |

## Examples

### Re-weight scoring (demo-friendly)
```json
"scoring": {
  "weights": {
    "stage_fit": 0.20,
    "sector_alignment": 0.20,
    "founder_signal": 0.35,
    "growth_momentum": 0.25
  }
}
```
Weights must sum to **1.0**.

### Add a target sector
```json
"target_sectors": [
  "Transportation",
  "Manufacturing",
  "Drones"
]
```

### Fix Tier 2 outreach (scores are 0–100)
```json
"actions": {
  "reach_out_threshold": 92,
  "partner_review_threshold": 88
}
```

### Add a diligence rule
```json
{
  "field": "founder_score",
  "op": "lt",
  "value": 60,
  "step": "Run extended founder reference checks."
}
```
Append inside `actions.diligence_rules`.

## JSON tips
- Use double quotes for keys and strings.
- No trailing commas after the last item in a list or object.
- If the pipeline prints a validation warning, check weight sums and tier ordering (`min_score` highest first in `score_tiers`).

## Outputs
- **`scored_companies.csv`** — every company at or above `min_score_threshold`.
- **`investor_brief.md` / `.docx`** — top `top_n_companies` only.
