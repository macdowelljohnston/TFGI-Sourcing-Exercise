"""
generate_report.py
Step 3 of the pipeline: turn the ranked dataframe into an investor-ready
brief (Markdown) plus a scored CSV.

By default this builds a deterministic, data-grounded rationale for each
company (no API key required -- safe for live demos). If you set the
ANTHROPIC_API_KEY environment variable and pass use_llm=True, it will
instead call Claude using the prompt in skills/04_screening_summary.md.

See skills/04_screening_summary.md for the prompt this implements.
"""

import os
import pandas as pd


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


def _template_rationale(row):
    """Deterministic, specific rationale grounded in the actual data."""
    name = row.get("Company Name", "This company")
    desc = (row.get("Description") or row.get("Tagline") or "").strip()
    # Avoid "Name — Name builds..." repetition.
    if desc.lower().startswith(str(name).lower()):
        desc = desc[len(str(name)):].lstrip(" -—:,").strip()
        desc = desc[0].upper() + desc[1:] if desc else desc
    if len(desc) > 220:
        desc = desc[:217].rstrip() + "..."

    total_funding = _fmt_usd(row.get("Total Funding Amount (in USD)"))
    last_type = row.get("Last Funding Type", "")
    last_date = _fmt_date(row.get("Last Funding Date"))
    emp = row.get("Employee Count", "")
    emp_g = row.get("Employee Monthly Growth6")
    web_g = row.get("Web Visits Monthly Growth6")
    tags = row.get("Founder Highlights", "")

    parts = []
    if desc:
        parts.append(f"{name} — {desc}")
    else:
        parts.append(f"{name}.")

    fund_bits = []
    if total_funding != "n/a":
        fund_bits.append(f"has raised {total_funding} to date")
    if last_type:
        fund_bits.append(f"most recently a {last_type} round ({last_date})")
    if fund_bits:
        parts.append("It " + " — ".join(fund_bits) + ".")

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
        key_tags = [t.strip() for t in str(tags).split(",")
                    if t.strip() in ("Prior Exit", "Prior IPO", "Serial Founder",
                                     "Unicorn Experience", "Top University")]
        if key_tags:
            parts.append("Founder signal: " + ", ".join(key_tags) + ".")

    parts.append(
        f"Stage {row['stage_score']}% | Sector {row['sector_score']}% | "
        f"Founder {row['founder_score']}% | Momentum {row['momentum_score']}%.")
    return " ".join(parts)


def _llm_rationale(row):
    """Optional: call Claude using the screening_summary prompt."""
    import anthropic
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    prompt = f"""You are a senior analyst at a venture capital firm focused on
Transportation, Manufacturing, Physical AI, Automotive, and Aerospace & Defense.

Write a 3-5 sentence investor rationale for {row.get('Company Name')}.
Be specific, reference the actual data, no generic VC language.

- Description: {row.get('Description')}
- Stage: {row.get('Growth Stage')}
- Total Funding: {_fmt_usd(row.get('Total Funding Amount (in USD)'))}
- Last Funding: {row.get('Last Funding Type')} ({_fmt_date(row.get('Last Funding Date'))})
- Founder Highlights: {row.get('Founder Highlights')}
- Employee Count: {row.get('Employee Count')}
- Employee 6mo Growth: {row.get('Employee Monthly Growth6')}
- Web 6mo Growth: {row.get('Web Visits Monthly Growth6')}
- Score: {row.get('total_score')}/100 ({row.get('qualification_tier', 'n/a')})

Return only the rationale paragraph."""
    msg = client.messages.create(
        model="claude-sonnet-4-20250514", max_tokens=400,
        messages=[{"role": "user", "content": prompt}])
    return msg.content[0].text.strip()


def generate_report(ranked, config, output_dir="output", use_llm=False):
    os.makedirs(output_dir, exist_ok=True)

    csv_path = os.path.join(output_dir, "scored_companies.csv")
    ranked.to_csv(csv_path, index=False)

    lines = []
    lines.append("# Friedkin — Weekly Sourcing Brief")
    lines.append("")
    lines.append(f"Generated from the latest Specter export. "
                 f"Showing the top {len(ranked)} qualified companies "
                 f"(min score {config['min_score_threshold']}%).")
    lines.append("")
    lines.append("**Active weights:** " + ", ".join(
        f"{k} {int(v * 100)}%" for k, v in config["weights"].items()))
    lines.append("")
    lines.append("---")
    lines.append("")

    tier_order = list(dict.fromkeys(ranked["qualification_tier"].tolist()))
    rank_num = 0
    for tier_label in tier_order:
        tier_rows = ranked[ranked["qualification_tier"] == tier_label]
        if len(tier_rows) == 0:
            continue
        lines.append(f"### {tier_label}")
        lines.append("")
        for _, row in tier_rows.iterrows():
            rank_num += 1
            rationale = _llm_rationale(row) if use_llm else _template_rationale(row)
            tier = row.get("qualification_tier", "")
            lines.append(f"## {rank_num}. {row.get('Company Name')}  "
                         f"— {row['total_score']}% · {tier}")
            loc = row.get("HQ Location", "")
            ind = row.get("Industry", "")
            meta = " · ".join(x for x in [str(row.get('Growth Stage', '')), str(ind), str(loc)] if x and x != "nan")
            if meta:
                lines.append(f"*{meta}*")
            lines.append("")
            lines.append(rationale)
            lines.append("")

    md_path = os.path.join(output_dir, "investor_brief.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"  Wrote {csv_path}")
    print(f"  Wrote {md_path}")
    return md_path


if __name__ == "__main__":
    from clean_data import load_and_clean
    from score_companies import load_config, score_dataframe
    cfg = load_config()
    ranked = score_dataframe(load_and_clean(), cfg)
    generate_report(ranked, cfg)