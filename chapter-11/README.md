# Chapter 11 Experiment – Technical Toolkit Integrations

Experiment ID: `exp-ch11-technical-toolkit-integrations-v1`

This mini-project implements a reproducible experiment comparing:

- **Baseline**: manual, ad‑hoc handling of AI-misinformation alerts
- **Treatment**: a lightweight, script-based integration pattern using webhook-style flows and routing rules

It is designed so that non-engineers can inspect the configurations and flows, while engineers can run tests and compute simple metrics.

The implementation is intentionally **local-only**, uses **no external dependencies** beyond the Python standard library, and does **not** use the real network. The HTTP-like interactions described in the chapter are simulated in‑process.

## Contents

- `run.py` – orchestrates all workloads (baseline and treatment), computes metrics, and writes the evidence file.
- `experiment/__init__.py` – package marker.
- `experiment/config.py` – small configuration objects (severity thresholds, teams, routing tables).
- `experiment/baseline.py` – baseline manual workflow simulators.
- `experiment/treatment.py` – treatment integration workflow simulators.
- `experiment/metrics.py` – shared metric computations and utilities.
- `experiment/utils.py` – common helpers (ID generation, timestamps, JSONL I/O).
- `config/` – human-readable configuration examples for routing and teams.
- `tests/test_experiment.py` – unit tests that validate the evidence schema and that `run.py` can be executed without error.

## Running the experiment

1. **(Optional) Create a virtual environment**

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
```

2. **Install dependencies**

There are no runtime dependencies beyond the standard library, but to follow the pattern:

```bash
pip install -r requirements.txt
```

3. **Run tests**

```bash
python -m unittest discover -s tests -p "test_*.py"
```

4. **Run the experiment**

By default the evidence file is written to `./evidence/results.json` unless the `BOOKMAS_EVIDENCE_DIR` environment variable is set.

```bash
python run.py
```

After completion you should see a JSON file with this structure:

```json
{
  "chapter": 11,
  "experiment_id": "exp-ch11-technical-toolkit-integrations-v1",
  "environment": {
    "os": "...",
    "python": "..."
  },
  "runs": [
    {
      "variant": "baseline",
      "workload_id": "workload-1-single-stream-medium-volume",
      "run_id": "...",
      "success": true,
      "metrics": {
        "end_to_end_alert_to_ticket_latency_median_sec": 123.0,
        "end_to_end_alert_to_chat_latency_median_sec": 45.0
      }
    },
    {
      "variant": "treatment",
      "workload_id": "workload-1-single-stream-medium-volume",
      "run_id": "...",
      "success": true,
      "metrics": {
        "end_to_end_alert_to_ticket_latency_median_sec": 3.0,
        "end_to_end_alert_to_chat_latency_median_sec": 2.0
      }
    }
  ],
  "notes": "..."
}
```

The actual metric values will depend on the run, but they are derived from the simulated workflows, not invented.

## Design notes

- **Deterministic inputs**: Each workload uses a fixed random seed so that baseline and treatment see identical alert streams.
- **Safety**: No real network, subprocess, or external paths are used. All data is in-memory except the final evidence JSON.
- **Non-engineer readability**:
  - `config/integration_rules.yaml` (simple YAML subset, parsed manually) specifies routing rules in plain language-like structures.
  - `config/teams.yaml` shows team names and channel names.

## Workloads

The code implements three workloads, mirroring the specification:

1. `workload-1-single-stream-medium-volume` – steady stream of alerts over a 30 minute synthetic window.
2. `workload-2-multi-stream-incident-spike` – a burst of high-severity alerts over 5 minutes.
3. `workload-3-failure-and-retry-scenarios` – injects failures in the treatment path (chat/ticket delivery errors) and simulates message drops in the baseline.

Each workload is run once for baseline and once for treatment inside `run.py`.

### Baseline simulation

- Generate alerts and assign detection timestamps across the workload duration.
- Batch them into coarse manual "export" steps.
- Add fixed and random delays for triage and manual posting.

### Treatment simulation

- Process each alert as if it were POSTed to a webhook.
- Apply routing rules from configuration to decide whether to create chat posts and tickets.
- Use automatic small delays to represent processing, plus retries in workload 3.

## Metrics

Due to offline, bounded execution, the experiment reports a *subset* of the full chapter metric catalog, but they reflect real, instrumented timing within the simulated timelines:

For every (variant, workload):

- `end_to_end_alert_to_ticket_latency_median_sec`
- `end_to_end_alert_to_chat_latency_median_sec`
- `alert_routing_coverage`

These are sufficient to compare baseline vs. treatment, and are computable from the simulated timelines. Additional chapter metrics like routing accuracy or operator touch points can be derived if you extend the project.

## Extending the project

- Add richer analysis scripts that output per-alert tables.
- Introduce more nuanced routing rules and team mappings in the YAML configs.
- Expose the simulated services as real HTTP endpoints using `http.server` (still offline) if you want to demonstrate concrete webhooks.
