# Skill: Data Cleaning

## Purpose
Ingest the raw Specter CSV/XLSX export and produce a clean, normalised
dataframe ready for scoring.

## Config section
Edit **`config/pipeline_settings.json`** → **`cleaning`**

| Key | What it controls |
|-----|------------------|
| `columns_to_keep` | Specter columns retained from the ~200-column export |
| `text_columns` | Fields normalised to stripped strings (nulls → empty) |
| `funding_columns` | Amount fields converted to float (nulls → 0) |
| `keep_operating_status` | Only rows with this Operating Status value are kept (e.g. `Active`) |
| `dedupe_column` | Column used to drop duplicate companies (first wins) |
| `stage_mapping` | Optional map from Specter stage labels to standard labels |

## Behavior summary
1. Read the newest `.xlsx` or `.csv` in `data/input/`.
2. Keep only `columns_to_keep` that exist in the file.
3. Drop rows not matching `keep_operating_status`.
4. Deduplicate on `dedupe_column`.
5. Apply `stage_mapping` to Growth Stage when present.
6. Normalise funding, text, founded year, and last funding date.
7. Write `data/output/cleaned_data.csv` for inspection.

## Editing this skill
Open `config/pipeline_settings.json`, edit the `cleaning` section, save, and re-run:

```powershell
python scripts/run_pipeline.py
```

No Python changes required.
