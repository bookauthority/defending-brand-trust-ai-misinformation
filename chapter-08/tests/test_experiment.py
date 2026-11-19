import json
import os
import sys
import unittest


class TestExperimentEvidenceSchema(unittest.TestCase):
    def setUp(self) -> None:
        # Ensure evidence directory
        self.evidence_dir = os.environ.get("BOOKMAS_EVIDENCE_DIR", "/evidence")
        os.makedirs(self.evidence_dir, exist_ok=True)
        self.evidence_path = os.path.join(self.evidence_dir, "results.json")

        # Run the experiment once before tests if evidence is missing
        if not os.path.exists(self.evidence_path):
            # Directly invoke run.main() to avoid using subprocess, which is disallowed.
            sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)))
            import run  # type: ignore

            run.main()

        with open(self.evidence_path, "r", encoding="utf-8") as f:
            self.evidence = json.load(f)

    def test_top_level_schema(self):
        e = self.evidence
        self.assertIsInstance(e, dict)
        self.assertEqual(e.get("chapter"), 8)
        self.assertEqual(e.get("experiment_id"), "exp-ch08-trust-metrics-dashboard-v1")
        self.assertIn("environment", e)
        self.assertIn("runs", e)
        self.assertIsInstance(e["runs"], list)

        env = e["environment"]
        self.assertIsInstance(env.get("os"), str)
        self.assertIsInstance(env.get("python"), str)

    def test_runs_schema_and_metrics_numeric(self):
        runs = self.evidence["runs"]
        self.assertGreaterEqual(len(runs), 1)

        required_workloads = {
            "synthetic_trust_and_incident_dataset_generation",
            "baseline_flat_reporting_pipeline",
            "treatment_metric_framework_and_dashboard_pipeline",
            "decision_simulation_and_user_story_workload",
        }

        seen_by_workload_variant = {}

        for run in runs:
            self.assertIn(run.get("variant"), ("baseline", "treatment"))
            workload_id = run.get("workload_id")
            self.assertIsInstance(workload_id, str)
            self.assertIsInstance(run.get("run_id"), str)
            self.assertIn("success", run)
            self.assertIsInstance(run["success"], bool)

            metrics = run.get("metrics")
            self.assertIsInstance(metrics, dict)
            for k, v in metrics.items():
                # Every metric value must be a number (int or float)
                self.assertIsInstance(
                    v,
                    (int, float),
                    msg=f"Metric {k} is not numeric: {type(v)}",
                )

            key = (workload_id, run.get("variant"))
            seen_by_workload_variant[key] = True

        # Ensure each workload has at least one baseline and one treatment run
        for wid in required_workloads:
            self.assertIn(
                (wid, "baseline"),
                seen_by_workload_variant,
                msg=f"Missing baseline run for {wid}",
            )
            self.assertIn(
                (wid, "treatment"),
                seen_by_workload_variant,
                msg=f"Missing treatment run for {wid}",
            )


if __name__ == "__main__":
    unittest.main()
