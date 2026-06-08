"""
generate_report.py
Step 4 of the pipeline: investor brief (Markdown) plus full scored CSV.

See skills/04_screening_summary.md and skills/06_brief_document_standard.md.
Tunable values: pipeline_settings.json -> rationale, report, scoring.
"""

import datetime
import os
import re
import pandas as pd

from load_settings import get_section, scoring_config
from load_skill import load_prompt, fill_prompt
from score_companies import brief_shortlist

_PUNCT = {
    "\u2014": "-", "\u2013": "-", "\u2012": "-", "\u2010": "-",
    "\u2018": "'", "\u2019": "'", "\u201c": '"', "\u201d": '"',
    "\u00b7": "-", "\u2022": "-", "\u2026": "...", "\u00a0": " ",
    "\u00ae": "", "\u2122": "", "\u00a9": "",
}


def _fix_mojibake(s):
    if "â€" in s or "Ã" in s or "â" in s:
        try:
            return s.encode("cp1252", errors="strict").decode("utf-8", errors="strict")
        except (UnicodeEncodeError, UnicodeDecodeError):
            return s
    return s


def clean_text(s):
    s = _fix_mojibake(str(s or ""))
    for bad, good in _PUNCT.items():
        s = s.replace(bad, good)
    return s


def _fmt_usd(x):
    try:
        x = float(x)
    except (TypeError, ValueError):
        return "n/a"
    if x <= 0:
        return "n/a"
    if x >= 1e9:
        return f"${x/1e9:.1f}B"
    if x >= 1e6:
        return f"${x/1e6:.1f}M"
    if x >= 1e3:
        return f"${x/1e3:.0f}K"
    return f"${x:.0f}"


def _fmt_date(d):
    if pd.isna(d):
        return "unknown"
    return pd.Timestamp(d).strftime("%b %Y")


def _clean_domain(row):
    d = str(row.get("Domain", "") or "").strip()
    if not d or d == "nan":
        return ""
    return d.replace("https://", "").replace("http://", "").replace("www.", "").strip("/")


def _matched_sectors(row, target_sectors, cols=None):
    cols = cols or ["Industry", "Tech Vertical", "Sub-industry", "Description", "Tagline"]
    text = " ".join(str(row.get(c, "")) for c in cols).lower()
    return [kw for kw in target_sectors if kw.lower() in text]


# Logical order for funding rounds in the summary (earliest -> latest).
_ROUND_ORDER = [
    "Pre-Seed", "Seed", "Angel",
    "Series A", "Series B", "Series C", "Series D",
    "Series E", "Series F", "Series G", "Series H",
]


def _normalize_round(value):
    """Collapse a raw Last Funding Type to its base round label.

    e.g. 'Series A extension' / 'Series A1' -> 'Series A', 'Pre-seed' -> 'Pre-Seed'.
    Unknown round types are returned cleaned but otherwise unchanged.
    """
    v = clean_text(value).strip()
    if not v or v.lower() == "nan":
        return ""
    low = v.lower()
    for label in _ROUND_ORDER:
        if low.startswith(label.lower()):
            return label
    return v


def _round_sort_key(label):
    return _ROUND_ORDER.index(label) if label in _ROUND_ORDER else len(_ROUND_ORDER)


def build_summary(ranked, scoring_cfg, style):
    """Compute the Portfolio Summary content (shared by md + docx)."""
    tier_order = [clean_text(t["label"]) for t in scoring_cfg.get("score_tiers", [])]
    raw_tiers = ranked["qualification_tier"].apply(clean_text)
    tier_counts = {t: int((raw_tiers == t).sum()) for t in tier_order}
    tier_counts = {t: n for t, n in tier_counts.items() if n > 0}

    sector_tally = {}
    cols = scoring_cfg.get("sector_text_columns")
    for _, row in ranked.iterrows():
        for s in _matched_sectors(row, scoring_cfg["target_sectors"], cols):
            sector_tally[s] = sector_tally.get(s, 0) + 1
    top_sectors = sorted(sector_tally.items(), key=lambda kv: kv[1], reverse=True)
    top_sectors = top_sectors[:style.get("max_sectors_in_summary", 5)]

    round_tally = {}
    for _, row in ranked.iterrows():
        r = _normalize_round(row.get("Last Funding Type"))
        if r:
            round_tally[r] = round_tally.get(r, 0) + 1
    rounds_sorted = sorted(round_tally.items(), key=lambda kv: _round_sort_key(kv[0]))

    n_picks = style.get("top_picks_count", 3)
    picks = [clean_text(r.get("Company Name", "")) for _, r in ranked.head(n_picks).iterrows()]

    return {
        "total": len(ranked),
        "tiers_str": ", ".join(f"{n} {t}" for t, n in tier_counts.items()),
        "sectors_str": ", ".join(f"{k} ({v})" for k, v in top_sectors),
        "stages_str": ", ".join(f"{k} ({v})" for k, v in rounds_sorted),
        "picks_str": ", ".join(picks),
    }


def _oxford(items):
    """Join a list into a natural-language phrase with an Oxford comma."""
    items = [i for i in items if i]
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    if len(items) == 2:
        return f"{items[0]} and {items[1]}"
    return ", ".join(items[:-1]) + f", and {items[-1]}"


def _truncate_prose(text, max_chars):
    """Trim to <= max_chars without cutting mid-word.

    Prefers the last full sentence inside the window; otherwise falls back to the
    last word boundary. Never leaves a dangling ellipsis or a half word.
    """
    text = text.strip()
    if len(text) <= max_chars:
        return text
    window = text[:max_chars]
    end = max(window.rfind(". "), window.rfind("! "), window.rfind("? "))
    if end >= max_chars * 0.5:
        return text[: end + 1].strip()
    space = window.rfind(" ")
    trimmed = (window[:space] if space > 0 else window).rstrip(" ,;:-")
    return trimmed


def _template_rationale(row, rationale_cfg):
    """Deterministic, investor-ready rationale driven by pipeline_settings.json -> rationale."""
    name = clean_text(row.get("Company Name", "This company"))
    max_chars = rationale_cfg.get("max_description_chars", 220)
    desc = clean_text(row.get("Description") or row.get("Tagline") or "").strip()
    desc = _truncate_prose(desc, max_chars) if desc else ""

    if desc:
        if desc.lower().startswith(name.lower()):
            lead = desc
        else:
            lead = f"{name}: {desc[0].upper()}{desc[1:]}"
        if not lead.endswith((".", "!", "?")):
            lead += "."
    else:
        lead = f"{name}."
    parts = [lead]

    if rationale_cfg.get("include_funding_section", True):
        total_funding = _fmt_usd(row.get("Total Funding Amount (in USD)"))
        last_type = clean_text(row.get("Last Funding Type", ""))
        last_date = _fmt_date(row.get("Last Funding Date"))
        fund_bits = []
        if total_funding != "n/a":
            fund_bits.append(f"backed by {total_funding} raised to date")
        if last_type:
            if last_date != "unknown":
                fund_bits.append(f"most recently a {last_type} round in {last_date}")
            else:
                fund_bits.append(f"most recently a {last_type} round")
        if fund_bits:
            sentence = ", ".join(fund_bits)
            parts.append(sentence[0].upper() + sentence[1:] + ".")

    if rationale_cfg.get("include_growth_signals", True):
        emp = row.get("Employee Count", "")
        emp_g = row.get("Employee Monthly Growth6")
        web_g = row.get("Web Visits Monthly Growth6")
        has_emp = emp not in ("", None) and not pd.isna(emp)
        growth_bits = []
        if pd.notna(emp_g):
            growth_bits.append(f"{emp_g:+.0f}% headcount")
        if pd.notna(web_g):
            growth_bits.append(f"{web_g:+.0f}% web traffic")
        if growth_bits:
            sentence = "Over the past six months, " + _oxford(growth_bits) + " growth"
            if has_emp:
                sentence += f", on a base of ~{int(emp)} employees"
            parts.append(sentence + ".")
        elif has_emp:
            parts.append(f"Currently ~{int(emp)} employees.")

    if rationale_cfg.get("include_founder_tags", True):
        tags = clean_text(row.get("Founder Highlights", ""))
        highlight = rationale_cfg.get("founder_tags_to_highlight", [])
        if tags and highlight:
            key_tags = [t.strip() for t in tags.split(",") if t.strip() in highlight]
            if key_tags:
                parts.append("Founder credentials include " + _oxford(key_tags) + ".")

    if rationale_cfg.get("include_score_breakdown", True):
        parts.append(
            f"Qualification score {int(row['total_score'])}/100 "
            f"(Stage {int(row['stage_score'])}, Sector {int(row['sector_score'])}, "
            f"Founder {int(row['founder_score'])}, Momentum {int(row['momentum_score'])})."
        )
    return " ".join(parts)


def _llm_rationale(row, scoring_cfg):
    import anthropic

    template = load_prompt("04_screening_summary.md")
    mapping = {
        "company_name": clean_text(row.get("Company Name", "")),
        "description": clean_text(row.get("Description", "")),
        "growth_stage": clean_text(row.get("Growth Stage", "")),
        "total_funding": _fmt_usd(row.get("Total Funding Amount (in USD)")),
        "last_funding_type": clean_text(row.get("Last Funding Type", "")),
        "last_funding_date": _fmt_date(row.get("Last Funding Date")),
        "founders": clean_text(row.get("Founders", "")),
        "founder_highlights": clean_text(row.get("Founder Highlights", "")),
        "employee_count": row.get("Employee Count", ""),
        "employee_growth_6m": row.get("Employee Monthly Growth6", ""),
        "web_visits": row.get("Web Visits", ""),
        "web_growth_6m": row.get("Web Visits Monthly Growth6", ""),
        "total_score": int(row.get("total_score", 0)),
        "qualification_tier": clean_text(row.get("qualification_tier", "")),
        "stage_score": int(row.get("stage_score", 0)),
        "sector_score": int(row.get("sector_score", 0)),
        "founder_score": int(row.get("founder_score", 0)),
        "momentum_score": int(row.get("momentum_score", 0)),
    }
    prompt = fill_prompt(template, mapping)
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    msg = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=400,
        messages=[{"role": "user", "content": prompt}],
    )
    return clean_text(msg.content[0].text.strip())


def _run_folder_name(input_path):
    stem = os.path.basename(input_path)
    for ext in (".xlsx", ".csv", ".xlsm"):
        if stem.lower().endswith(ext):
            stem = stem[:-len(ext)]
    stem = re.sub(r"[^A-Za-z0-9._-]+", "_", stem).strip("_")
    return f"{stem}_{datetime.date.today().isoformat()}"


def _validate_output_dir(output_dir):
    """All pipeline artifacts must live under output/<run_folder>/, not output/."""
    norm = os.path.normpath(output_dir)
    if norm in ("output", "."):
        raise ValueError(
            "output_dir must be a run subfolder (output/<run_folder>/), not output/"
        )
    parent, leaf = os.path.split(norm)
    if os.path.normpath(parent) != "output" or not leaf:
        raise ValueError(
            f"output_dir must be output/<run_folder>/ (got {output_dir!r})"
        )


def generate_report(ranked_full, settings, output_dir, use_llm=False):
    _validate_output_dir(output_dir)
    os.makedirs(output_dir, exist_ok=True)
    scoring_cfg = scoring_config(settings)
    style = get_section(settings, "report")
    rationale_cfg = get_section(settings, "rationale")

    ranked_full.to_csv(os.path.join(output_dir, "scored_companies.csv"), index=False)
    brief = brief_shortlist(ranked_full, settings)

    title = clean_text(style.get("title", "Weekly Sourcing Brief"))
    subtitle = clean_text(style.get("subtitle", ""))
    min_score = scoring_cfg["min_score_threshold"]

    L = [f"# {title}"]
    if subtitle:
        L.append(f"### {subtitle}")
    L.append("")
    L.append(
        f"Top {len(brief)} qualified companies (minimum score {min_score}). "
        f"Full scored list: {len(ranked_full)} companies in scored_companies.csv."
    )
    L.append("")

    if style.get("show_summary_section", True):
        s = build_summary(brief, scoring_cfg, style)
        L.append("## Portfolio Summary")
        L.append("")
        L.append("| Breakdown | Detail |")
        L.append("|-----------|--------|")
        L.append(f"| Tiers | {s['tiers_str']} |")
        L.append(f"| Sector concentration | {s['sectors_str']} |")
        L.append(f"| Funding rounds | {s['stages_str']} |")
        L.append("")
        L.append(f"**Top picks:** {s['picks_str']}")
        L.append("")
    L.append("---")
    L.append("")

    for i, row in brief.iterrows():
        tier = clean_text(row.get("qualification_tier", ""))
        name = clean_text(row.get("Company Name", ""))
        header = f"## {i+1}. {name}  |  Score {int(row['total_score'])}"
        if tier:
            header += f"  ({tier})"
        L.append(header)
        meta = " | ".join(x for x in [
            clean_text(row.get("Growth Stage", "")),
            clean_text(row.get("Industry", "")),
            clean_text(row.get("HQ Location", "")),
        ] if x and x != "nan")
        if meta:
            L.append(f"*{meta}*")
        dom = _clean_domain(row)
        if dom:
            L.append(f"**Website:** [{dom}](https://{dom})")
        L.append("")
        if use_llm:
            L.append(_llm_rationale(row, scoring_cfg))
        else:
            L.append(_template_rationale(row, rationale_cfg))
        L.append("")
        if "outreach_action" in row and pd.notna(row.get("outreach_action")):
            L.append(
                f"**Action:** {clean_text(row['outreach_action'])}. "
                f"{clean_text(row.get('timing_note', ''))}"
            )
            L.append("")
            steps = clean_text(row.get("diligence_steps", "")).split(" | ")
            if steps and steps[0]:
                L.append("**Diligence:**")
                for st in steps:
                    L.append(f"- {st}")
                L.append("")

    md_path = os.path.join(output_dir, "investor_brief.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(L))

    print(f"  Wrote {os.path.join(output_dir, 'scored_companies.csv')} ({len(ranked_full)} rows)")
    print(f"  Wrote {md_path} ({len(brief)} companies in brief)")
    return md_path, brief


if __name__ == "__main__":
    from clean_data import find_input_file, load_and_clean
    from score_companies import score_dataframe
    from recommend_actions import add_recommendations
    from load_settings import load_settings

    settings = load_settings()
    input_path = find_input_file()
    out_dir = os.path.join("output", _run_folder_name(input_path))
    ranked = add_recommendations(
        score_dataframe(load_and_clean(input_path=input_path, settings=settings), settings),
        settings,
    )
    generate_report(ranked, settings, output_dir=out_dir)
