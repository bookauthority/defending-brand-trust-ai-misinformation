# Experiment 4 – From Alert to Incident: Triage, Classification, and Escalation

This repository contains a self-contained, reproducible Python 3.11+ experiment project for:

> **From Alert to Incident: Triage, Classification, and Escalation**
>
> Experiment ID: `chap4-alert-to-incident-triage-matrix-v1`

The goal is to compare an **unstructured analyst triage baseline** with a **structured, rules-based triage workflow** for AI misinformation alerts.

The project is designed to run in an offline, restricted environment and writes experiment evidence to `/evidence/results.json` using a fixed schema.

---

## Contents

- `run.py` – Main entry point. Runs baseline and treatment triage for both workloads and writes evidence.
- `triage/baseline.py` – Baseline unstructured triage simulation.
- `triage/treatment.py` – Structured rules-based triage implementation.
- `triage/data.py` – Synthetic alert stream and ground-truth generation utilities.
- `triage/metrics.py` – Metric computation utilities shared by baseline and treatment.
- `triage/config.py` – Encodes the triage taxonomy, scoring, and escalation thresholds (normally would be a YAML file).
- `tests/test_experiment.py` – Unit tests that validate the evidence schema and basic behavior.
- `requirements.txt` – No external runtime dependencies; uses Python standard library only.


## Experiment Design Overview

### Hypothesis

> A structured, rules-based triage and escalation workflow using an explicit AI misinformation incident taxonomy and severity thresholds will reduce alert fatigue and misrouting while increasing consistency and speed of incident handling, compared with an unstructured, analyst-discretion-only approach.

### Baseline – `Unstructured_Analyst_Triage`

Simulated behavior:

- Alerts processed sequentially with simple heuristic decisions and small random variations to approximate analyst inconsistency.
- No standardized taxonomy or severity scale.
- Flags `is_incident` (Y/N), an ad-hoc `priority`, and a free-text style owner category approximation.

### Treatment – `Structured_Triage_Workflow`

Implements a deterministic rules engine based on the specification:

- Explicit **taxonomy** T1–T6 for incident types.
- 4-level **severity** S1–S4 from impact scores (0–15) across five dimensions.
- Explicit **escalation thresholds** and mapping to escalation levels.
- **Ownership model** that maps taxonomy+severity to primary owner teams.

The core decision logic is implemented in `triage/treatment.py` as a small, readable rules engine.


## Workloads

The experiment uses two synthetic alert streams:

1. **Synthetic_Alert_Stream_Low_to_Mid_Risk** – Low to moderate risk alerts, small scale, slower velocity.
2. **Synthetic_Alert_Stream_High_Risk_And_Mixed** – Mixed severity with a few high-impact scenarios and repeated narratives (simulating deduplication / grouping).

For reproducibility and offline execution, these streams are generated deterministically in memory in `triage/data.py` rather than read from external CSV files.


## Metrics

The full specification describes several metrics. In this offline, single-process sandbox we compute a subset that can be meaningfully measured without human analysts or wall-clock timing:

- `alert_to_incident_conversion_rate` – Percentage of alerts classified as incidents.
- `high_severity_incident_detection_rate` – Share of ground-truth S3–S4 incidents correctly surfaced at S3–S4 by each variant.
- `misrouted_incident_rate` – Percentage of incidents whose owner_team does not match ground truth.
- `severity_misclassification_rate` – Percentage of incidents whose severity level differs from ground truth.
- `cross_functional_escalation_accuracy` – Percentage of S3–S4 incidents escalated to all required functions.

Some other metrics from the narrative (e.g., human alert fatigue proxies, real time-to-classification, inter-analyst consistency) are not measured in this automated sandbox. They are therefore omitted from the evidence file, as required by the contract. All reported metrics are derived from actual computations on the synthetic data.


## Evidence File Schema

Running `python run.py` produces `/evidence/results.json` with this structure:

```json
{
  "chapter": 4,
  "experiment_id": "chap4-alert-to-incident-triage-matrix-v1",
  "environment": {
    "os": "...",
    "python": "..."
  },
  "runs": [
    {
      "variant": "baseline",
      "workload_id": "Synthetic_Alert_Stream_Low_to_Mid_Risk",
      "run_id": "...",
      "success": true,
      "metrics": {
        "alert_to_incident_conversion_rate": 42.0,
        "high_severity_incident_detection_rate": 60.0,
        "misrouted_incident_rate": 30.0,
        "severity_misclassification_rate": 25.0,
        "cross_functional_escalation_accuracy": 40.0
      }
    },
    {
      "variant": "treatment",
      "workload_id": "Synthetic_Alert_Stream_Low_to_Mid_Risk",
      "run_id": "...",
      "success": true,
      "metrics": {
        "alert_to_incident_conversion_rate": 55.0,
        "high_severity_incident_detection_rate": 95.0,
        "misrouted_incident_rate": 5.0,
        "severity_misclassification_rate": 10.0,
        "cross_functional_escalation_accuracy": 90.0
      }
    },
    {
      "variant": "baseline",
      "workload_id": "Synthetic_Alert_Stream_High_Risk_And_Mixed",
      "run_id": "...",
      "success": true,
      "metrics": {"...": 0.0}
    },
    {
      "variant": "treatment",
      "workload_id": "Synthetic_Alert_Stream_High_Risk_And_Mixed",
      "run_id": "...",
      "success": true,
      "metrics": {"...": 0.0}
    }
  ],
  "notes": "Additional non-metric explanatory text, if any."
}
```

All metric values are numbers (floats). Additional non-metric information, if any, is stored outside the `metrics` objects.


## How to Run

1. Ensure you are using **Python 3.11+**.
2. Install dependencies (none beyond the standard library):

   ```bash
   python -m pip install -r requirements.txt
   ```

3. Run the experiment:

   ```bash
   python run.py
   ```

   This generates `/evidence/results.json`. If the `BOOKMAS_EVIDENCE_DIR` environment variable is not set, an `/evidence` directory will be created in the current working directory.

4. Run tests:

   ```bash
   python -m unittest discover -s tests -p "test_*.py"
   ```


## Extending the Experiment

- You can modify `triage/config.py` to change severity thresholds or ownership mappings.
- You can change the synthetic data generators in `triage/data.py` to test different alert distributions.
- To add more metrics, implement them in `triage/metrics.py` and include them in the `metrics` dictionaries, ensuring they are numeric.

All changes should preserve the evidence schema enforced by `tests/test_experiment.py`.
