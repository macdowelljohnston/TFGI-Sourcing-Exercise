# Skill: Founder Assessment

## Purpose
Use Claude to parse unstructured Founder Highlights text and return a
structured founder quality score and key signals for each company.

## Input
The Founder Highlights field from Specter, e.g.:
"CEO previously founded and sold LogisticsAI to UPS in 2019.
 CTO has 10 years at SpaceX in propulsion systems."

## Prompt Template

You are an investment analyst at a venture capital firm focused on
Transportation, Manufacturing, Physical AI, Automotive, and Aerospace & Defense.

Given the following founder background for {{company_name}}, return ONLY
a JSON object with no other text:

    {
      "score": float 0.0 to 1.0,
      "signals": list of up to 3 short positive signal strings,
      "red_flags": list of any concerns or empty list,
      "summary": one sentence assessment
    }

Scoring guide:
- Prior exit or founding experience: +0.4
- Deep domain or operator background: +0.3
- Top-tier university or employer (MIT, Stanford, SpaceX, Google, McKinsey): +0.2
- Multiple founders: +0.1
- No information available: 0.0

Founder background:
{{founder_highlights}}

## Editing This Skill
- To change scoring signals, edit the Scoring guide section above
  and update the prompt in scripts/score_companies.py accordingly.
- To add new positive signals, adjust weights so total possible
  score does not exceed 1.0.
  