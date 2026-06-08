"""
clean_workspace.py
Reset the workspace so the pipeline can be re-run from scratch (handy for a live
demo of the drop-folder automation).

By default this clears BOTH generated outputs AND the local input copies, so the
next `python scripts/run_pipeline.py` has to pull the export fresh from the
Friedkin_Inbox drop folder - proving the end-to-end automation.

What it removes:
  - every run folder under output/
  - files under data/output/ (e.g. cleaned_data.csv)
  - input files under data/input/ (e.g. the .xlsx/.csv export)

What it never touches:
  - the Friedkin_Inbox drop folder (your source of truth)
  - data/input/archive/ and any .gitkeep placeholders
  - Word copies on the Desktop

Safety: input files are only deleted when the drop folder actually has an export
to re-pull, so a reset can never leave you with no copy of the data. Override
with --force if you really want to clear inputs regardless.

Usage:
    python scripts/clean_workspace.py                 (asks for confirmation)
    python scripts/clean_workspace.py --yes            (no prompt; for a fast demo)
    python scripts/clean_workspace.py --keep-input     (outputs only; keep inputs)
    python scripts/clean_workspace.py --force          (clear inputs even if inbox empty)
"""

import argparse
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from load_settings import load_settings
from clean_data import resolve_drop_folder, _candidates_in, DEFAULT_EXTENSIONS

OUTPUT_DIR = "output"
DATA_OUTPUT_DIR = os.path.join("data", "output")
DATA_INPUT_DIR = os.path.join("data", "input")
PRESERVE_NAMES = {".gitkeep"}


def _files_in(folder):
    """Return files directly in folder, skipping preserved placeholders and dirs."""
    if not os.path.isdir(folder):
        return []
    out = []
    for name in sorted(os.listdir(folder)):
        if name in PRESERVE_NAMES:
            continue
        path = os.path.join(folder, name)
        if os.path.isfile(path):
            out.append(path)
    return out


def _gather_targets(include_input):
    run_folders = []
    if os.path.isdir(OUTPUT_DIR):
        for name in sorted(os.listdir(OUTPUT_DIR)):
            path = os.path.join(OUTPUT_DIR, name)
            if os.path.isdir(path):
                run_folders.append(path)

    data_output_files = _files_in(DATA_OUTPUT_DIR)
    input_files = _files_in(DATA_INPUT_DIR) if include_input else []
    return run_folders, data_output_files, input_files


def _load_settings_safe():
    try:
        return load_settings()
    except Exception:
        return {}


def _drop_folder_candidates(settings):
    """Return (drop_folder, [files ready there]) without raising."""
    try:
        drop = resolve_drop_folder(settings)
    except Exception:
        drop = None
    if not drop:
        return None, []
    exts = tuple(settings.get("input", {}).get("file_extensions", DEFAULT_EXTENSIONS))
    return drop, _candidates_in(drop, exts)


def _report_drop_folder(settings):
    """Tell the user where the next run will pull its input from."""
    drop, pending = _drop_folder_candidates(settings)
    if not drop:
        return
    if pending:
        print(f"Next run will pull from the drop folder: {drop}")
        print(f"  ({len(pending)} file(s) ready there.)")
    else:
        print(f"Drop folder is currently empty: {drop}")
        print("  Add the Specter export there before running the pipeline.")


def main():
    parser = argparse.ArgumentParser(
        description="Reset the workspace (outputs and, by default, local inputs).")
    parser.add_argument("--yes", action="store_true",
                        help="Skip the confirmation prompt.")
    parser.add_argument("--keep-input", action="store_true",
                        help="Only clear generated outputs; leave data/input/ alone.")
    parser.add_argument("--force", action="store_true",
                        help="Clear inputs even if the drop folder has no file to re-pull.")
    args = parser.parse_args()

    settings = _load_settings_safe()
    include_input = not args.keep_input
    run_folders, data_output_files, input_files = _gather_targets(include_input)

    input_blocked = False
    if include_input and input_files and not args.force:
        drop, pending = _drop_folder_candidates(settings)
        if not pending:
            input_blocked = True
            input_files = []

    if not run_folders and not data_output_files and not input_files:
        if input_blocked:
            print("Skipping inputs: the drop folder is empty, so clearing "
                  "data/input/ would leave no copy of the export.")
            drop, _ = _drop_folder_candidates(settings)
            if drop:
                print(f"  Put the export in {drop} first, or re-run with --force.")
        else:
            print("Nothing to clean.")
        return

    print("The following will be removed:")
    for path in run_folders:
        print(f"  [run folder]   {path}")
    for path in data_output_files:
        print(f"  [output file]  {path}")
    for path in input_files:
        print(f"  [input file]   {path}")
    if input_blocked:
        drop, _ = _drop_folder_candidates(settings)
        print("Note: keeping data/input/ - the drop folder is empty, so clearing "
              "it would leave no copy of the export.")
        if drop:
            print(f"  Put the export in {drop} first, or re-run with --force.")
    elif include_input:
        print("The Friedkin_Inbox drop folder, data/input/archive/, and .gitkeep "
              "placeholders are kept.")
    else:
        print("Input files are kept (--keep-input).")

    if not args.yes:
        answer = input("Proceed? [y/N] ").strip().lower()
        if answer != "y":
            print("Aborted. Nothing was removed.")
            return

    for path in run_folders:
        shutil.rmtree(path, ignore_errors=True)
    for path in data_output_files + input_files:
        try:
            os.remove(path)
        except OSError:
            pass

    parts = []
    if run_folders:
        parts.append(f"{len(run_folders)} run folder(s)")
    if data_output_files:
        parts.append(f"{len(data_output_files)} output file(s)")
    if input_files:
        parts.append(f"{len(input_files)} input file(s)")
    print(f"Removed {' and '.join(parts)}.")

    if include_input and not input_blocked:
        print()
        _report_drop_folder(settings)


if __name__ == "__main__":
    main()
