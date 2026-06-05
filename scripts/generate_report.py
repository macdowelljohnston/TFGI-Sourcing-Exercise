"""
generate_report.py
Step 3 of the pipeline: turn the ranked dataframe into an investor-ready
brief (Markdown) plus a scored CSV. Follows skills/06_brief_document_standard.md.

All generated text is normalised to plain ASCII punctuation (no smart quotes,
no em-dashes) and written as UTF-8, so the output never shows mojibake.
build_summary() is the single source of the summary content (md + docx).
"""

import os
import pandas as pd

_PUNCT = {
    "\u2014": "-", "\u2013": "-", "\u2012": "-", "\u2010": "-",
    "\u2018": "'", "\u2019": "'", "\u201c": '"', "\u201d": '"',
    "\u00b7": "-", "\u2022": "-", "\u2026": "...", "\u00a0": " ",
    "\u00ae": "", "\u2122": "", "\u00a9": "",
}


def _fix_mojibake(s):
    """Reverse classic UTF-8-read-as-cp1252 corruption (e.g. 'â€™' -> apostrophe)."""
    if "â€" in s or "Ã" in s or "â" in s:
        try:
            return s.encode("cp1252", errors="strict").decode("utf-8", errors="strict")
        except (UnicodeEncodeError, UnicodeDecodeError):
            return s
    return s


def clean_text(s):
    """Repair mojibake, then normalise any unicode punctuation to plain ASCII."""
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


def _matched_sectors(row, target_sectors):
    text = " ".join(str(row.get(c, "")) for c in
                    ["Industry", "Tech Vertical", "Sub-industry", "Description", "Tagline"]).lower()
    return [kw for kw in target_sectors if kw.lower() in text]


def build_summary(ranked, config, style):
    """Compute the Portfolio Summary content (shared by md + docx)."""
    total = len(ranked)

    tier_order = [clean_text(t["label"]) for t in config.get("score_tiers", [])]
    raw_tiers = ranked["qualification_tier"].apply(clean_text)
    tier_counts = {t: int((raw_tiers == t).sum()) for t in tier_order}
    tier_counts = {t: n for t, n in tier_counts.items() if n > 0}

    sector_tally = {}
    for _, row in ranked.iterrows():
        for s in _matched_sectors(row, config["target_sectors"]):
            sector_tally[s] = sector_tally.get(s, 0) + 1
    top_sectors = sorted(sector_tally.items(), key=lambda kv: kv[1], reverse=True)
    top_sectors = top_sectors[:style.get("max_sectors_in_summary", 5)]

    stage_counts = ranked["Growth Stage"].value_counts().to_dict()

    n_picks = style.get("top_picks_count", 3)
    picks = [clean_text(r.get("Company Name", "")) for _, r in ranked.head(n_picks).iterrows()]

    return {
        "total": total,
        "tiers_str": ", ".join(f"{n} {t}" for t, n in tier_counts.items()),
        "sectors_str": ", ".join(f"{k} ({v})" for k, v in top_sectors),
        "stages_str": ", ".join(f"{k} ({v})" for k, v in stage_counts.items()),
        "picks_str": ", ".join(picks),
    }


def _template_rationale(row):
    """Deterministic, specific rationale grounded in the actual data (ASCII)."""
    name = clean_text(row.get("Company Name", "This company"))
    desc = clean_text(row.get("Description") or row.get("Tagline") or "").strip()
    if desc.lower().startswith(name.lower()):
        desc = desc[len(name):].lstrip(" -:,").strip()
        desc = desc[0].upper() + desc[1:] if desc else desc
    if len(desc) > 220:
        desc = desc[:217].rstrip() + "..."

    total_funding = _fmt_usd(row.get("Total Funding Amount (in USD)"))
    last_type = clean_text(row.get("Last Funding Type", ""))
    last_date = _fmt_date(row.get("Last Funding Date"))
    emp = row.get("Employee Count", "")
    emp_g = row.get("Employee Monthly Growth6")
    web_g = row.get("Web Visits Monthly Growth6")
    tags = clean_text(row.get("Founder Highlights", ""))

    parts = [f"{name}. {desc}" if desc else f"{name}."]

    fund_bits = []
    if total_funding != "n/a":
        fund_bits.append(f"has raised {total_funding} to date")
    if last_type:
        fund_bits.append(f"most recently a {last_type} round ({last_date})")
    if fund_bits:
        parts.append("It " + ", ".join(fund_bits) + ".")

    growth_bits = []
    if pd.notna(emp_g):
        growth_bits.append(f"{emp_g:+.0f}% headcount growth (6mo)")
    if pd.notna(web_g):
        growth_bits.append(f"{web_g:+.0f}% web traffic growth (6mo)")
    if emp not in ("", None) and not pd.isna(emp):
        growth_bits.append(f"~{int(emp)} employees")
    if growth_bits:
        parts.append("Signals: " + ", ".join(growth_bits) + ".")

    if tags:
        key_tags = [t.strip() for t in tags.split(",")
                    if t.strip() in ("Prior Exit", "Prior IPO", "Serial Founder",
                                     "Unicorn Experience", "Top University")]
        if key_tags:
            parts.append("Founder signal: " + ", ".join(key_tags) + ".")

    parts.append(
        f"Scores: Stage {int(row['stage_score'])}, Sector {int(row['sector_score'])}, "
        f"Founder {int(row['founder_score'])}, Momentum {int(row['momentum_score'])}.")
    return " ".join(parts)


def _llm_rationale(row):
    import anthropic
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    prompt = f"""You are a senior analyst at a venture capital firm focused on
Transportation, Manufacturing, Physical AI, Automotive, and Aerospace & Defense.
Write a 3-5 sentence investor rationale for {row.get('Company Name')}.
Be specific, reference the actual data, no generic VC language, no em-dashes.

- Description: {row.get('Description')}
- Stage: {row.get('Growth Stage')}
- Total Funding: {_fmt_usd(row.get('Total Funding Amount (in USD)'))}
- Last Funding: {row.get('Last Funding Type')} ({_fmt_date(row.get('Last Funding Date'))})
- Founder Highlights: {row.get('Founder Highlights')}
- Score: {row.get('total_score')}/100

Return only the rationale paragraph."""
    msg = client.messages.create(model="claude-sonnet-4-20250514", max_tokens=400,
                                 messages=[{"role": "user", "content": prompt}])
    return clean_text(msg.content[0].text.strip())


def _load_style(path="config/report_style.json"):
    import json
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


def generate_report(ranked, config, output_dir="output", use_llm=False):
    os.makedirs(output_dir, exist_ok=True)
    style = _load_style()

    ranked.to_csv(os.path.join(output_dir, "scored_companies.csv"), index=False)

    title = clean_text(style.get("title", "Weekly Sourcing Brief"))
    subtitle = clean_text(style.get("subtitle", ""))

    L = [f"# {title}"]
    if subtitle:
        L.append(f"### {subtitle}")
    L.append("")
    L.append(f"Top {len(ranked)} qualified companies (minimum score {config['min_score_threshold']}).")
    L.append("")

    if style.get("show_summary_section", True):
        s = build_summary(ranked, config, style)
        L.append("## Portfolio Summary")
        L.append("")
        L.append("| Breakdown | Detail |")
        L.append("|-----------|--------|")
        L.append(f"| Tiers | {s['tiers_str']} |")
        L.append(f"| Sector concentration | {s['sectors_str']} |")
        L.append(f"| Stages | {s['stages_str']} |")
        L.append("")
        L.append(f"**Top picks:** {s['picks_str']}")
        L.append("")
    L.append("---")
    L.append("")

    for i, row in ranked.iterrows():
        tier = clean_text(row.get("qualification_tier", ""))
        name = clean_text(row.get("Company Name", ""))
        header = f"## {i+1}. {name}  |  Score {int(row['total_score'])}"
        if tier:
            header += f"  ({tier})"
        L.append(header)
        meta = " | ".join(x for x in [clean_text(row.get('Growth Stage', '')),
                                       clean_text(row.get('Industry', '')),
                                       clean_text(row.get('HQ Location', ''))]
                          if x and x != "nan")
        if meta:
            L.append(f"*{meta}*")
        dom = _clean_domain(row)
        if dom:
            L.append(f"**Website:** [{dom}](https://{dom})")
        L.append("")
        L.append(_llm_rationale(row) if use_llm else _template_rationale(row))
        L.append("")
        if "outreach_action" in row and pd.notna(row.get("outreach_action")):
            L.append(f"**Action:** {clean_text(row['outreach_action'])}. {clean_text(row.get('timing_note', ''))}")
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

    print(f"  Wrote {os.path.join(output_dir, 'scored_companies.csv')}")
    print(f"  Wrote {md_path}")
    return md_path


if __name__ == "__main__":
    from clean_data import load_and_clean
    from score_companies import load_config, score_dataframe
    cfg = load_config()
    ranked = score_dataframe(load_and_clean(), cfg)
    generate_report(ranked, cfg)
