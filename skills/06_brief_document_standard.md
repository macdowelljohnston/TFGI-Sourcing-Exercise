# Skill: Brief Document Standard

## Purpose
Defines structure and house style for the weekly sourcing brief — Markdown
(`investor_brief.md`) and Word (`investor_brief.docx`). Both are generated from
the same ranked rows so outputs stay aligned.

## Config section
Edit **`config/pipeline_settings.json`** → **`report`**

| Key | What it controls |
|-----|------------------|
| `title` / `subtitle` | Document title block |
| `font` | Typeface for the Word doc (e.g. Georgia) |
| `body_size_pt` | Body text size in Word |
| `colors.primary` | Headings and company names |
| `colors.accent` | Scores, rule lines, links |
| `colors.muted` / `colors.faint` | Sub-headers and metadata |
| `footer_text` | Confidential footer in Word |
| `show_summary_section` | Portfolio Summary on/off |
| `top_picks_count` | Names in "Top picks" line |
| `max_sectors_in_summary` | Sector rows in summary table |

Scoring knobs for the brief (`top_n_companies`, tiers) live in **`scoring`**.

## Document structure (fixed order)
1. **Header** — title, subtitle, count line (top N in brief + full CSV note).
2. **Portfolio Summary** — tiers, sector concentration, stages, top picks.
3. **Per-company entries** — rank, name, score, tier, meta, website, rationale (skill 04), Action + Diligence (skill 05).

## House style
- Classic serif (Georgia) in Word; plain ASCII punctuation in all outputs.
- Mojibake in source data is repaired before output.
- Confidential footer with page numbers in Word.

## Editing this skill
- **Look and feel:** edit `report` in `config/pipeline_settings.json`.
- **How many companies in the brief:** edit `scoring.top_n_companies`.
- **Rationale content:** edit `rationale` (skill 04) or use `--use-llm`.

Re-run: `python scripts/run_pipeline.py`
