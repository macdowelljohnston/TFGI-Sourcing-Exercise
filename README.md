# TFGI Sourcing Exercise — Specter Screening Pipeline

A repeatable workflow that ingests a weekly Specter CSV export, qualifies and ranks each company against The Friedkin Group's investment criteria, and produces an investor-ready shortlist with a rationale for each name.

Built to be **re-run every week** when a fresh export drops in — and to be
**edited by a non-technical team member** without touching any code.

---

## Quick start

```powershell
# 1. Install dependencies (once)
pip install pandas openpyxl python-docx

# 2. Drop the latest Specter export into data/input/

# 3. Run
python scripts/run_pipeline.py
```

Results appear in `output/<filename>_<date>/`:
- `scored_companies.csv` — all companies above the score threshold
- `investor_brief.md` — top N ranked names with rationale and actions
- `investor_brief.docx` — Word version (also copied to Desktop when found)

---

## How it works

Four pipeline steps plus optional Word export. Each step maps to a **skill file**
in `/skills/` (human-readable spec) and a **config section** in
`config/pipeline_settings.json` (machine-readable rules).

```
data/input/*.xlsx
       |
       v
[1] clean_data.py         <- skills/01  |  config: cleaning
       |
       v
[2] score_companies.py    <- skills/02-03  |  config: scoring
       |
       v
[3] recommend_actions.py  <- skills/05  |  config: actions
       |
       v
[4] generate_report.py    <- skills/04, 06  |  config: rationale, report
       |
       +--> export_word.py (optional)
       v
output/<run>/investor_brief.md + scored_companies.csv [+ .docx]
```

`run_pipeline.py` is the single entry point.

---

## The six modules (skills)

| Skill | Config section | Job |
|-------|----------------|-----|
| `01_data_cleaning.md` | `cleaning` | Columns, filters, normalisation |
| `02_qualification_scoring.md` | `scoring` | Four-dimension score and tiers |
| `03_founder_assessment.md` | `scoring` | Founder tags from Specter |
| `04_screening_summary.md` | `rationale` | Per-company rationale (+ LLM prompt) |
| `05_action_recommendation.md` | `actions` | Outreach, timing, diligence |
| `06_brief_document_standard.md` | `report` | Brief layout and Word style |

See [skills/README.md](skills/README.md) and [config/README.md](config/README.md).

---

## The scoring model

Every company gets four sub-scores (0–100), combined using `scoring.weights`:

| Dimension | What it measures |
|-----------|------------------|
| **Stage fit** | Target stages (Early / Growth) vs partial credit for others |
| **Sector alignment** | Keyword match on industry and description |
| **Founder signal** | Specter founder tags (Prior Exit, Serial Founder, etc.) |
| **Growth momentum** | Headcount + web growth + funding recency |

```
total_score = round(100 x (stage*w1 + sector*w2 + founder*w3 + momentum*w4))
```

Tier labels come from `scoring.score_tiers` (default: Tier 1 at 80+, Tier 2 at 70+, Tier 3 at 60+). Companies below `min_score_threshold` (default 75) are excluded.

---

## How to update the system (no code required)

**All tuning is in one file: `config/pipeline_settings.json`.**

| To do this... | Edit this section |
|---------------|-------------------|
| Change columns or filters | `cleaning` |
| Re-weight dimensions | `scoring.weights` (sum to 1.0) |
| Add/remove sectors or stages | `scoring.target_sectors`, `target_stages` |
| Change founder tag points | `scoring.founder_tag_scores` |
| Change shortlist length | `scoring.top_n_companies` |
| Change score cutoff | `scoring.min_score_threshold` |
| Change tier bands | `scoring.score_tiers` |
| Change outreach / diligence | `actions` |
| Change rationale text | `rationale` |
| Change brief title / colours | `report` |

After editing, re-run:

```powershell
python scripts/run_pipeline.py
```

### Live demo (walkthrough script)

Everything the interviewer may ask you to change lives in **`config/pipeline_settings.json`**. Re-run with:

```powershell
python scripts/run_pipeline.py
```

Keep your Specter file in `data/input/` and re-run after each config edit.

| They ask to change… | Config path | Effect | What to show after re-run |
|---------------------|-------------|--------|---------------------------|
| **Scoring weight** | `scoring.weights` (must sum to 1.0) | Re-orders top 15 in the brief | Terminal Top 5 + `output/<run>/investor_brief.md` |
| **Sector** | `scoring.target_sectors` | Changes `sector_score` and sector summary | `scored_companies.csv` sorted by `sector_score` |
| **Filter** | `scoring.min_score_threshold` (e.g. `60` → `75`) or `scoring.target_stages` | Fewer/more qualified companies | Terminal: `N companies passed the threshold` |
| Outreach tiers (bonus) | `actions.reach_out_threshold` | Tier 1 vs Tier 2 action lines | `Action:` lines in the brief |

**Suggested live tweak:** set `founder_signal` to `0.40` and `growth_momentum` to `0.30` (and `stage_fit`/`sector_alignment` to `0.15` each — weights must sum to 1.0), re-run, show Top 5 in the terminal and `output/<run>/investor_brief.md`.

Add `--no-word` to skip the Word document during a quick demo. If `data/input/` is empty, drop a Specter export there, or pass `--input path/to/file.xlsx`.

### Optional LLM rationales
```powershell
python scripts/run_pipeline.py --use-llm
```
Requires `ANTHROPIC_API_KEY`. Uses the prompt in `skills/04_screening_summary.md`.

### Running on a new week's export
1. Drop the new Specter file into `data/input/` (newest file is picked automatically).
2. Run `python scripts/run_pipeline.py`.
3. Open `output/<latest_run>/investor_brief.md`.

Input files remain in `data/input/` after each run. Use `data/input/archive/` only if you move old exports there manually.

---

## Tool choices (and why)

- **Python + pandas** — deterministic, auditable cleaning and scoring across ~150 rows weekly.
- **Single JSON config** — non-technical users change criteria without reading code.
- **Markdown skills** — modular documentation; skill 04 doubles as the LLM prompt source.
- **Rule-based founder tags** — reproducible, no API cost; Specter already structures highlights.
- **Optional Claude** — `--use-llm` for richer rationales when desired.

---

## A note on the data

This Specter extract is **pre-filtered to Friedkin's sectors and stages**, so
many companies score ~100 on stage and sector. Differentiation within the list
comes mainly from **founder signal** and **growth momentum**. The four-dimension
model still applies correctly on a broader export.

---

## Repo structure

```
TFGI-Sourcing-Exercise/
├── config/
│   ├── pipeline_settings.json   # all tunable knobs
│   └── README.md
├── skills/                      # one module per pipeline step
│   ├── 01_data_cleaning.md
│   ├── 02_qualification_scoring.md
│   ├── 03_founder_assessment.md
│   ├── 04_screening_summary.md
│   ├── 05_action_recommendation.md
│   ├── 06_brief_document_standard.md
│   └── README.md
├── scripts/
│   ├── load_settings.py
│   ├── load_skill.py
│   ├── clean_data.py
│   ├── score_companies.py
│   ├── recommend_actions.py
│   ├── generate_report.py
│   ├── export_word.py
│   └── run_pipeline.py
├── data/
│   ├── input/                   # drop weekly export here
│   └── output/                  # cleaned_data.csv
└── output/                      # dated run folders
```
