"""
clean_data.py
Step 1 of the pipeline: ingest the raw Specter export and produce a clean,
normalised dataframe ready for scoring.

See skills/01_data_cleaning.md. Tunable values: pipeline_settings.json -> cleaning.
"""

import glob
import os
import shutil
import pandas as pd

from load_settings import load_settings, get_section

DEFAULT_EXTENSIONS = (".xlsx", ".csv", ".xlsm")


def _resolve_desktop():
    """Return the user's Desktop path (handles OneDrive-redirected Desktop)."""
    home = os.path.expanduser("~")
    for cand in (os.path.join(home, "Desktop"),
                 os.path.join(home, "OneDrive", "Desktop")):
        if os.path.isdir(cand):
            return cand
    return os.path.join(home, "Desktop")


def resolve_drop_folder(settings=None):
    """Resolve the external drop folder from env var or config.

    Resolution order: env var (from config.input.drop_folder_env_var) >
    config.input.drop_folder. A relative path is resolved against the Desktop so
    the repo stays portable (no hardcoded personal absolute path). Returns the
    absolute path, creating it when auto_create_drop_folder is set.
    """
    cfg = (settings or {}).get("input", {}) if settings else {}
    env_var = cfg.get("drop_folder_env_var", "FRIEDKIN_INBOX")
    configured = os.environ.get(env_var) or cfg.get("drop_folder")
    if not configured:
        return None

    if os.path.isabs(configured):
        folder = configured
    else:
        rel = configured.replace("\\", "/")
        if rel.lower().startswith("desktop/"):
            rel = rel[len("desktop/"):]
        folder = os.path.join(_resolve_desktop(), rel)

    if cfg.get("auto_create_drop_folder", True):
        os.makedirs(folder, exist_ok=True)
    return folder


def _candidates_in(folder, extensions):
    """Return all files in folder matching any of the given extensions."""
    if not folder or not os.path.isdir(folder):
        return []
    files = []
    for ext in extensions:
        files.extend(glob.glob(os.path.join(folder, f"*{ext}")))
    return files


def _newest_in(folder, extensions):
    files = _candidates_in(folder, extensions)
    return max(files, key=os.path.getmtime) if files else None


def find_input_file(input_dir="data/input", settings=None, inbox=None):
    """Return the input file to process, searching the drop folder then the repo.

    Search order: explicit ``inbox`` folder > configured external drop folder >
    repo ``input_dir``. When a file is found outside ``input_dir`` and
    ``input.copy_to_repo`` is set, it is copied into ``input_dir`` (for
    reproducibility) and the repo copy path is returned.
    """
    cfg = (settings or {}).get("input", {}) if settings else {}
    extensions = tuple(cfg.get("file_extensions", DEFAULT_EXTENSIONS))
    repo_input_dir = cfg.get("repo_input_dir", input_dir)

    drop_folder = inbox or resolve_drop_folder(settings)

    search_dirs = []
    if drop_folder:
        search_dirs.append(drop_folder)
    search_dirs.append(repo_input_dir)

    chosen = None
    chosen_files = []
    for folder in search_dirs:
        files = _candidates_in(folder, extensions)
        if files:
            chosen_files = files
            chosen = max(files, key=os.path.getmtime)
            break

    if len(chosen_files) > 1:
        folder = os.path.dirname(chosen)
        ordered = sorted(chosen_files, key=os.path.getmtime, reverse=True)
        print(f"  Warning: {len(chosen_files)} candidate files found in {folder}:")
        for f in ordered:
            marker = "  <- using (most recently modified)" if f == chosen else ""
            print(f"    - {os.path.basename(f)}{marker}")
        print('  Keep only one file here, or choose explicitly with '
              '--input "<path>".')

    if not chosen:
        archive_dir = os.path.join(repo_input_dir, "archive")
        archived = _newest_in(archive_dir, extensions)
        hint = "No input file found.\n"
        if drop_folder:
            hint += f"  Drop a Specter export into {drop_folder}\n"
        hint += f"  or into {repo_input_dir}/ and run again."
        if archived:
            hint += (
                f"\n  Or point at a copy in archive/:\n"
                f'    python scripts/run_pipeline.py --input "{archived}"'
            )
        raise FileNotFoundError(hint)

    chosen_dir = os.path.normpath(os.path.dirname(chosen))
    if cfg.get("copy_to_repo", False) and chosen_dir != os.path.normpath(repo_input_dir):
        os.makedirs(repo_input_dir, exist_ok=True)
        dest = os.path.join(repo_input_dir, os.path.basename(chosen))
        shutil.copyfile(chosen, dest)
        print(f"  Picked up from drop folder: {chosen}")
        print(f"  Copied into {repo_input_dir}/")
        return dest

    return chosen


def load_and_clean(input_path=None, input_dir="data/input",
                   output_dir="data/output", settings=None):
    if settings is None:
        settings = load_settings()
    cfg = get_section(settings, "cleaning")

    if input_path is None:
        input_path = find_input_file(input_dir, settings=settings)
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
