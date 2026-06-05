# TFGI Sourcing Exercise — Specter Screening Pipeline

A repeatable workflow that ingests a weekly Specter CSV export (~150 companies,
~200 columns), qualifies and ranks each company against Friedkin's investment
criteria, and produces an investor-ready shortlist with a rationale for each name.

Built to be **re-run every week** when a fresh export drops in — and to be
**edited by a non-technical team member** without touching any code.

---

## Quick start

```powershell
# 1. Install dependencies (once)
pip install pandas openpyxl

# 2. Drop the latest Specter export into data/input/

# 3. Run
python scripts/run_pipeline.py
```

Results appear in `output/`:
- `investor_brief.md` — the ranked shortlist with a rationale per company
- `scored_companies.csv` — full scores and sub-scores for every qualified company

---

## How it works

The workflow is a three-stage pipeline. Each stage is a separate script, and
each script implements the logic described in a matching **skill file** in
`/skills/`. The skill files are plain-English specs; the scripts are the
executable version. This keeps the *logic* (editable by anyone) separate from
the *implementation* (only touched when behaviour needs to change).

```
data/input/*.xlsx
       │
       ▼
[1] clean_data.py        ← skills/01_data_cleaning.md
       │   selects relevant columns, normalises funding/dates/text,
       │   dedupes, drops inactive companies
       ▼
[2] score_companies.py   ← skills/02_qualification_scoring.md
       │   scores each company 0–100 on four weighted dimensions,
       │   assigns a tier, filters and ranks
       ▼
[3] generate_report.py   ← skills/04_screening_summary.md
       │   writes a data-grounded rationale per company
       ▼
output/investor_brief.md + scored_companies.csv
```

`run_pipeline.py` is the single entry point that runs all three in order.

---

## The four modules (skills)

Each file in `/skills/` does one job and is independently editable.

| File | Job |
|------|-----|
| `01_data_cleaning.md` | Which columns to keep and how to normalise them |
| `02_qualification_scoring.md` | The scoring rubric and how the four dimensions combine |
| `03_founder_assessment.md` | How founder quality is derived from Specter's founder tags |
| `04_screening_summary.md` | How each company's rationale is written |

## The scoring model

Every company gets four sub-scores (each **0–100**), combined using weights from
`config/scoring_weights.json`, plus a **qualification tier** (e.g. Tier 1 — Priority):

| Dimension | What it measures |
|-----------|------------------|
| **Stage fit** | Is the company in a target stage (Series A–C / Early–Growth)? |
| **Sector alignment** | Does it match Friedkin's focus sectors (keyword match on industry + description)? |
| **Founder signal** | Founder pedigree, derived from Specter's structured founder tags (Prior Exit, Serial Founder, Unicorn Experience, etc.) |
| **Growth momentum** | Headcount growth + web traffic growth + funding recency |

```
total_score (0–100) = round(100 × (stage·w1 + sector·w2 + founder·w3 + momentum·w4))
```

Tier labels come from `score_tiers` in the config (default: Priority 92+, Strong 88+, Qualified 40+).

---

## How to update the system (no code required)

**All tuning happens in one file: `config/scoring_weights.json`.**

| To do this… | Edit this in the config |
|-------------|--------------------------|
| Re-weight the four dimensions | `weights` (values should sum to 1.0) |
| Add/remove a target sector | `target_sectors` |
| Change which stages qualify | `target_stages` |
| Change how founder tags score | `founder_tag_scores` |
| Change the shortlist length | `top_n_companies` |
| Change the cutoff for inclusion | `min_score_threshold` (0–100, default 40) |
| Change tier labels and bands | `score_tiers` |

After editing, just re-run `python scripts/run_pipeline.py`. No code changes needed.

### Running on a new week's export
1. Drop the new Specter file into `data/input/` (the pipeline auto-picks the newest file)
2. Run `python scripts/run_pipeline.py`
3. Read `output/investor_brief.md`

---

## Tool choices (and why)

- **Python + pandas** for the pipeline — the cleaning, scoring, and ranking are
  deterministic, auditable, and identical every run. A spreadsheet would be
  fragile across a 200-column weekly export; a pure-LLM approach would be
  non-reproducible and slow over 150 rows.
  - **Cursor (or VSCode)** plus Agent aid. Allows non-technical user to articulate goals to the agent build.
- **A JSON config file** for all tunable values — so a non-technical user can
  change the model without reading code, which is exactly the "edit and re-run"
  requirement.
- **Markdown skill files** as the human-readable spec for each module — they
  document intent and double as editable prompts.
- **Founder scoring is rule-based on Specter's own founder tags**, not a fresh
  LLM parse. The tags (`Prior Exit`, `Serial Founder`, etc.) are already
  structured, so scoring them directly is faster, free, fully reproducible, and
  has no API dependency — which matters for a tool that runs weekly.
- **Optional LLM rationales**: `generate_report.py` writes data-grounded
  rationales deterministically by default. Passing `--use-llm` (with an
  `ANTHROPIC_API_KEY` set) swaps in Claude-written rationales using the prompt
  in `skills/04_screening_summary.md`.

---

## A note on the data

This Specter extract is **pre-filtered to Friedkin's sectors and stages**, so
nearly every company scores ~100% on stage fit and sector alignment — those axes
don't discriminate much *within* this list. The meaningful differentiation comes
from **founder signal** and **growth momentum**, which is where the ranking
actually separates companies. The four-dimension model is kept intact so the
same pipeline still works correctly on a less-filtered export.

---

## Repo structure

```
TFGI-Sourcing-Exercise/
├── config/
│   └── scoring_weights.json     # all tunable knobs live here
├── skills/                      # plain-English spec for each module
│   ├── 01_data_cleaning.md
│   ├── 02_qualification_scoring.md
│   ├── 03_founder_assessment.md
│   ├── 04_screening_summary.md
│   └── README.md
├── scripts/                     # the executable pipeline
│   ├── clean_data.py
│   ├── score_companies.py
│   ├── generate_report.py
│   └── run_pipeline.py
├── data/
│   ├── input/                   # drop weekly Specter export here
│   └── output/                  # cleaned_data.csv (intermediate)
├── output/                      # investor_brief.md + scored_companies.csv
└── README.md
```