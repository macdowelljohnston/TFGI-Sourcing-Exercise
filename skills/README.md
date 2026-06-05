# Skills

Each file in this folder is one module of the Friedkin Specter screening pipeline.
**Behavior is controlled by `config/pipeline_settings.json`** — skills explain what
each section does and how to edit it without code.

| Skill | Config section | Role |
|-------|----------------|------|
| [01_data_cleaning.md](01_data_cleaning.md) | `cleaning` | Ingest and normalise the Specter export |
| [02_qualification_scoring.md](02_qualification_scoring.md) | `scoring` | Four-dimension score and tiers |
| [03_founder_assessment.md](03_founder_assessment.md) | `scoring` (founder tags) | Founder sub-score from Specter tags |
| [04_screening_summary.md](04_screening_summary.md) | `rationale` + Prompt Template | Per-company rationale (template or LLM) |
| [05_action_recommendation.md](05_action_recommendation.md) | `actions` | Outreach, timing, diligence |
| [06_brief_document_standard.md](06_brief_document_standard.md) | `report` | Brief layout and Word styling |

## How to update criteria
1. Open `config/pipeline_settings.json`.
2. Edit the section for the module you want to change (see table above).
3. Save and run from the repo root:

```powershell
python scripts/run_pipeline.py
```

See [config/README.md](../config/README.md) for section-by-section examples.

## Default vs LLM mode
- **Default:** deterministic scoring, rationales, and actions — no API key.
- **Optional LLM rationales:** `python scripts/run_pipeline.py --use-llm`  
  Uses the Prompt Template in `04_screening_summary.md` (requires `ANTHROPIC_API_KEY`).

Founder scoring is always rule-based (skill 03); it does not call an LLM.
