# TFGI Sourcing Pipeline — Specter Company Screening

A repeatable weekly process that ingests a Specter export, qualifies and ranks each company against The Friedkin Group's investment criteria, and produces an investor-ready shortlist with a rationale for each name.

The pipeline is **deterministic and reproducible**: the same export always yields the same brief, and a new export reproduces a full run end to end. It is designed to be **run every week** when a fresh export arrives, and to be **tuned by a non-technical team member** entirely through one configuration file — no code changes required.

---

## Quick start

```powershell
# 1. Install dependencies (once)
pip install -r requirements.txt

# 2. Drop the latest Specter export into data/input/

# 3. Run
python scripts/run_pipeline.py
```

Results appear in `output/<filename>_<date>/`:
- `scored_companies.csv` — all companies above the score threshold
- `investor_brief.md` — top N ranked names with rationale and actions
- `investor_brief.docx` — Word version (also copied to Desktop when found)

---

## The weekly process

The pipeline is built to run on a new Specter export each week. Every run is
self-contained and reproducible.

1. **Add the export.** Drop the new Specter file into `data/input/`. The newest
   file is selected automatically, or pass one explicitly with
   `--input path/to/file.xlsx`.
2. **Run the pipeline.** `python scripts/run_pipeline.py`.
3. **Review the brief.** Open `output/<latest_run>/investor_brief.md` (or the
   `.docx`).

Each run writes to its own dated folder under `output/`, so prior weeks are
preserved and runs never overwrite each other. Input files remain in
`data/input/` after a run; move older exports to `data/input/archive/` only if
you want to keep that folder tidy.

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

Every company gets four sub-scores (0-100), combined using `scoring.weights`:

| Dimension | What it measures |
|-----------|------------------|
| **Stage fit** | Target stages (Early / Growth) vs partial credit for others |
| **Sector alignment** | Keyword match on industry and description |
| **Founder signal** | Specter founder tags (Prior Exit, Serial Founder, etc.) |
| **Growth momentum** | Headcount + web growth + funding recency |

```
total_score = round(100 x (stage*w1 + sector*w2 + founder*w3 + momentum*w4))
```

Tier labels come from `scoring.score_tiers` (default: Tier 1 at 90+, Tier 2 at 75+, Tier 3 at 60+). Companies below `min_score_threshold` (default 75) are excluded.

---

## How to update the system (no code required)

**All tuning is in one file: `config/pipeline_settings.json`.**

| To do this... | Edit this section |
|---------------|-------------------|
| Change columns or filters | `cleaning` |
| Re-weight dimensions | `scoring.weights` (must sum to 1.0) |
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

For a plain-English explanation of every config setting — including the less obvious ones — see [config/README.md](config/README.md).

### Live walkthrough

Every business rule lives in **`config/pipeline_settings.json`**. To see a change
take effect, edit the config and re-run:

```powershell
python scripts/run_pipeline.py
```

Keep the current Specter file in `data/input/` and re-run after each config edit.
The table below maps common adjustments to where they live and what to verify
afterward — useful for a live walkthrough or for validating a tuning change.

| To change... | Config path | Effect | Where to verify after re-run |
|--------------|-------------|--------|------------------------------|
| **Scoring weight** | `scoring.weights` (must sum to 1.0) | Re-orders top 15 in the brief | Terminal Top 5 + `output/<run>/investor_brief.md` |
| **Sector** | `scoring.target_sectors` | Changes sector score and sector summary | `scored_companies.csv` sorted by `sector_score` |
| **Filter** | `scoring.min_score_threshold` (e.g. raise from `75` to `80`) or `scoring.target_stages` | Fewer/more qualified companies | Terminal: `N companies passed the threshold` |
| Outreach tiers (bonus) | `actions.reach_out_threshold` | Tier 1 vs Tier 2 action lines | `Action:` lines in the brief |

**Example adjustment:** in `scoring.weights`, change `founder_signal` from `0.40` to `0.20` and `growth_momentum` from `0.30` to `0.50` (keep `stage_fit` and `sector_alignment` at `0.15` each — weights still sum to 1.0). This shifts emphasis from founder pedigree to growth signals and visibly reorders the Top 5: companies like Filics (+100% headcount, +457% web) move up, while companies that scored mainly on founder tags drop. Re-run and compare the Top 5 in the terminal and `output/<run>/investor_brief.md`.

Add `--no-word` to skip the Word document for a faster run. If `data/input/` is empty, drop a Specter export there, or pass `--input path/to/file.xlsx`.

---

## API integrations

The pipeline runs fully offline by default — scoring, founder tags, rationales,
and actions are all deterministic and require no external services. API keys are
**optional enhancements**, configured through a local `.env` file.

To set keys up, copy the template and fill in the values you have:

```powershell
copy .env.example .env
```

`.env` is gitignored and never committed. `.env.example` lists every key the
pipeline can use.

### Available today

- **`ANTHROPIC_API_KEY`** — enables LLM-written rationales in place of the
  deterministic template:

```powershell
python scripts/run_pipeline.py --use-llm
```

  Uses the prompt in `skills/04_screening_summary.md`. The default run (without
  `--use-llm`) uses the built-in template rationale and needs no key.

### Planned enhancements

We intend to add further integrations as keys become available, to enrich the
screen without changing the core workflow — for example a data-enrichment
provider for fuller founder and traction data, and a news/signals API for
recent-event context. These are placeholders in `.env.example` today and are not
yet wired into the pipeline.

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
│   └── README.md                # plain-English config reference
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
├── output/                      # dated run folders
├── requirements.txt             # pinned dependencies
├── .env.example                 # optional API keys (copy to .env)
└── LICENSE                      # confidential / internal use
```

---

## License

Confidential. Prepared for The Friedkin Group for internal use only. Not for
redistribution. See [LICENSE](LICENSE).
