"""
clean_data.py
Step 1 of the pipeline: ingest the raw Specter export and produce a clean,
normalised dataframe ready for scoring.

See skills/01_data_cleaning.md for the logic this implements.
"""

import glob
import os
import pandas as pd

# Columns we keep from the ~200-column raw export.
COLUMNS_TO_KEEP = [
    "Company Name", "Domain", "Description", "Industry", "Tech Vertical",
    "Sub-industry", "Growth Stage", "Founded Date", "HQ Location",
    "Operating Status",
    "Total Funding Amount (in USD)", "Last Funding Amount (in USD)",
    "Last Funding Date", "Last Funding Type", "Post Money Valuation (in USD)",
    "Number of Funding Rounds", "Investors", "Lead Investors",
    "Annual Revenue Estimate (in USD)",
    "Founders", "Founder Highlights", "Number of Founders",
    "Employee Count",
    "Employee Monthly Growth3", "Employee Monthly Growth6",
    "Web Visits", "Web Visits Monthly Growth3", "Web Visits Monthly Growth6",
    "Number of Patents", "Awards Count", "Highlights", "Tagline",
]

TEXT_COLS = ["Description", "Founder Highlights", "Highlights", "Tagline",
             "Founders", "Investors", "Lead Investors"]
FUNDING_COLS = ["Total Funding Amount (in USD)", "Last Funding Amount (in USD)",
                "Post Money Valuation (in USD)", "Annual Revenue Estimate (in USD)"]


def find_input_file(input_dir="data/input"):
    """Return the most recently modified xlsx/csv in the input directory."""
    files = glob.glob(os.path.join(input_dir, "*.xlsx")) + \
            glob.glob(os.path.join(input_dir, "*.csv"))
    if not files:
        raise FileNotFoundError(f"No .xlsx or .csv found in {input_dir}")
    return max(files, key=os.path.getmtime)


def load_and_clean(input_path=None, input_dir="data/input",
                   output_dir="data/output"):
    if input_path is None:
        input_path = find_input_file(input_dir)
    print(f"  Reading: {input_path}")

    if input_path.lower().endswith(".csv"):
        df = pd.read_csv(input_path)
    else:
        df = pd.read_excel(input_path)

    # Keep only columns that exist in this export.
    keep = [c for c in COLUMNS_TO_KEEP if c in df.columns]
    df = df[keep].copy()

    # Drop non-active companies.
    if "Operating Status" in df.columns:
        df = df[df["Operating Status"].astype(str).str.strip() == "Active"]

    # Deduplicate on Domain.
    if "Domain" in df.columns:
        df = df.drop_duplicates(subset=["Domain"], keep="first")

    # Normalise funding amounts -> float, nulls -> 0.
    for c in FUNDING_COLS:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0.0)

    # Normalise text fields -> stripped strings, nulls -> "".
    for c in TEXT_COLS:
        if c in df.columns:
            df[c] = df[c].fillna("").astype(str).str.strip()

    # Founded Date -> int year, nulls -> 0.
    if "Founded Date" in df.columns:
        df["Founded Date"] = pd.to_numeric(
            df["Founded Date"], errors="coerce").fillna(0).astype(int)

    # Last Funding Date -> datetime.
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