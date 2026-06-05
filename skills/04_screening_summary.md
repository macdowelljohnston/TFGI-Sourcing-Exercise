# Skill: Screening Summary

## Purpose
Use Claude to generate a concise, investor-ready rationale for each
top-ranked company. Output is used directly in the final brief.

## Input
A single company's cleaned data row, including name, description,
funding, founders, growth signals, and total score.

## Prompt Template

You are a senior analyst at a venture capital firm focused on
Transportation, Manufacturing, Physical AI, Automotive, and Aerospace & Defense.

Given the following data for {{company_name}}, write a 3-5 sentence
investor rationale suitable for an internal deal screening brief.

Be specific. Reference the actual funding, growth, and founder data.
Do not use generic VC language. Do not pad.

Company data:
- Name: {{company_name}}
- Description: {{description}}
- Stage: {{growth_stage}}
- Total Funding: {{total_funding}}
- Last Funding: {{last_funding_type}} ({{last_funding_date}})
- Founders: {{founders}}
- Founder Highlights: {{founder_highlights}}
- Employee Count: {{employee_count}}
- Employee 6-month Growth: {{employee_growth_6m}}
- Web Visits: {{web_visits}}
- Web 6-month Growth: {{web_growth_6m}}
- Qualification Score: {{total_score}}% ({{qualification_tier}})
- Score Breakdown: Stage {{stage_score}}% | Sector {{sector_score}}% | Founder {{founder_score}}% | Momentum {{momentum_score}}%

Return only the rationale paragraph. No bullet points. No headers.

## Editing This Skill
- To change the output format, edit the instructions above and update
  scripts/generate_report.py accordingly.
- To add or remove data fields, edit both the template above and the
  field mapping in scripts/generate_report.py.
  