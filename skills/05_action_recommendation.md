# Skill: Action Recommendation

## Purpose
For each qualified company, recommend a concrete next action: outreach tier,
funding timing note, and tailored diligence steps.

Rule-based and deterministic. All thresholds live in config.

## Config section
Edit **`config/pipeline_settings.json`** → **`actions`**

| Key | What it controls |
|-----|------------------|
| `reach_out_threshold` | Total score (0–100) for Tier 1 outreach |
| `partner_review_threshold` | Total score (0–100) for Tier 2 outreach |
| `outreach_labels` | Wording for each outreach tier |
| `timing_bands` | Messages based on months since last funding (`{months}` placeholder) |
| `timing_unknown_message` | When last funding date is missing |
| `diligence_rules` | Declarative list of when to add each diligence step |
| `diligence_closers` | Standard steps appended until `max_diligence_steps` |
| `max_diligence_steps` | Cap on diligence bullets per company |

## Outreach tiers (defaults)
| Condition | Label |
|-----------|--------|
| `total_score >= 92` | Reach out now (Tier 1) |
| `total_score >= 88` | Schedule partner review (Tier 2) |
| otherwise | Monitor (Tier 3) |

Align thresholds with `scoring.score_tiers` for consistency.

## Diligence rules (defaults)
Rules are evaluated in order. Supported `op` values: `always`, `lt`, `gt`, `missing`.

| Rule | Step added when true |
|------|----------------------|
| always | Validate founder track record |
| `sector_score < 100` | Confirm core technology and sector fit |
| `momentum_score < 70` | Investigate soft growth signals |
| `months_since_funding > 20` | Confirm runway and burn |
| `web_visits` missing | Pull fresh traction data |

## Editing this skill
Example — make Tier 1 outreach require score 95:

```json
"actions": {
  "reach_out_threshold": 95,
  ...
}
```

Example — add a diligence step when founder score is weak:

```json
{
  "field": "founder_score",
  "op": "lt",
  "value": 60,
  "step": "Deep-dive founder references and cap table history."
}
```

Save and re-run: `python scripts/run_pipeline.py`
