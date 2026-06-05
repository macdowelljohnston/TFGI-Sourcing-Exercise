# Skills

Each file in this folder is a self-contained module that defines one step
of the pipeline. A non-technical team member can open any file, read the
logic, and edit it without touching any code.

| File | Purpose |
|------|---------|
| `01_data_cleaning.md` | Which columns to keep and how to normalise them |
| `02_qualification_scoring.md` | Scoring rubric and dimension weights |
| `03_founder_assessment.md` | Claude prompt for parsing founder backgrounds |
| `04_screening_summary.md` | Claude prompt for writing investor rationales |

## How to update scoring criteria
1. Open `config/scoring_weights.json`
2. Change the weight values (they must sum to 1.0)
3. Add or remove sectors in `target_sectors`
4. Adjust `min_score_threshold` (0–100) or `score_tiers` for tier labels
5. Re-run: `python scripts/run_pipeline.py`

## How to run on a new CSV
1. Drop the new Specter export into `data/input/`
2. Run: `python scripts/run_pipeline.py`
3. Results appear in `output/`
