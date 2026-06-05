"""
run_pipeline.py
Single entry point for the whole workflow.

Usage:
    python scripts/run_pipeline.py
    python scripts/run_pipeline.py --input data/input/your_file.xlsx
    python scripts/run_pipeline.py --use-llm     (requires ANTHROPIC_API_KEY)

Steps:
    1. Clean the raw Specter export        (clean_data.py)
    2. Score + rank against criteria       (score_companies.py)
    3. Generate investor brief + CSV       (generate_report.py)
"""

import argparse
import os
import sys

# Allow running from repo root: make sibling modules importable.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from clean_data import load_and_clean
from score_companies import load_config, score_dataframe
from generate_report import generate_report


def main():
    parser = argparse.ArgumentParser(description="Friedkin sourcing pipeline")
    parser.add_argument("--input", default=None,
                        help="Path to a specific Specter export. "
                             "Defaults to newest file in data/input/")
    parser.add_argument("--config", default="config/scoring_weights.json")
    parser.add_argument("--use-llm", action="store_true",
                        help="Use Claude for rationales (needs ANTHROPIC_API_KEY)")
    args = parser.parse_args()

    print("Step 1/3  Cleaning data...")
    cleaned = load_and_clean(input_path=args.input)

    print("Step 2/3  Scoring + ranking...")
    cfg = load_config(args.config)
    ranked = score_dataframe(cleaned, cfg)
    print(f"  {len(ranked)} companies passed the threshold.")

    print("Step 3/3  Generating report...")
    generate_report(ranked, cfg, use_llm=args.use_llm)

    print("\nDone. Top 5:")
    for i, row in ranked.head(5).iterrows():
        print(f"  {i+1}. {row['Company Name']:<28} "
              f"{row['total_score']}% · {row['qualification_tier']}")
    print("\nOpen output/investor_brief.md for the full brief.")


if __name__ == "__main__":
    main()