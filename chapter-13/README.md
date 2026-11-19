# Chapter 13 Experiment: Incident Learning & Postmortem Analytics

Experiment ID: `exp-13-incident-learning-postmortem-analytics-v1`

This project is a **self-contained, offline Python 3.11+ experiment** that
simulates a structured, analytics-enabled postmortem process for AI
misinformation incidents and compares it against a baseline, narrative-only
postmortem approach.

The goal is to demonstrate, in a reproducible way, how structured incident
schemas and basic analytics can:

- Increase the number and quality of concrete follow-through actions.
- Support pattern detection across incidents.
- Remain operationally feasible in terms of effort.

Because this sandbox cannot access real organizational data, we use
**deterministic synthetic incidents** that still respect the evidence schema
outlined in the specification.

## Project Layout

- `run.py` – Main experiment runner. Generates synthetic incident data,
  applies baseline vs treatment analysis, validates the results object, and
  writes `/evidence/results.json`.
- `incident_schema.py` – Python representation of the incident, events,
  actions, and experiment log structures.
- `experiment.py` – Core logic for simulating incident postmortems under
  baseline and treatment conditions and computing metrics.
- `data/` – Deterministic synthetic fixtures used by the experiment.
- `tests/test_experiment.py` – Unit tests for result schema and basic
  behavioral checks.
- `requirements.txt` – Empty of third‑party runtime dependencies (standard
  library only).

## Environment Assumptions

- Python **3.11+**.
- No network access.
- Writable `/tmp`, `/tmp/work`, and `/evidence` directories.
- No external libraries beyond the Python standard library.

## Running the Experiment

1. Ensure the environment variable `BOOKMAS_EVIDENCE_DIR` points to a
   writable directory. In the target sandbox, this will already be `/evidence`.

2. From the project root, run:

   ```bash
   python run.py
   ```

   This will:

   - Run both **baseline** and **treatment** variants for each of the three
     workloads:
     - `historical_backfill`
     - `live_postmortem`
     - `pattern_library`
   - Compute simple numeric metrics for each run (e.g., number of actions,
     effort hours proxies).
   - Validate that the constructed results object matches core invariants
     (chapter, experiment_id, environment shape, and presence of both
     variants per workload) before writing.
   - Write a JSON file to:

   ```text
   /evidence/results.json
   ```

   with the exact required shape:

   ```json
   {
     "chapter": 13,
     "experiment_id": "exp-13-incident-learning-postmortem-analytics-v1",
     "environment": {"os": "...", "python": "..."},
     "runs": [
       {
         "variant": "baseline",
         "workload_id": "historical_backfill",
         "run_id": "...",
         "success": true,
         "metrics": {
           "number_of_concrete_follow_through_actions": 3.0,
           "postmortem_effort_hours": 5.0
         }
       }
       // ... additional runs ...
     ],
     "notes": "..."
   }
   ```

   All metric values are finite numbers, never strings or null.

## Metrics in This Sandbox

The real-world specification includes many human- and time-dependent
metrics (e.g., 60/120-day completion rates, Likert scores). Those **cannot
be measured** meaningfully in this offline sandbox without fabrication, so
we **do not include them** in the `metrics` objects.

Instead, we implement fair and deterministic numeric metrics that reflect
core aspects of the hypothesis:

- `number_of_concrete_follow_through_actions` – Count of synthetic actions
  generated for each run. Treatment generates more and more specific
  actions per incident, reflecting structured analytics.
- `average_action_specificity_score` – Average of per-action specificity
  scores (1–5). Treatment produces higher scores.
- `postmortem_effort_hours` – Synthetic effort proxy derived
  deterministically from incident complexity. Treatment requires a modest
  additional effort vs baseline.

All metrics are computed from the simulated incident structures at
execution time; nothing is hard-coded per run.

These metrics are **proxy values** computed from synthetic incident
structure; they are not derived from real follow-through actions, logs, or
human perception data and are acceptable for this sandbox only.

## Unsupported Real-World Metrics

The schema includes fields such as:

- `follow_through_completion_rate_60d`
- `follow_through_completion_rate_120d`
- `participant_perceived_clarity_gain`
- `participant_perceived_confidence_in_actions`

In this sandbox implementation:

- These fields are represented as **optional** in `ExperimentLogEntry` and
  are always left unset (`None`).
- They **must not** be fabricated to satisfy type hints or tests.
- They are reserved for real-world deployments where longitudinal and
  survey data are genuinely available.

## Running Tests

Execute the unit tests with:

```bash
python -m unittest discover -s tests -p "test_*.py"
```

The tests validate that:

- `/evidence/results.json` exists after running `run.py`.
- The top-level keys and types match the required contract.
- Each `run` entry includes required fields and numeric `metrics` values.
- At least one baseline and one treatment run exist for each workload.
- Metrics objects contain only numeric values (no textual or structured
  fields like `notes` embedded under `metrics`).

## How the Simulation Works

The simulation is deliberately simple but structured:

1. **Synthetic Incidents**: We define several example incidents covering
   different narrative types, channels, and severities, consistent with the
   provided `evidence_schema`.

2. **Baseline vs Treatment Logic**:

   - Baseline uses unstructured narrative style:
     - Fewer actions per incident.
     - Lower specificity scores.
     - Slightly lower effort hours (less analysis, no structured analytics).

   - Treatment simulates analytics-enabled postmortem behavior:
     - More actions derived from richer event analysis.
     - Higher specificity scores.
     - Slightly increased effort hours due to structured analysis.

   The functions in `experiment.py` implement these behaviors deterministically
   using only the incident structure (counts, severity, etc.).

   The metrics produced are **sandbox proxy metrics** and are documented as
   such in code comments and docstrings to avoid confusion with real-world
   measurements.

3. **Workloads**:

   - `historical_backfill`: Uses three historical synthetic incidents.
   - `live_postmortem`: Uses one synthetic new incident.
   - `pattern_library`: Uses a broader set of incidents to mimic cross-incident
     pattern analysis.

4. **Evidence Recording**:

   All runs are recorded in `results.json` with distinct `run_id` values, and
   consistent `workload_id` labels across baseline and treatment variants.

## Extending for Real Use

To adapt this example to real organizational data:

- Replace the synthetic incident generation in `experiment.py` with loaders
  that read your own JSON/CSV incident records matching the evidence schema.
- Plug in real analytics (timelines, phase metrics, clustering) to compute
  additional numeric metrics.
- Wire this experiment harness into your postmortem process and integrate the
  resulting metrics with your governance dashboards.

This project focuses on **reproducibility** and **schema correctness** while
remaining entirely self-contained and safe to execute in restricted
sandboxes.
