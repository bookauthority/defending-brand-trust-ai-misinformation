from __future__ import annotations

import json
import os
import types
import unittest
from pathlib import Path
from typing import Any, Dict, List

import run as experiment_run


class ExperimentEvidenceSchemaTest(unittest.TestCase):
    """Validate that run.py produces evidence matching the required schema."""

    def setUp(self) -> None:
        # Use a temporary evidence directory under the test working tree
        self.evidence_dir = Path("/evidence")
        # Ensure directory exists and is empty-ish
        self.evidence_dir.mkdir(parents=True, exist_ok=True)
        results_file = self.evidence_dir / "results.json"
        if results_file.exists():
            results_file.unlink()

        # Point the experiment at our evidence directory
        os.environ["BOOKMAS_EVIDENCE_DIR"] = str(self.evidence_dir)

        # Run the experiment once for all tests; this should be fast
        experiment_run.main()

        # Load the produced evidence
        self.results_path = self.evidence_dir / "results.json"
        self.assertTrue(self.results_path.exists(), "results.json was not created")

        with self.results_path.open("r", encoding="utf-8") as f:
            self.evidence: Dict[str, Any] = json.load(f)

    def test_top_level_schema(self) -> None:
        evidence = self.evidence
        for key in ("chapter", "experiment_id", "environment", "runs"):
            self.assertIn(key, evidence, f"Missing top-level key: {key}")

        self.assertIsInstance(evidence["chapter"], int)
        self.assertEqual(evidence["chapter"], 12)

        self.assertIsInstance(evidence["experiment_id"], str)
        self.assertEqual(
            evidence["experiment_id"],
            "exp-ch12-readiness-sim-tabletop-redteam-v1",
        )

        env = evidence["environment"]
        self.assertIsInstance(env, dict)
        self.assertIn("os", env)
        self.assertIn("python", env)

        runs = evidence["runs"]
        self.assertIsInstance(runs, list)
        self.assertGreaterEqual(len(runs), 6)  # 3 workloads * (baseline + treatment)

    def test_runs_schema_and_metrics_numeric(self) -> None:
        runs: List[Dict[str, Any]] = self.evidence["runs"]
        allowed_variants = {"baseline", "treatment"}

        seen_by_workload: Dict[str, Dict[str, int]] = {}

        for run in runs:
            for key in ("variant", "workload_id", "run_id", "success", "metrics"):
                self.assertIn(key, run, f"Missing run key: {key}")

            self.assertIn(run["variant"], allowed_variants)
            self.assertIsInstance(run["workload_id"], str)
            self.assertIsInstance(run["run_id"], str)
            self.assertIsInstance(run["success"], bool)

            metrics = run["metrics"]
            self.assertIsInstance(metrics, dict)

            # Each metric must be a finite JSON number (int or float)
            for m_name, m_value in metrics.items():
                self.assertIsInstance(
                    m_value,
                    (int, float),
                    msg=f"Metric {m_name} has non-numeric value {m_value!r}",
                )

            workload_id = run["workload_id"]
            variant = run["variant"]
            seen_by_workload.setdefault(workload_id, {})
            seen_by_workload[workload_id].setdefault(variant, 0)
            seen_by_workload[workload_id][variant] += 1

        # Ensure at least one baseline and one treatment run per workload
        for workload_id, counts in seen_by_workload.items():
            self.assertGreaterEqual(
                counts.get("baseline", 0),
                1,
                f"No baseline run recorded for workload {workload_id}",
            )
            self.assertGreaterEqual(
                counts.get("treatment", 0),
                1,
                f"No treatment run recorded for workload {workload_id}",
            )


if __name__ == "__main__":
    unittest.main()
