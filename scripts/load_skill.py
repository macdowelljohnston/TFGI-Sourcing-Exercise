"""
load_skill.py
Extract prompt templates from skills/*.md for optional LLM steps.
"""

import os
import re

SKILLS_DIR = os.path.join("skills")


def load_prompt(skill_filename, section="Prompt Template", skills_dir=None):
    """
    Return text under '## {section}' until the next '## ' heading.
    skill_filename: e.g. '04_screening_summary.md'
    """
    base = skills_dir or SKILLS_DIR
    path = os.path.join(base, skill_filename)
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    pattern = rf"^##\s+{re.escape(section)}\s*$"
    match = re.search(pattern, content, re.MULTILINE | re.IGNORECASE)
    if not match:
        raise ValueError(f"Section '## {section}' not found in {path}")

    start = match.end()
    next_heading = re.search(r"^##\s+", content[start:], re.MULTILINE)
    block = content[start: start + next_heading.start()] if next_heading else content[start:]
    return block.strip()


def fill_prompt(template, mapping):
    """Replace {{key}} placeholders in a prompt template."""
    out = template
    for key, value in mapping.items():
        out = out.replace("{{" + key + "}}", str(value if value is not None else ""))
    return out
