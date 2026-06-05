# Skill: Data Cleaning

## Purpose
Ingest the raw Specter CSV/XLSX export and produce a clean, normalised
dataframe ready for scoring. This module handles nulls, standardises
field formats, and selects only the columns relevant to qualification.

## Input
- Raw Specter export: `data/input/*.xlsx` (or `.csv`)

## Output
- Cleaned dataframe passed to scoring module
- `data/output/cleaned_data.csv` for inspection

## Columns to Retain
Company Name, Domain, Description, Industry, Tech Vertical, Sub-industry,
Growth Stage, Founded Date, HQ Location,
Total Funding Amount (in USD), Last Funding Amount (in USD),
Last Funding Date, Last Funding Type, Post Money Valuation (in USD),
Number of Funding Rounds, Investors, Lead Investors,
Annual Revenue Estimate (in USD),
Founders, Founder Highlights, Number of Founders,
Employee Count,
Employee Monthly Growth1, Employee Monthly Growth3, Employee Monthly Growth6,
Web Visits, Web Visits Monthly Growth3, Web Visits Monthly Growth6,
Number of Patents, Awards Count, Highlights, Tagline

## Cleaning Rules
1. **Funding amounts** — strip currency symbols, convert to float. Nulls → 0.
2. **Growth Stage** — map to standard labels:
   - "Pre-seed / Seed" → "Pre-Seed"
   - "Early Stage" → "Series A/B"
   - "Growth Stage" → "Series B/C"
   - "Late Stage" → "Series D+"
3. **Founded Date** — parse to year integer. Nulls → 0.
4. **Employee growth columns** — convert percentage strings to floats (e.g. "12%" → 0.12).
5. **Text fields** — strip whitespace. Nulls → empty string.
6. **Duplicates** — deduplicate on `Domain`. Keep first occurrence.
7. **Operating Status** — drop rows where not "Active".

## Editing This Skill
To add or remove columns, edit the list above and update
`COLUMNS_TO_KEEP` in `scripts/clean_data.py` accordingly.