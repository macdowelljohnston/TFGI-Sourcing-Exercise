"""
run_pipeline.py
Single entry point for the whole workflow.

Usage:
    python scripts/run_pipeline.py
    python scripts/run_pipeline.py --input data/input/your_file.xlsx
    python scripts/run_pipeline.py --use-llm     (requires ANTHROPIC_API_KEY)
    python scripts/run_pipeline.py --no-word      (skip the Word doc)

Each run is saved to its own folder:  output/<filename>_<date>/
  - investor_brief.md     (readable in Cursor / GitHub)
  - scored_companies.csv  (full data)
  - investor_brief.docx   (Word doc, also copied to your Desktop)

After a successful run, the processed input file is moved into
data/input/archive/ so the drop-zone stays clean for next week.
Re-running the same file on the same day overwrites that run's folder.
"""

import argparse
import datetime
import os
import re
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from clean_data import load_and_clean, find_input_file
from score_companies import load_config, score_dataframe
from recommend_actions import add_recommendations
from generate_report import generate_report
from export_word import export_to_word


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


def _archive_input(input_path, run_name):
    """Move a processed input file into data/input/archive/ (after success).
    Only archives files that live inside data/input/ -- never external paths."""
    input_dir = os.path.join("data", "input")
    abs_input = os.path.abspath(input_path)
    abs_indir = os.path.abspath(input_dir)
    if not abs_input.startswith(abs_indir):
        return None  # external file (e.g. --input from Desktop); leave it alone
    archive_dir = os.path.join(input_dir, "archive")
    os.makedirs(archive_dir, exist_ok=True)
    base = os.path.basename(input_path)
    stem, ext = os.path.splitext(base)
    dest = os.path.join(archive_dir, f"{stem}_{datetime.date.today().isoformat()}{ext}")
    shutil.move(input_path, dest)
    return dest


def main():
    parser = argparse.ArgumentParser(description="Friedkin sourcing pipeline")
    parser.add_argument("--input", default=None)
    parser.add_argument("--config", default="config/scoring_weights.json")
    parser.add_argument("--use-llm", action="store_true")
    parser.add_argument("--no-word", action="store_true",
                        help="Skip Word doc generation")
    args = parser.parse_args()

    input_path = args.input or find_input_file()
    run_name = _run_folder_name(input_path)
    out_dir = os.path.join("output", run_name)

    print("Step 1/4  Cleaning data...")
    cleaned = load_and_clean(input_path=input_path)

    print("Step 2/4  Scoring + ranking...")
    cfg = load_config(args.config)
    ranked = score_dataframe(cleaned, cfg)
    print(f"  {len(ranked)} companies passed the threshold.")

    print("Step 3/4  Recommending actions...")
    ranked = add_recommendations(ranked, cfg)

    print("Step 4/4  Generating report...")
    generate_report(ranked, cfg, output_dir=out_dir, use_llm=args.use_llm)

    if not args.no_word:
        docx_path = export_to_word(ranked, cfg, out_dir,
                                   input_name=os.path.basename(input_path))
        print(f"  Wrote {docx_path}")
        desktop = _find_desktop()
        if desktop:
            dest = os.path.join(desktop, f"Friedkin_Sourcing_Brief_{run_name}.docx")
            shutil.copyfile(docx_path, dest)
            print(f"  Copied Word doc to Desktop: {dest}")
        else:
            print("  (Desktop not found - Word doc saved in the run folder only.)")

    archived = _archive_input(input_path, run_name)
    if archived:
        print(f"  Archived input -> {archived}")

    print(f"\nRun saved to: {out_dir}")
    print("Top 5:")
    for i, row in ranked.head(5).iterrows():
        print(f"  {i+1}. {row['Company Name']:<28} {row['total_score']:.0f}")


if __name__ == "__main__":
    main()
