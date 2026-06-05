# Skill: Action Recommendation

## Purpose
For each qualified company, recommend a concrete next action: an outreach
call (with timing) and a tailored set of diligence steps. This turns the
ranked shortlist into something an investor can act on immediately.

Rule-based and deterministic. Thresholds are read from
config/scoring_weights.json under "actions".

## Outputs (added to each company)
- **Outreach action** — a tier based on total score:
  - score >= reach_out_threshold (default 0.90) -> "Reach out now (Tier 1)"
  - score >= partner_review_threshold (default 0.80) -> "Schedule partner review (Tier 2)"
  - otherwise -> "Monitor (Tier 3)"
- **Timing note** — based on months since last funding round:
  - under 9 months -> recently raised, build relationship ahead of next round
  - 9-20 months -> likely approaching a new round, strong time to engage
  - over 20 months (or unknown) -> may be raising soon, worth a direct conversation
- **Diligence steps** — tailored to each company's weak spots:
  - Always: validate founder track record
  - If sector score < 1.0: confirm core technology and sector fit
  - If momentum score < 0.7: investigate soft growth signals
  - If last funding over 20 months ago: confirm runway and burn
  - If web traffic data is missing: pull fresh traction data
  - Standard closers: market sizing, cap table / investor quality
  - Capped at 5 steps per company

## Editing This Skill
- To change the outreach tiers, add an "actions" block to
  config/scoring_weights.json:
      "actions": {
        "reach_out_threshold": 0.90,
        "partner_review_threshold": 0.80
      }
- To change which diligence steps fire, edit the rules in
  scripts/recommend_actions.py (function _diligence_steps).
  