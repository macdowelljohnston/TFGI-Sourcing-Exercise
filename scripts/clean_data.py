"""
clean_data.py
Step 1 of the pipeline: ingest the raw Specter export and produce a clean,
normalised dataframe ready for scoring.

See skills/01_data_cleaning.md. Tunable values: pipeline_settings.json -> cleaning.
"""

import glob
import os
import pandas as pd

from load_settings import load_settings, get_section


def find_input_file(input_dir="data/input"):
    """Return the most recently modified xlsx/csv in the input directory."""
    files = glob.glob(os.path.join(input_dir, "*.xlsx")) + \
            glob.glob(os.path.join(input_dir, "*.csv"))
    if not files:
        archive_dir = os.path.join(input_dir, "archive")
        archived = glob.glob(os.path.join(archive_dir, "*.xlsx")) + \
                   glob.glob(os.path.join(archive_dir, "*.csv"))
        hint = f"No .xlsx or .csv found in {input_dir}.\n"
        hint += f"  Drop a Specter export into {input_dir}/ and run again."
        if archived:
            newest = max(archived, key=os.path.getmtime)
            hint += (
                f"\n  Or point at a copy in archive/:\n"
                f'    python scripts/run_pipeline.py --input "{newest}"'
            )
        raise FileNotFoundError(hint)
    return max(files, key=os.path.getmtime)


def load_and_clean(input_path=None, input_dir="data/input",
                   output_dir="data/output", settings=None):
    if settings is None:
        settings = load_settings()
    cfg = get_section(settings, "cleaning")

    if input_path is None:
        input_path = find_input_file(input_dir)
    print(f"  Reading: {input_path}")

    if input_path.lower().endswith(".csv"):
        df = pd.read_csv(input_path)
    else:
        df = pd.read_excel(input_path)

    keep = [c for c in cfg["columns_to_keep"] if c in df.columns]
    df = df[keep].copy()

    status_col = "Operating Status"
    keep_status = cfg.get("keep_operating_status")
    if keep_status and status_col in df.columns:
        df = df[df[status_col].astype(str).str.strip() == keep_status]

    dedupe_col = cfg.get("dedupe_column")
    if dedupe_col and dedupe_col in df.columns:
        df = df.drop_duplicates(subset=[dedupe_col], keep="first")

    stage_col = "Growth Stage"
    mapping = cfg.get("stage_mapping") or {}
    if mapping and stage_col in df.columns:
        df[stage_col] = df[stage_col].astype(str).str.strip().replace(mapping)

    for c in cfg.get("funding_columns", []):
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0.0)

    for c in cfg.get("text_columns", []):
        if c in df.columns:
            df[c] = df[c].fillna("").astype(str).str.strip()

    if "Founded Date" in df.columns:
        df["Founded Date"] = pd.to_numeric(
            df["Founded Date"], errors="coerce").fillna(0).astype(int)

    if "Last Funding Date" in df.columns:
        df["Last Funding Date"] = pd.to_datetime(
            df["Last Funding Date"], errors="coerce")

    df = df.reset_index(drop=True)

    os.makedirs(output_dir, exist_ok=True)
    out_path = os.path.join(output_dir, "cleaned_data.csv")
    df.to_csv(out_path, index=False)
    print(f"  Cleaned {len(df)} companies -> {out_path}")
    return df


if __name__ == "__main__":
    load_and_clean()
