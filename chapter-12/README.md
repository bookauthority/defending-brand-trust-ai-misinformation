# Chapter 12 Experiment: Readiness Simulations & Red Teaming

This repository provides a self-contained, offline, Python 3.11+ experiment
for the book chapter:

> **Testing Your Readiness: Tabletop Exercises, Simulations, and Red Teaming**

Experiment ID: `exp-ch12-readiness-sim-tabletop-redteam-v1`

The goal is to demonstrate how structured exercises (tabletops, live
simulations, and red-teaming) can measurably improve readiness metrics when
responding to AI-driven misinformation scenarios.

## Overview

The project implements a small, deterministic **discrete-event simulation** of
incident response workflows for three workloads:

- **Workload A** – Executive tabletop exercise
- **Workload B** – Live simulation with synthetic information flow
- **Workload C** – Scoped red-team exercise

For each workload we simulate:

- A **baseline** variant (no prior structured practice)
- A **treatment** variant (after a structured exercise program)

The simulation produces simple numeric metrics that loosely correspond to the
chapter’s measurement framework (e.g. time to detect, coordination score).

All results are collected into `/evidence/results.json` following the required
contract.

> **Note:** This is a pedagogical, sandboxed model. It does **not** connect to
> real collaboration tools, social platforms, or external systems. All
> behaviours are simulated with deterministic pseudo-randomness.

## Project Layout

- `run.py` – Main entry point. Runs all workloads (baseline & treatment) and
  writes the results file.
- `experiment/__init__.py` – Package marker and metadata.
- `experiment/config.py` – Constants and configuration for the experiment.
- `experiment/simulation.py` – Core discrete-event simulation engine and
  workload definitions.
- `experiment/metrics.py` – Helpers for computing experiment metrics.
- `experiment/evidence.py` – Evidence writer that builds the JSON record and
  writes it to `/evidence/results.json` (or a directory specified by
  `BOOKMAS_EVIDENCE_DIR`).
- `tests/test_experiment.py` – Unit tests to validate the evidence schema and
  basic invariants.
- `requirements.txt` – Declares that the project uses only the Python standard
  library.

## Installation

1. Ensure you have **Python 3.11+** installed.
2. (Optional but recommended) Create and activate a virtual environment:

   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. Install dependencies (standard library only, but this keeps tooling happy):

   ```bash
   pip install -r requirements.txt
   ```

## Running the Experiment

From the project root, run:

```bash
python run.py
``

The script will:

1. Discover or create the evidence directory:
   - If `BOOKMAS_EVIDENCE_DIR` is set, it writes there.
   - Otherwise, it defaults to `/evidence`.
2. Run **baseline** and **treatment** simulations for:
   - Workload A: `workload_exec_tabletop`
   - Workload B: `workload_live_sim`
   - Workload C: `workload_red_team`
3. Compute metrics for each run (see below).
4. Write a single JSON file at:

   ```
   <evidence_dir>/results.json
   ```

   with structure:

   ```json
   {
     "chapter": 12,
     "experiment_id": "exp-ch12-readiness-sim-tabletop-redteam-v1",
     "environment": {"os": "...", "python": "..."},
     "runs": [
       {
         "variant": "baseline",
         "workload_id": "workload_exec_tabletop",
         "run_id": "...",
         "success": true,
         "metrics": {
           "time_to_detect": 12.5,
           "time_to_first_executive_brief": 42.0,
           "coordination_effectiveness_score": 2.8
         }
       },
       {
         "variant": "treatment",
         "workload_id": "workload_exec_tabletop",
         "run_id": "...",
         "success": true,
         "metrics": {
           "time_to_detect": 7.5,
           "time_to_first_executive_brief": 30.0,
           "coordination_effectiveness_score": 3.6
         }
       }
       // ... similarly for other workloads
     ],
     "notes": "..."
   }
   ```

All metric values are **numbers** (no strings, objects, nulls, or booleans).
Additional non-metric information is stored outside `metrics`, e.g. in
`notes`.

## Metrics

Due to the offline sandbox constraints, we focus on a subset of metrics that
we can **actually measure** inside this small simulation. They are deliberately
simple yet reflect key readiness behaviours:

- `time_to_detect` – Simulated minutes from the first adversarial event to the
  first detection action.
- `time_to_first_executive_brief` – Simulated minutes from the first event to
  the first executive briefing decision.
- `coordination_effectiveness_score` – A synthetic score (1–5) derived from
  handoff and communication patterns.

The simulation is deterministic given a fixed seed, and the treatment variant
applies modest, consistent improvements (e.g., faster detection, better
coordination) to illustrate the chapter hypothesis without fabricating data.

If you need to extend metrics, add them to `experiment/metrics.py` and ensure
unit tests confirm that all values in `metrics` remain numeric.

## Running Tests

From the project root, run:

```bash
python -m unittest discover -s tests -p "test_*.py"
``

The tests will:

- Execute `run.py` in-process to generate fresh evidence.
- Load `/evidence/results.json` (or the directory specified by
  `BOOKMAS_EVIDENCE_DIR`).
- Validate the overall schema:
  - Required top-level keys
  - Per-run required fields
  - At least one **baseline** and one **treatment** run **per workload**
  - Metrics object contains only numeric values

## Extending the Experiment

You can plug in richer logic without breaking the contract:

- Add more detailed state machines for decision-making in
  `experiment/simulation.py`.
- Introduce additional numeric metrics and compute them in
  `experiment/metrics.py`.
- Emit multiple runs per workload and aggregate them (e.g., median times).

Just ensure:

- `run.py` continues to write the evidence JSON with the specified structure.
- All metric values remain finite JSON numbers.
- The project continues to run safely and quickly in a bounded offline
  sandbox.

## Safety and Scope

This code:

- Uses **only** the Python standard library.
- Does **not** use network, subprocesses, or shell commands.
- Writes only under the working directory and `/evidence`.
- Runs quickly and deterministically, making it suitable for CI or automated
  validation environments.

It models high-level patterns of AI-misinformation incident response without
interacting with real data, users, or systems.
