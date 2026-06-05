# Live demo cheat sheet



Use this during a walkthrough: change **one** knob in JSON, re-run **one** command, show the output.



## Before you start



1. Open `config/pipeline_settings.json` in the editor.

2. Ensure a Specter `.xlsx` or `.csv` is in `data/input/` (newest file is used automatically).



**Re-run command** (same command every time; input stays in place):



```powershell

python scripts/run_pipeline.py

```



Optional: `python scripts/run_pipeline.py --input path/to/file.xlsx` if the file is not in `data/input/`.



---



## The three levers they may ask for



| They ask for… | Edit in `pipeline_settings.json` | What to show after re-run |

|---------------|----------------------------------|---------------------------|

| **Scoring weight** | `scoring.weights` — e.g. `founder_signal: 0.35`, `growth_momentum: 0.15` (keep sum = **1.0**) | Terminal **Top 5** and `investor_brief.md` rank order |

| **Sector** | `scoring.target_sectors` — add/remove a keyword | `scored_companies.csv` → `sector_score` and Portfolio Summary |

| **Filter** | `scoring.min_score_threshold` (e.g. `40` → `70`) or `scoring.target_stages` | Terminal line: `N companies passed the threshold` |



Skills (`.md` files) are documentation only — **do not** edit them for the demo.



---



## Recommended primary demo (weight)



In `scoring.weights`:



```json

"stage_fit": 0.25,

"sector_alignment": 0.25,

"founder_signal": 0.35,

"growth_momentum": 0.15

```



Re-run, then compare Top 5 to the previous run folder under `output/`.



---



## Sector demo (if they say "change a sector")



Add or remove one string in `scoring.target_sectors`, e.g. remove `"Maritime"` or add `"Drones"`.



Re-run, open `scored_companies.csv`, sort by `sector_score`.



---



## Filter demo (if they say "change a filter")



Raise cutoff:



```json

"min_score_threshold": 70

```



Re-run; qualified count drops (terminal + fewer rows in CSV).



---



## Bonus lever (outreach, not ranking)



`actions.reach_out_threshold`: `92` → `95` changes Tier 1 vs Tier 2 **Action** lines without reordering the list.



---



## Empty input folder?



Drop a Specter export into `data/input/`, or use `--input` with a path (e.g. an old copy in `data/input/archive/`).


