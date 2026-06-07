# Skill: Screening Summary

## Purpose
Produce a concise, investor-ready rationale for each company in the weekly brief.

**Default:** deterministic template driven by `pipeline_settings.json` → `rationale`.
It renders as flowing prose — a lead sentence (truncated on a sentence or word
boundary, never mid-word), followed by funding, six-month growth signals,
founder credentials, and the qualification score — with each part toggled by the
config flags below.
**Optional:** Claude-written rationales via `--use-llm` using the prompt below.

## Config section (default mode)
Edit **`config/pipeline_settings.json`** → **`rationale`**

| Key | What it controls |
|-----|------------------|
| `max_description_chars` | Truncate company description in the rationale |
| `founder_tags_to_highlight` | Which founder tags to mention in the text |
| `include_funding_section` | Include raised amount and last round |
| `include_growth_signals` | Include headcount / web / employee count |
| `include_founder_tags` | Mention highlighted founder tags |
| `include_score_breakdown` | Append Stage / Sector / Founder / Momentum scores |

## Editing this skill
1. **Template output:** edit `rationale` in `config/pipeline_settings.json`.
2. **LLM output:** edit the Prompt Template below, then run with `--use-llm` and `ANTHROPIC_API_KEY` set.

```powershell
python scripts/run_pipeline.py --use-llm
```

## Prompt Template

You are a senior analyst at a venture capital firm focused on
Transportation, Manufacturing, Physical AI, Automotive, and Aerospace & Defense.

Given the following data for {{company_name}}, write a 3-5 sentence
investor rationale suitable for an internal deal screening brief.

Be specific. Reference the actual funding, growth, and founder data.
Do not use generic VC language. Do not pad.

Company data:
- Name: {{company_name}}
- Description: {{description}}
- Stage: {{growth_stage}}
- Total Funding: {{total_funding}}
- Last Funding: {{last_funding_type}} ({{last_funding_date}})
- Founders: {{founders}}
- Founder Highlights: {{founder_highlights}}
- Employee Count: {{employee_count}}
- Employee 6-month Growth: {{employee_growth_6m}}
- Web Visits: {{web_visits}}
- Web 6-month Growth: {{web_growth_6m}}
- Qualification Score: {{total_score}} ({{qualification_tier}})
- Score Breakdown: Stage {{stage_score}} | Sector {{sector_score}} | Founder {{founder_score}} | Momentum {{momentum_score}}

Return only the rationale paragraph. No bullet points. No headers.
