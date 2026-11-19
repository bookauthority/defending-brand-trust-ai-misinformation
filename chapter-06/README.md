# Experiment: Playbooks for Common AI Misinformation Scenarios

This self-contained Python 3.11+ project implements a minimal, offline-friendly
simulation experiment for:

- **Chapter**: 6
- **Experiment ID**: `exp-ch06-playbooks-misinformation-sim-0001`
- **Title**: Playbooks for Common AI Misinformation Scenarios

The goal is to compare **baseline** (ad-hoc narrative guidance) versus
**treatment** (modular, trigger-based playbooks) conditions on scripted
misinformation incident scenarios.

This project provides:

- A small, deterministic CLI-based simulator.
- Synthetic timelines for three workloads (deepfake video, synthetic
  complaints, fabricated safety incident).
- Tiny, structured playbooks encoding simple trigger/action rules.
- An experiment runner that executes both baseline and treatment variants for
  all workloads and records numeric metrics.
- Unit tests that verify the evidence schema and core behaviour.

All logic uses the Python standard library only; there are **no external
runtime dependencies**.

## Repository layout

- `run.py` – Main entry point; runs the experiment and writes evidence.
- `experiment/__init__.py` – Package marker.
- `experiment/config.py` – Encodes experiment metadata and small configs.
- `experiment/data_loader.py` – Loads synthetic timelines and playbooks.
- `experiment/simulator.py` – Core simulation logic implementing baseline and
  treatment behaviours.
- `experiment/metrics.py` – Metric computation helpers.
- `experiment/evidence_writer.py` – Writes `/evidence/results.json` according to
  the required schema.
- `experiment/assets/` – Bundled CSV/YAML-like data for scenarios & playbooks.
- `tests/test_experiment.py` – Unit tests (run via `unittest`).

## Running the experiment

The experiment is deterministic: each run uses fixed pseudo-random seeds and
small synthetic datasets. This keeps execution fast and reproducible while still
implementing genuine behavioural differences between baseline and treatment.

### 1. Run the experiment

From the project root:

```bash
python run.py
``

This will:

1. Load workloads and playbooks from `experiment/assets/`.
2. Run **baseline** and **treatment** variants for each of the three workloads.
3. Compute numeric metrics derived from the simulated event timelines and
   actions (e.g., time to first action, time to first public response,
   channel coverage ratio, and a simple outcome risk proxy).
4. Write evidence to a JSON file at:

- `$BOOKMAS_EVIDENCE_DIR/results.json` if `BOOKMAS_EVIDENCE_DIR` is set, or
- `/evidence/results.json` otherwise.

The file will conform to the runtime contract:

```json
{
  "chapter": 6,
  "experiment_id": "exp-ch06-playbooks-misinformation-sim-0001",
  "environment": {"os": "...", "python": "..."},
  "runs": [
    {
      "variant": "baseline",
      "workload_id": "scenario-deepfake-exec-video-v1",
      "run_id": "...",
      "success": true,
      "metrics": {
        "time_to_first_meaningful_action_minutes": 5.0,
        "time_to_public_response_minutes": 25.0,
        "channel_coverage_ratio": 0.75,
        "incident_outcome_risk_proxy": 0.42
      }
    }
  ],
  "notes": "..."
}
```

- Every `metrics` value is a **number**.
- At least one baseline and one treatment run is recorded per workload.
- Extra descriptive fields (stdout summaries, LOC counts, etc.) are recorded in
  `notes` (or as additional top-level keys), never inside `metrics`.

### 2. Run tests

From the project root:

```bash
python -m unittest discover -s tests -p "test_*.py"
```

Tests verify that:

- The experiment runs without errors and produces evidence in the correct path.
- Evidence conforms to the required schema (types, required fields, metric
  shapes, and value types).
- Baseline and treatment both appear per workload.
- Metrics values are numeric and finite.

## Design notes

### Baseline vs. Treatment implementation

The simulator uses simple rule-based agents:

- **Common elements** (both variants):
  - Read a timeline of events with relative times and channels.
  - Step through events in chronological order.
  - At each event, decide on zero or more actions (e.g., investigation,
    escalation, draft statement, channel response).

- **Baseline**:
  - Uses generic, non-playbook heuristics (e.g., react after a fixed delay once
    several events accumulate; slower to escalate; slower to respond publicly).
  - No structured triggers, roles, or channel coverage logic.

- **Treatment**:
  - Uses playbook definitions (simple YAML-like data) with:
    - Triggers on event volume or channel types.
    - Target time windows for investigative steps and public responses.
    - Channel-specific coverage expectations.
  - Reacts faster and more consistently when triggers fire.

The simulation captures actions and computes metrics derived from timestamps and
coverage. While this is a simplification of real-world behaviour, it
satisfies the requirement for **actual, instrumented metrics** without using
any external libraries or a full interactive UI.

### Metrics implemented

In this offline sandbox, rich qualitative metrics (like expert-judged
escalation appropriateness or decision-tree adherence) cannot be measured
meaningfully. To maintain fidelity to the schema **and** honesty about what is
measurable here, the experiment records only those metrics that can be
computed directly from the simulation traces:

- `time_to_first_meaningful_action_minutes` – Time from first event to first
  action of types considered "meaningful" (investigation, escalation, public
  drafting or response).
- `time_to_public_response_minutes` – Time from first event to first external
  public response action (e.g., social post, press statement).
- `channel_coverage_ratio` – Fraction of scenario channels that received at
  least one targeted action.
- `incident_outcome_risk_proxy` – A simple proxy calculated from how late the
  first action and first public response occur, normalized to `[0, 1]`.

Other metrics from the chapter spec (e.g., decision consistency, cognitive
load, expert ratings, playbook adherence) are **not** emitted, since doing so
would require synthetic or subjective inputs not available in this sandbox.

### Reproducibility

- All data files are part of the repository under `experiment/assets/`.
- Simulation uses deterministic logic; any pseudo-randomness is seeded
  predictably.
- No network or external system calls are used; only the local filesystem (and
  the `/evidence` directory) is accessed.

### Extensibility

You can extend this project by:

- Adding richer timelines under `experiment/assets/data/`.
- Modifying playbooks in `experiment/assets/playbooks/` to experiment with
  different trigger designs.
- Enhancing the simulator with a TUI or web frontend while keeping the same
  underlying evidence writer.
- Implementing more sophisticated metrics in `experiment/metrics.py` that remain
  computable from logs.
