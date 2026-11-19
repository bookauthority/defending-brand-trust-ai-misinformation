from __future__ import annotations

import json
import os
import platform
from pathlib import Path
from typing import Any, Dict, List

from experiment.config import CHAPTER_NUMBER, EXPERIMENT_ID
from experiment.evidence import write_evidence
from experiment.simulation import (
    WorkloadResult,
    run_all_workloads,
)


def main() -> None:
    """Run baseline and treatment simulations for all workloads and
    write evidence JSON to /evidence/results.json or BOOKMAS_EVIDENCE_DIR.
    """

    # Run all workloads (baseline & treatment variants)
    workload_results: List[WorkloadResult] = run_all_workloads()

    # Build runs list for evidence
    runs: List[Dict[str, Any]] = []
    for result in workload_results:
        runs.append(
            {
                "variant": result.variant,
                "workload_id": result.workload_id,
                "run_id": result.run_id,
                "success": result.success,
                # Metrics must contain only numeric values
                "metrics": result.metrics,
            }
        )

    evidence: Dict[str, Any] = {
        "chapter": CHAPTER_NUMBER,
        "experiment_id": EXPERIMENT_ID,
        "environment": {
            "os": platform.platform(),
            "python": platform.python_version(),
        },
        "runs": runs,
        "notes": (
            "Offline discrete-event simulation of AI-misinformation "
            "readiness across baseline and treatment variants for "
            "three workloads (executive tabletop, live simulation, "
            "scoped red-team exercise). All metrics are synthetic "
            "but derived from actual instrumented execution within "
            "this sandbox."
        ),
    }

    write_evidence(evidence)


if __name__ == "__main__":
    main()
