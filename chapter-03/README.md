# Chapter 3 Experiment: Signals, Noise, and Detection

This project is a self-contained Python 3.11+ experiment for:

> **Signals, Noise, and Detection: Seeing the Attack Early**  
> Experiment ID: `exp-ch03-signals-noise-detection-v1`

It demonstrates a simplified but faithful version of the chapter's detection-stack concepts:

- Synthetic multi-channel event streams for three workloads
- A **baseline** heuristic-only detector
- A **treatment** integrated detector combining heuristics, a deterministic ML-like score, and a simulated human-review workflow
- Measurement of detection metrics for each variant and workload
- Emission of structured evidence as `/evidence/results.json`

The design mirrors the chapter sections:

1. **Where Early Signals Emerge** – We simulate `social`, `search`, `dark_web`, and `owned` channels.
2. **Detection Approaches** – Baseline rules vs. integrated heuristics + ML-like scoring + human review.
3. **Evaluating Vendors and Tools** – The code is transparent and simple, illustrating what “under the hood” logic can look like.
4. **Designing Your Detection Stack** – The project is split into separable components (config, baseline, integrated, metrics).
5. **Detection Metrics That Matter to Executives** – Precision, recall, and alert volumes are computed per workload.
6. **Integrating Alerts to Workflows** – The treatment variant simulates a triage queue and executive-level alerts.
7. **Case Snapshot** – WL1 and WL2 mimic slow-burn deepfake and flash boycott narratives; WL3 models background chatter.

## Project Layout

- `run.py` – Entry point for running the experiment and writing `/evidence/results.json`.
- `config/ch03_detection_config.yaml` – Human-readable configuration for rules and thresholds.
- `data/` – Not actual CSVs; synthetic workloads are generated in-memory matching the described schemas.
- `docs/ch03_metrics_and_interpretation.md` – Brief, executive-readable metric glossary and interpretation.
- `experiment/` – Core experiment code
  - `__init__.py`
  - `config_loader.py` – Loads and parses the YAML detection configuration using stdlib only.
  - `workloads.py` – Deterministic synthetic data generators for WL1, WL2, WL3.
  - `detection_baseline.py` – Heuristics-only monitoring implementation.
  - `detection_integrated.py` – Integrated heuristics + ML-like scoring + human-review simulation.
  - `metrics.py` – Shared metric calculations and helper utilities.
  - `runner.py` – Orchestrates runs for all workloads and variants.
- `tests/test_experiment.py` – Unit tests that verify the evidence schema and basic behavior.
- `requirements.txt` – Empty of runtime dependencies (stdlib only).

## Environment Requirements

- Python **3.11+**
- No third-party packages required; the implementation uses only the Python standard library.

## Running the Experiment

In a typical shell or the provided sandbox:

```bash
# From the project root
export BOOKMAS_EVIDENCE_DIR=/evidence
python run.py
```

This will:

1. Load configuration from `config/ch03_detection_config.yaml`.
2. Generate three synthetic workloads:
   - `WL1_Synthetic_SlowBurn_Deepfake_Rumor`
   - `WL2_Synthetic_Flash_Boycott_Campaign`
   - `WL3_Synthetic_Background_Chatter_With_No_Incident`
3. Run both **baseline** and **treatment** detectors for each workload.
4. Compute metrics for each run.
5. Write a single evidence file to `${BOOKMAS_EVIDENCE_DIR}/results.json` with the following schema:

```json
{
  "chapter": 3,
  "experiment_id": "exp-ch03-signals-noise-detection-v1",
  "environment": {"os": "...", "python": "..."},
  "runs": [
    {
      "variant": "baseline" | "treatment",
      "workload_id": "WL1" | "WL2" | "WL3",
      "run_id": "<unique string>",
      "success": true,
      "metrics": {
        "detected_misinfo_events": 42,
        "total_alerts": 100,
        "true_alerts": 60,
        "false_alerts": 40,
        "precision": 0.6,
        "recall_event_level": 0.7
      }
    }
  ],
  "notes": "...optional free-form text..."
}
```

All metric values are numbers and are derived from actual instrumented execution over the synthetic workloads.

## Running Tests

Tests use only the Python standard library.

```bash
python -m unittest discover -s tests -p "test_*.py"
```

The tests verify that:

- `run.py` creates `/evidence/results.json` using `BOOKMAS_EVIDENCE_DIR`.
- The evidence JSON conforms to the required top-level schema (`chapter`, `experiment_id`, `environment`, `runs`).
- For each workload, there is at least one **baseline** and one **treatment** run.
- Metric values are numbers.

## Design Notes

- **Determinism & Reproducibility**: Workloads are generated using fixed seeds and simple formulas so that results are repeatable.
- **No External I/O**: No network, subprocess, or external APIs are used. All data is synthetic and kept in memory.
- **Safety & Bounded Execution**: Dataset sizes are modest, and all loops are over in-memory lists.
- **Exec-Friendly**: Metrics and logic are intentionally simple enough to be explained in a meeting, while still demonstrating real trade-offs between precision, recall, and alert volume.

For conceptual alignment with the book chapter, see `docs/ch03_metrics_and_interpretation.md`.
