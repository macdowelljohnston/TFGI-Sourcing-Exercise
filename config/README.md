# Pipeline configuration

All tunable business rules live in **`pipeline_settings.json`**. The Python scripts
read this file at runtime — edit the JSON, save, and re-run. No code changes needed.

```powershell
python scripts/run_pipeline.py
```

---

## Quick-edit reference

| To do this... | Section to edit |
|---------------|-----------------|
| Add or remove a target sector | `scoring.target_sectors` |
| Change scoring weights | `scoring.weights` (must sum to 1.0) |
| Add or adjust a founder tag | `scoring.founder_tag_scores` |
| Change which stages qualify | `scoring.target_stages` |
| Change how many companies appear in the brief | `scoring.top_n_companies` |
| Change the minimum score to qualify | `scoring.min_score_threshold` |
| Change the tier bands (Tier 1 / 2 / 3) | `scoring.score_tiers` |
| Change the outreach action wording | `actions.outreach_labels` |
| Change when to recommend Tier 1 vs Tier 2 outreach | `actions.reach_out_threshold`, `actions.partner_review_threshold` |
| Add a diligence step | `actions.diligence_rules` |
| Change the brief title or footer | `report.title`, `report.footer_text` |

---

## Section-by-section reference

### `input`

Controls where the pipeline looks for a new Specter export. This lets you drop a
file into a convenient external folder instead of attaching it in the chat or
copying it into the repo by hand.

- **`drop_folder`** — the external folder to scan. A relative path (e.g.
  `"Desktop/Friedkin_Inbox"`) is resolved against your Desktop at runtime, so the
  setting stays portable across machines (it also handles a OneDrive-redirected
  Desktop). An absolute path is used as-is.
- **`drop_folder_env_var`** — name of an environment variable that, if set,
  overrides `drop_folder`. Default: `"FRIEDKIN_INBOX"`. Set it in `.env`.
- **`auto_create_drop_folder`** — when `true`, the drop folder is created if it
  does not exist, so there is always somewhere to drop the file.
- **`copy_to_repo`** — when `true`, a file found in the external drop folder is
  copied into `repo_input_dir` before processing, so every run is reproducible
  from the repo. The original in the drop folder is left in place.
- **`repo_input_dir`** — the in-repo input/fallback folder. Default:
  `"data/input"`.
- **`file_extensions`** — which file types count as an export. Default:
  `[".xlsx", ".csv", ".xlsm"]`.

**Resolution order** (first match wins): `--input <file>` >
`--inbox <folder>` / `FRIEDKIN_INBOX` > `input.drop_folder` > `data/input/`.

---

### `cleaning`

Controls which columns are kept from the raw Specter export and how the data is
cleaned before scoring.

- **`columns_to_keep`** — the list of Specter column names to retain. Any column
  not listed here is dropped before scoring. Add a column name here if you want
  it to appear in the scored CSV output.
- **`keep_operating_status`** — only companies matching this value in the
  Operating Status column are kept. Default: `"Active"`.
- **`dedupe_column`** — if two rows share the same value in this column, only
  the first is kept. Default: `"Domain"` (website URL).
- **`text_columns`** / **`funding_columns`** — internal formatting lists; safe
  to leave as-is.

---

### `scoring.weights`

Controls how much each dimension contributes to the total score. All four values
**must sum to 1.0** exactly — the pipeline will stop with an error if they do not.

```json
"weights": {
  "stage_fit": 0.15,
  "sector_alignment": 0.15,
  "founder_signal": 0.40,
  "growth_momentum": 0.30
}
```

To emphasise founders more heavily, raise `founder_signal` and lower another
dimension by the same amount.

---

### `scoring.target_stages` and `scoring.stage_partial_scores`

`target_stages` lists the growth stages that score 100% on stage fit. Companies
at other stages receive partial credit as defined in `stage_partial_scores`
(a number between 0 and 1, where 1.0 = 100%).

---

### `scoring.target_sectors`

A list of keywords checked against each company's industry, description, and
other text fields. The more keywords match, the higher the sector score.
Add or remove keywords freely — they are case-insensitive.

---

### `scoring.sector_match`

Controls how many keyword matches are needed for a full or partial sector score.

- **`keywords_for_full_score`** — a company must match this many sector keywords
  to score 100 on sector alignment. Default: 3.
- **`keywords_for_partial_score`** — matching at least this many keywords earns
  a partial score. Default: 1.
- **`partial_score_pct`** — the partial score awarded (0-100). Default: 60,
  meaning a company with one or two keyword matches scores 60 out of 100 on sector.

Example: with defaults, a company matching "Transportation" and "Logistics" (2 keywords)
scores 60. A company matching "Transportation", "Logistics", and "Robotics" (3+) scores 100.

---

### `scoring.founder_tag_scores`

Each tag that Specter records under "Founder Highlights" is worth a certain
number of points. Tags not listed here score zero.

```json
"Prior Exit": 0.35,
"Serial Founder": 0.25,
"Top University": 0.10
```

Add a new tag by adding a line: `"Tag Name As It Appears In Specter": 0.15`

---

### `scoring.founder_tags_for_max_score`

The combined tag value a founder team needs to earn a perfect founder score (100).
Tag values are summed, then divided by this number, then capped at 100.

Default is **1.5**. With that setting, a founder with Prior Exit (0.35) + Serial
Founder (0.25) + Top University (0.10) = 0.70 total scores 47 out of 100.
A founder with Prior Exit + Prior IPO + Serial Founder = 0.95 scores 63 out of 100.

Raise this number to make the founder score harder to max out. Lower it to give
more credit to founders with fewer tags.

---

### `scoring.momentum`

Controls the growth momentum sub-score, which blends three signals: headcount
growth, web traffic growth, and how recently the company last raised.

- **`headcount_growth_pct_for_full_score`** — a company with this percentage or
  more of 6-month headcount growth scores 100 on the headcount signal. Below
  that, the score scales proportionally. Default: 15 (meaning 15% growth = full score).
- **`web_growth_pct_for_full_score`** — same logic for 6-month web traffic growth.
  Default: 30.
- **`recent_funding_window_months`** — companies that raised within this many
  months score full marks on the recency signal. Default: 12.
- **`mid_funding_window_months`** — companies that raised between the recent
  window and this many months ago score partial marks on recency. Default: 24.
- **`score_if_funding_date_unknown`** — score assigned to the recency signal
  when no funding date is on record. Default: 0.1 (10%), treating the company as
  unlikely to be in an active raise.
- **`headcount_weight`**, **`web_weight`**, **`recency_weight`** — how the three
  signals are blended. These must sum to 1.0 — the pipeline will stop with an
  error if they do not.

---

### `scoring.score_tiers`, `scoring.min_score_threshold`, `scoring.top_n_companies`

- **`score_tiers`** — the tier label and minimum score for each band. Must be
  listed highest to lowest.
- **`min_score_threshold`** — companies below this total score are excluded from
  all outputs. Default: 75.
- **`top_n_companies`** — how many companies appear in the investor brief.
  The full scored list (all above the threshold) is always saved to
  `scored_companies.csv`.

---

### `actions`

Controls the outreach recommendation and diligence steps added to each company
in the brief.

- **`reach_out_threshold`** — companies at or above this score get a Tier 1
  "reach out now" recommendation. Default: 85.
- **`partner_review_threshold`** — companies at or above this score (but below
  the Tier 1 threshold) get a Tier 2 "schedule review" recommendation.
  Default: 80.
- **`outreach_labels`** — the exact wording used for each tier in the brief.
  Edit these to change how the action line reads.
- **`timing_bands`** — messages based on how long ago the company last raised.
  `max_months` is the upper end of the band; `null` means "anything older".
  `{months}` in the message text is replaced with the actual number.

#### Diligence rules

Each rule adds a bullet point to a company's diligence section if the condition
is met.

```json
{
  "field": "momentum_score",
  "op": "less_than",
  "value": 70,
  "step": "Investigate soft growth signals (headcount / web traffic)."
}
```

- **`field`** — which score or data point to check. Options:
  `sector_score`, `momentum_score`, `months_since_funding`, `web_visits`
- **`op`** — the comparison to run. Options:
  `less_than`, `greater_than`, `missing` (field has no data)
- **`value`** — the number to compare against
- **`step`** — the text that appears in the Diligence section of the brief

To add a step that appears for every company, use `"always": true` instead
of a field/op/value:

```json
{ "always": true, "step": "Validate founder track record and prior exit outcomes." }
```

**`diligence_closers`** are steps appended to every company after the conditional
rules, up to the `max_diligence_steps` limit.

---

### `rationale`

Controls what appears in the text paragraph for each company in the brief.

- Toggle `include_funding_section`, `include_growth_signals`, `include_founder_tags`,
  `include_score_breakdown` on or off (`true`/`false`).
- `founder_tags_to_highlight` — only these tags are mentioned in the rationale
  text (even if the company has others).
- `max_description_chars` — how much of the company description to include.

---

### `report`

Controls the brief's title, fonts, colours, and layout.

- `title` / `subtitle` — appear at the top of the brief.
- `footer_text` — appears at the bottom of every page in the Word doc.
- `font` — typeface for the Word document. Default: Georgia.
- `colors` — hex colour codes for the Word document styling.
- `show_summary_section` — toggle the Portfolio Summary table on or off.
- `top_picks_count` — how many companies are named in the "Top picks" line.

---

## JSON tips

- Use double quotes for all keys and string values.
- No trailing comma after the last item in a list or object.
- `true` and `false` are lowercase, not `True`/`False`.
- If the pipeline prints a validation error, check that `scoring.weights` sum
  to exactly 1.0 and that `score_tiers` run from highest `min_score` to lowest.
