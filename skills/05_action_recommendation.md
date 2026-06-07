# Skill: Action Recommendation

## Purpose
For each qualified company, recommend a concrete next action: outreach tier,
funding timing note, and tailored diligence steps.

Rule-based and deterministic. All thresholds live in config.

## Config section
Edit **`config/pipeline_settings.json`** -> **`actions`**

| Key | What it controls |
|-----|------------------|
| `reach_out_threshold` | Total score (0-100) above which a company gets Tier 1 outreach |
| `partner_review_threshold` | Total score (0-100) above which a company gets Tier 2 outreach |
| `outreach_labels` | Wording for each outreach tier |
| `timing_bands` | Messages based on months since last funding (`{months}` placeholder) |
| `timing_unknown_message` | When last funding date is missing |
| `diligence_rules` | List of rules that add diligence steps to a company's entry |
| `diligence_closers` | Standard steps appended to every company up to the step limit |
| `max_diligence_steps` | Maximum number of diligence bullets per company |

## Outreach tiers (defaults)
| Condition | Label |
|-----------|--------|
| `total_score` is 90 or above | Reach out now (Tier 1) |
| `total_score` is 80 or above | Schedule partner review (Tier 2) |
| otherwise | Monitor (Tier 3) |

Align these thresholds with `scoring.score_tiers` for consistency.

## Diligence rules (defaults)
Rules are evaluated in order. Each rule adds one bullet to the Diligence section
of the brief when its condition is true.

Supported `op` values: `less_than`, `greater_than`, `missing`

| Condition | Step added |
|-----------|------------|
| always | Validate founder track record |
| `sector_score` less than 100 | Confirm core technology and sector fit |
| `momentum_score` less than 70 | Investigate soft growth signals |
| `months_since_funding` greater than 20 | Confirm runway and burn |
| `web_visits` missing | Pull fresh traction data |

## Editing this skill

Example — make Tier 1 outreach require score 90:

```json
"actions": {
  "reach_out_threshold": 90
}
```

Example — add a diligence step when founder score is weak:

```json
{
  "field": "founder_score",
  "op": "less_than",
  "value": 60,
  "step": "Deep-dive founder references and cap table history."
}
```

Append new rules inside `actions.diligence_rules`. Save and re-run:

```powershell
python scripts/run_pipeline.py
```
