"""
run_pipeline.py
Single entry point for the Friedkin Specter screening workflow.

Usage:
    python scripts/run_pipeline.py
    python scripts/run_pipeline.py --input data/input/your_file.xlsx
    python scripts/run_pipeline.py --use-llm     (requires ANTHROPIC_API_KEY)
    python scripts/run_pipeline.py --no-word      (skip the Word doc)

Pipeline (4 steps + optional Word export):
  1. clean_data.py       -> skills/01, config cleaning section
  2. score_companies.py  -> skills/02-03, config scoring section
  3. recommend_actions.py -> skills/05, config actions section
  4. generate_report.py  -> skills/04/06, config rationale + report sections

Each run is saved to:  output/<filename>_<date>/
  - scored_companies.csv  (all companies above min_score_threshold)
  - investor_brief.md     (top N from config)
  - investor_brief.docx   (optional; copied to Desktop when found)

Input files stay in data/input/ after each run so you can re-run while tuning config.
data/input/archive/ is optional manual storage only.
"""

import argparse
import datetime
import os
import re
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from clean_data import load_and_clean, find_input_file
from score_companies import score_dataframe, brief_shortlist
from recommend_actions import add_recommendations
from generate_report import generate_report
from export_word import export_to_word
from load_settings import load_settings


def _run_folder_name(input_path):
    stem = os.path.basename(input_path)
    for ext in (".xlsx", ".csv", ".xlsm"):
        if stem.lower().endswith(ext):
            stem = stem[:-len(ext)]
    stem = re.sub(r"[^A-Za-z0-9._-]+", "_", stem).strip("_")
    date = datetime.date.today().isoformat()
    return f"{stem}_{date}"


def _find_desktop():
    home = os.path.expanduser("~")
    for cand in (os.path.join(home, "Desktop"),
                 os.path.join(home, "OneDrive", "Desktop")):
        if os.path.isdir(cand):
            return cand
    return None


def main():
    parser = argparse.ArgumentParser(description="Friedkin sourcing pipeline")
    parser.add_argument("--input", default=None)
    parser.add_argument("--config", default="config/pipeline_settings.json")
    parser.add_argument("--use-llm", action="store_true")
    parser.add_argument("--no-word", action="store_true", help="Skip Word doc generation")
    args = parser.parse_args()

    settings = load_settings(args.config)
    input_path = args.input or find_input_file()
    run_name = _run_folder_name(input_path)
    out_dir = os.path.join("output", run_name)

    print("Step 1/4  Cleaning data...")
    cleaned = load_and_clean(input_path=input_path, settings=settings)

    print("Step 2/4  Scoring + ranking...")
    ranked = score_dataframe(cleaned, settings)
    print(f"  {len(ranked)} companies passed the threshold.")

    print("Step 3/4  Recommending actions...")
    ranked = add_recommendations(ranked, settings)

    print("Step 4/4  Generating report...")
    _, brief = generate_report(ranked, settings, output_dir=out_dir, use_llm=args.use_llm)

    if not args.no_word:
        docx_path = export_to_word(brief, settings, out_dir,
                                   input_name=os.path.basename(input_path))
        print(f"  Wrote {docx_path}")
        desktop = _find_desktop()
        if desktop:
            dest = os.path.join(desktop, f"Friedkin_Sourcing_Brief_{run_name}.docx")
            shutil.copyfile(docx_path, dest)
            print(f"  Copied Word doc to Desktop: {dest}")
        else:
            print("  (Desktop not found - Word doc saved in the run folder only.)")

    print(f"\nRun saved to: {out_dir}")
    print("Top 5 in brief:")
    for i, row in brief.head(5).iterrows():
        print(f"  {i+1}. {row['Company Name']:<28} {row['total_score']:.0f}  "
              f"{row.get('outreach_action', '')}")


if __name__ == "__main__":
    main()
