"""
export_word.py
Optional output step: render the ranked shortlist as a polished Word
document (.docx) that can be emailed directly to the investment team.

Uses python-docx (pure Python, no external tools). The same data that
feeds investor_brief.md feeds this, so the Word doc always matches.
"""

import os
from docx import Document
from docx.shared import Pt, RGBColor

from docx.oxml import OxmlElement
from docx.oxml.ns import qn

from generate_report import _template_rationale, _website_url


def _add_hyperlink(paragraph, text, url):
    part = paragraph.part
    r_id = part.relate_to(
        url,
        "http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink",
        is_external=True,
    )
    hyperlink = OxmlElement("w:hyperlink")
    hyperlink.set(qn("r:id"), r_id)
    run = OxmlElement("w:r")
    r_pr = OxmlElement("w:rPr")
    color = OxmlElement("w:color")
    color.set(qn("w:val"), "0563C1")
    r_pr.append(color)
    underline = OxmlElement("w:u")
    underline.set(qn("w:val"), "single")
    r_pr.append(underline)
    run.append(r_pr)
    text_el = OxmlElement("w:t")
    text_el.text = text
    run.append(text_el)
    hyperlink.append(run)
    paragraph._p.append(hyperlink)


def _set_font(run, size=11, bold=False, color=None):
    run.font.name = "Arial"
    run.font.size = Pt(size)
    run.font.bold = bold
    if color:
        run.font.color.rgb = RGBColor(*color)


def export_to_word(ranked, config, output_dir, input_name=""):
    doc = Document()
    doc.styles["Normal"].font.name = "Arial"
    doc.styles["Normal"].font.size = Pt(11)

    # Title
    h = doc.add_heading(level=0)
    r = h.add_run("Friedkin — Weekly Sourcing Brief")
    _set_font(r, size=22, bold=True, color=(0x1F, 0x3A, 0x5F))

    # Subheader
    p = doc.add_paragraph()
    src = f" Source file: {input_name}." if input_name else ""
    r = p.add_run(f"Top {len(ranked)} qualified companies "
                  f"(min score {config['min_score_threshold']}).{src}")
    _set_font(r, size=10, color=(0x60, 0x60, 0x60))

    p = doc.add_paragraph()
    r = p.add_run("Active weights: " + ", ".join(
        f"{k} {v}" for k, v in config["weights"].items()))
    _set_font(r, size=10, color=(0x60, 0x60, 0x60))

    doc.add_paragraph("")

    for i, row in ranked.iterrows():
        # Company heading with score + tier
        tier = row.get("qualification_tier", "")
        head = doc.add_heading(level=1)
        r = head.add_run(f"{i+1}. {row.get('Company Name')}  —  score {int(row['total_score'])}")
        _set_font(r, size=15, bold=True, color=(0x1F, 0x3A, 0x5F))
        if tier:
            r2 = head.add_run(f"   ·   {tier}")
            _set_font(r2, size=11, bold=False, color=(0x60, 0x60, 0x60))

        # Meta line
        meta = " · ".join(x for x in [str(row.get("Growth Stage", "")),
                                      str(row.get("Industry", "")),
                                      str(row.get("HQ Location", ""))]
                          if x and x != "nan")
        if meta:
            p = doc.add_paragraph()
            r = p.add_run(meta)
            _set_font(r, size=9, color=(0x88, 0x88, 0x88))
            r.italic = True

        url = _website_url(row.get("Domain"))
        if url:
            p = doc.add_paragraph()
            _set_font(p.add_run("Website: "), size=10, bold=True)
            display = url.removeprefix("https://").removeprefix("http://")
            _add_hyperlink(p, display, url)

        # Rationale
        p = doc.add_paragraph()
        _set_font(p.add_run(_template_rationale(row)), size=11)

        # Action
        if "outreach_action" in row:
            p = doc.add_paragraph()
            _set_font(p.add_run("Action: "), size=11, bold=True)
            _set_font(p.add_run(f"{row['outreach_action']} — {row.get('timing_note', '')}"), size=11)

            steps = str(row.get("diligence_steps", "")).split(" | ")
            if steps and steps[0]:
                p = doc.add_paragraph()
                _set_font(p.add_run("Diligence:"), size=11, bold=True)
                for s in steps:
                    bp = doc.add_paragraph(style="List Bullet")
                    _set_font(bp.add_run(s), size=11)

        doc.add_paragraph("")

    os.makedirs(output_dir, exist_ok=True)
    out_path = os.path.join(output_dir, "investor_brief.docx")
    doc.save(out_path)
    return out_path
