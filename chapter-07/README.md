# Communications Under Fire: A/B Simulation Experiment

This project implements a **self-contained, offline** Python 3.11+ experiment for:

- **Chapter:** 7 – *Communications Under Fire: Crafting Responses That Preserve Trust*
- **Experiment ID:** `exp-ch07-comms-under-fire-ab-testing-v1`

It simulates baseline vs. treatment crisis communication strategies in synthetic audiences and panel ratings, then emits structured evidence in `results.json`.

## Structure

- `run.py` – Entry point. Runs all workloads and writes `results.json` to the path in `$BOOKMAS_EVIDENCE_DIR` (or `./evidence` fallback).
- `experiment/__init__.py` – Package marker.
- `experiment/config.py` – Static configuration and defaults for the experiment.
- `experiment/simulation.py` – Synthetic user and social feed simulation logic (Workload 1).
- `experiment/panel.py` – Synthetic panel A/B test simulation (Workload 2).
- `experiment/analysis.py` – Computation of metrics from simulated data (used by workloads 1, 2 and 3).
- `tests/test_experiment.py` – Unit tests verifying the evidence schema and basic behaviors.

No external dependencies beyond the Python standard library are used.

## Workloads Implemented

The experiment approximates the specification via three workloads.

### Workload 1 – Synthetic Audience Social Feed Simulation

Simulates a social-media-like environment in which a deepfake misinformation event spreads and is then countered by either a **baseline** or **treatment** message.

Key features:

- Generates a synthetic audience with:
  - `segment` (employees, customers, investors, general_public)
  - baseline trust
  - propensity to share misinformation
  - sensitivity to authoritative corrections
  - sensitivity to speed of response
  - region
- Simulates misinformation spread from `t = 0` until response release.
- Applies different behavior rules for baseline vs. treatment messages:
  - Treatment is modeled as clearer, more trustworthy, and slightly slower but still inside SLA.
  - Baseline is faster but less effective at reducing negative sentiment.
- Produces per-cohort metrics:
  - `misinformation_share_of_voice`
  - `negative_sentiment_rate`
  - `corrective_message_reach`

This is a simplified but deterministic, seed-controlled simulation, sufficient to compare variants consistently.

### Workload 2 – Message Copy A/B Test on Sandboxed Panel

Simulates synthetic panelists who rate message variants on various Likert-style scales.

- Panel segments: employees, customers, investors, regulators.
- Each panelist has:
  - baseline trust
  - risk aversion
  - prior exposure to misinformation.
- Baseline and treatment messages differ in modeled psychological effectiveness.
- Metrics computed:
  - `avg_trust_score`
  - `avg_clarity_score`
  - `willingness_to_wait_for_updates`
  - `behavioral_intent_shift`

Again, behavior is simulated deterministically given a seed.

### Workload 3 – Sentiment and Narrative Shift Dashboard (Simplified)

In a full system, this would ingest rich event logs and build time-series dashboards. In this offline, bounded implementation, Workload 3 derives a small additional metric from Workload 1 outputs:

- Computes approximate `time_to_sentiment_stabilization` using a simple function of Workload 1 sentiment metrics.

This keeps runtime small and avoids complex plotting, but preserves the spirit of a comparative analysis workload.

## Running the Experiment

1. **Set up environment**

   ```bash
   python3.11 -m venv .venv
   source .venv/bin/activate  # or .venv\Scripts\activate on Windows
   pip install -r requirements.txt
   ```

2. **Prepare evidence directory**

   Ensure a writable directory for evidence exists. The harness will usually provide `/evidence`. You can also run locally:

   ```bash
   mkdir -p evidence
   export BOOKMAS_EVIDENCE_DIR="$(pwd)/evidence"
   ```

3. **Run the experiment**

   ```bash
   python run.py
   ```

   This will create `results.json` in `$BOOKMAS_EVIDENCE_DIR` (or `./evidence` fallback):

   ```json
   {
     "chapter": 7,
     "experiment_id": "exp-ch07-comms-under-fire-ab-testing-v1",
     "environment": {"os": "...", "python": "..."},
     "runs": [
       {
         "variant": "baseline",
         "workload_id": "workload-1-synthetic-audience-social-feed-simulation",
         "run_id": "...",
         "success": true,
         "metrics": {"misinformation_share_of_voice": 0.7, ...}
       },
       {
         "variant": "treatment",
         "workload_id": "workload-1-synthetic-audience-social-feed-simulation",
         "run_id": "...",
         "success": true,
         "metrics": {"misinformation_share_of_voice": 0.5, ...}
       },
       ...
     ],
     "notes": "..."
   }
   ```

4. **Run tests**

   ```bash
   python -m unittest discover -s tests -p "test_*.py"
   ```

## Design Notes

- **Determinism & Reproducibility**: All random draws share a configurable integer seed (`DEFAULT_RANDOM_SEED` in `config.py`). Each run records its seed-derived `run_id`.
- **No fabricated metrics**: All numeric metrics are computed from the simulated interactions and ratings. No hard-coded values.
- **Fair baseline vs. treatment**: Both variants share the same user and panel populations (when comparing within a workload) by reusing initial data and only changing the response behavior model.
- **Offline & Safe**: No network, subprocess, or non-local filesystem access. Uses only standard library.

## Extending the Experiment

You can adapt this scaffold by:

- Tweaking audience sizes, behavior coefficients, and timing in `config.py`.
- Adjusting how baseline vs. treatment messages influence trust and sharing behavior in `simulation.py` and `panel.py`.
- Adding richer metric calculations in `analysis.py`, ensuring numeric values only in `metrics` within `results.json`.

Any such changes should preserve the evidence contract checked by `tests/test_experiment.py`.
