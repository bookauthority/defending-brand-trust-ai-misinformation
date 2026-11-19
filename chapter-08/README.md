# Chapter 8 Experiment: Data, Dashboards, and Metrics – Quantifying Trust and Resilience

Experiment ID: `exp-ch08-trust-metrics-dashboard-v1`

This self-contained Python 3.11+ project implements a reproducible experiment comparing a **baseline** ad‑hoc reporting pipeline to a **treatment** structured trust & resilience metrics system.

It operates entirely on **synthetic data** and produces a standardized evidence file describing the runs and measured metrics. No external dependencies or network access are required.

## Contents

- `run.py` – Main entry point. Generates data, runs baseline and treatment workloads, and writes evidence JSON.
- `experiment/data_generation.py` – Synthetic data generation for trust, incidents, web/search, and financial metrics.
- `experiment/baseline.py` – Baseline flat-reporting style aggregation (simple weekly averages and counts).
- `experiment/treatment.py` – Treatment pipeline implementing a richer metric catalog and engineered indicators.
- `experiment/metrics.py` – Shared utilities for computing experiment-wide metrics (e.g., median TTD/TTR, catalog completeness).
- `experiment/utils.py` – Helper functions (time periods, aggregation, simple stats).
- `tests/test_experiment.py` – Unit tests validating the evidence schema and basic behavior.
- `requirements.txt` – Empty runtime dependency file (standard library only).

## Conceptual Mapping to Chapter Sections

The project is intentionally small but illustrates core ideas:

1. **What You Can and Cannot Measure About ‘Trust’**  
   - Trust proxies: sentiment index, volatility, misinformation mention rate.  
   - Limitations documented via comments and `notes` in evidence.

2. **Core Metrics for AI Misinformation Defense: Leading and Lagging Indicators**  
   - Leading: sentiment index, misinformation-mention rate, help-center visits, search volume.  
   - Lagging: revenue, churn proxy, NPS proxy, call-center volume.

3. **Designing an Executive Trust and Risk Dashboard**  
   - Treatment computes an integrated weekly table approximating a dashboard back-end (no GUI framework needed).  
   - RAG-style thresholds are represented as engineered fields (e.g., trust index flags) but not rendered visually in this sandbox.

4. **Attribution Challenges**  
   - Treatment builds simple pre/post incident attribution deltas for selected metrics and counts the number of views.

5. **Incident Analytics: Time to Detect, Time to Respond, and Outcome Metrics**  
   - Incident logs include timestamps: alert, detection, classification, statement, containment, resolved.  
   - Treatment computes TTD, TTR, containment duration, total duration; medians are recorded in evidence.

6. **Connecting Trust Metrics to Financial and Strategic KPIs**  
   - Treatment computes a Pearson-like correlation between trust index and revenue using basic statistics.

7. **Reporting to the Board**  
   - We do not generate slide decks here, but the treatment summary table is suitable as a board reporting data source.  
   - Evidence includes counts such as number of catalog metrics and attribution views, mirroring what would feed into board templates.

## Experimental Design Overview

- **Baseline condition**:  
  - Simple weekly aggregations of synthetic data.  
  - No metric catalog.  
  - No explicit leading vs lagging distinction.  
  - No incident analytics beyond raw counts.

- **Treatment condition**:  
  - Metric catalog with standardized fields and completeness computation.  
  - Leading/lagging indicator tagging and coverage estimation.  
  - Incident analytics (TTD/TTR medians, containment durations).  
  - Simple attribution views (pre vs post incident) and linkage metrics (correlation to revenue).

The **hypothesis** is **not** tested with real users here. Instead, the project focuses on making the *mechanics* of such a system reproducible and inspectable.

## Evidence Output Contract

Running `python run.py` writes a JSON file at:

```jsonc
{
  "chapter": 8,
  "experiment_id": "exp-ch08-trust-metrics-dashboard-v1",
  "environment": {"os": "...", "python": "..."},
  "runs": [
    {
      "variant": "baseline",      // or "treatment"
      "workload_id": "...",       // stable string per workload
      "run_id": "...",            // unique within workload+variant
      "success": true,             // or false if something failed
      "metrics": {
        "some_metric_name": 1.23   // numeric values only
      }
    }
  ],
  "notes": "optional free-text notes about limitations, etc."
}
```

### Important Constraints

- At least **one baseline** and **one treatment** run are recorded **per workload**:
  - `synthetic_trust_and_incident_dataset_generation`
  - `baseline_flat_reporting_pipeline`
  - `treatment_metric_framework_and_dashboard_pipeline`
  - `decision_simulation_and_user_story_workload`
- `metrics` values must be finite JSON numbers (no strings, nulls, lists, or objects).
- Additional descriptive info must live outside the `metrics` dict (e.g., in `notes`).
- If a quantity cannot be measured in this sandbox, it is simply omitted from `metrics` but may be mentioned in `notes`.

### Shared Numeric Metrics Between Baseline and Treatment

The review highlighted a blocking issue: the treatment metric framework workload did not expose at least one **shared numeric metric** present in **both** baseline and treatment variants.

To preserve a meaningful baseline/treatment comparison, this project now ensures that within the `treatment_metric_framework_and_dashboard_pipeline` workload:

- Both variants compute `channel_weighted_sentiment_index_mean` and `revenue_mean` as numeric metrics.  
- These metrics are derived from their respective weekly tables (baseline summary versus treatment trust/financial table), so they reflect actual execution while remaining comparable across variants.

Additional treatment-only metrics (e.g., catalog completeness, incident medians, correlation) are still computed and recorded for the treatment variant.

## How to Run

1. Ensure a directory for evidence exists and is writable, e.g. `/evidence`.

2. Set the environment variable `BOOKMAS_EVIDENCE_DIR` to that path, for example:

   ```bash
   export BOOKMAS_EVIDENCE_DIR=/evidence
   ```

3. From the project root, execute:

   ```bash
   python run.py
   ```

4. Inspect the generated evidence file:

   ```bash
   cat /evidence/results.json
   ```

## Running Tests

From the project root, run:

```bash
python -m unittest discover -s tests -p "test_*.py"
```

Tests verify that:

- `/evidence/results.json` exists after running `run.py`.
- The evidence schema matches the required structure.
- Each defined workload has at least one baseline and one treatment run.
- Metrics are numeric.

## Adapting This Project

This reference implementation is intentionally conservative:

- No external libraries beyond the Python standard library.
- Synthetic data only; no network or external APIs.

To adapt for a real organization, you could:

- Replace the synthetic generators in `experiment/data_generation.py` with connectors to real data sources.
- Extend `experiment/treatment.py` with richer attribution models or dashboards (e.g., using pandas, plotly, or a BI layer) while preserving the evidence contract.
- Add new metrics to the catalog and surface them in your executive and board reports.
