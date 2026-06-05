# Skill: Brief Document Standard

## Purpose
Defines the structure and house style for the weekly sourcing brief — the
Markdown brief (read in Cursor) and the Word doc (sent to the investment team).
Both are generated from the same data and follow this standard, so the two
outputs never drift apart.

## Document Structure (in order)

1. **Header** — title, subtitle, and one line giving the number of qualified
   companies and the minimum score. (Scoring weights are intentionally NOT
   shown in the deliverable; they live in the config.)

2. **Portfolio Summary** — a bordered table with three rows: Tiers, Sector
   concentration, and Stages. Followed by "Top picks" (company names only, no
   scores). Computed by build_summary() in scripts/generate_report.py so the
   Markdown and Word versions are identical.

3. **Per-company entries** (kept brief) — heading (rank, name, score, tier),
   meta line (stage | industry | HQ), clickable website, one rationale
   paragraph (skill 04), and Action + Diligence (skill 05).

## House Style (single source of truth: config/report_style.json)

- Classic serif typeface (Georgia) for a sophisticated, old-line feel.
- Restrained monochrome palette: charcoal primary, subtle bronze accent.
- Plain ASCII punctuation only — no em-dashes, no smart quotes. Any mojibake
  in the source data (e.g. "â€™") is auto-repaired before output.
- Confidential footer with page numbers.

| Setting | Controls |
|---------|----------|
| `title` / `subtitle` | Document title block |
| `font` | Typeface for the Word doc |
| `colors.primary` | Headings and company names |
| `colors.accent` | Scores, rule lines, links |
| `colors.muted` / `colors.faint` | Sub-headers and metadata |
| `footer_text` | Confidential footer text |
| `show_summary_section` | Portfolio Summary on/off |
| `top_picks_count` / `max_sectors_in_summary` | Summary detail |

## Editing This Skill
- Change the LOOK: edit config/report_style.json.
- Change SECTIONS/order: edit scripts/generate_report.py and scripts/export_word.py.
- Change summary CONTENT: edit build_summary() in scripts/generate_report.py.
