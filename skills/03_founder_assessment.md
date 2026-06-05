# Skill: Founder Assessment

## Purpose
Derive a founder quality sub-score from Specter's structured **Founder Highlights**
tags (e.g. Prior Exit, Serial Founder, Unicorn Experience). Fast, reproducible,
and free of API calls — suitable for a weekly batch run.

## Config section
Edit **`config/pipeline_settings.json`** → **`scoring`**

| Key | What it controls |
|-----|------------------|
| `founder_tag_scores` | Points added when each tag appears in Founder Highlights |
| `founder_normaliser` | Tag sum is divided by this value, then capped at 1.0 (×100 in output) |

## How scoring works
1. Split `Founder Highlights` on commas.
2. Sum the configured points for each recognised tag.
3. `founder_signal = min(sum / founder_normaliser, 1.0)` → stored as 0–100.

Example tags and default weights:

| Tag | Default points |
|-----|----------------|
| Prior Exit | 0.35 |
| Prior IPO | 0.35 |
| Serial Founder | 0.25 |
| Unicorn Experience | 0.20 |
| Top University | 0.10 |

(Add or remove tags in `founder_tag_scores`; unknown tags score 0.)

## Editing this skill
- **Add a tag:** add `"Tag Name": 0.15` under `founder_tag_scores`.
- **Re-weight founder vs momentum:** change `weights.founder_signal` in the same `scoring` section.

Re-run: `python scripts/run_pipeline.py`

## Note on LLM mode
Founder scoring is always rule-based. Optional LLM-written **rationales** use skill 04 with `--use-llm`; they do not change founder scores.
