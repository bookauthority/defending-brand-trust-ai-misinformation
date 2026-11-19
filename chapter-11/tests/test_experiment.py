import json
import os
import unittest


class TestExperimentSchema(unittest.TestCase):
    def setUp(self) -> None:
        # Ensure a clean evidence directory under the working tree
        self.evidence_dir = os.path.join(os.getcwd(), "evidence_test")
        os.makedirs(self.evidence_dir, exist_ok=True)
        os.environ["BOOKMAS_EVIDENCE_DIR"] = self.evidence_dir

    def tearDown(self) -> None:
        # Clean up generated evidence file if present
        results_path = os.path.join(self.evidence_dir, "results.json")
        if os.path.exists(results_path):
            os.remove(results_path)

    def test_run_produces_valid_evidence(self) -> None:
        # Import and run the main entry point
        import run as experiment_run

        experiment_run.main()

        results_path = os.path.join(self.evidence_dir, "results.json")
        self.assertTrue(os.path.exists(results_path), "results.json must exist")

        with open(results_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Top-level keys
        self.assertIn("chapter", data)
        self.assertIn("experiment_id", data)
        self.assertIn("environment", data)
        self.assertIn("runs", data)

        self.assertIsInstance(data["chapter"], int)
        self.assertEqual(data["experiment_id"], "exp-ch11-technical-toolkit-integrations-v1")

        env = data["environment"]
        self.assertIsInstance(env.get("os"), str)
        self.assertIsInstance(env.get("python"), str)

        runs = data["runs"]
        self.assertIsInstance(runs, list)
        self.assertGreaterEqual(len(runs), 6)  # 3 workloads * 2 variants

        seen_workload_variants = set()
        for run in runs:
            self.assertIn("variant", run)
            self.assertIn(run["variant"], ("baseline", "treatment"))
            self.assertIn("workload_id", run)
            self.assertIsInstance(run["workload_id"], str)
            self.assertIn("run_id", run)
            self.assertIsInstance(run["run_id"], str)
            self.assertIn("success", run)
            self.assertIsInstance(run["success"], bool)
            self.assertIn("metrics", run)
            metrics = run["metrics"]
            self.assertIsInstance(metrics, dict)

            # All metric values must be numbers
            for key, value in metrics.items():
                self.assertIsInstance(
                    value,
                    (int, float),
                    msg=f"Metric '{key}' must be numeric, got {type(value)}",
                )

            seen_workload_variants.add((run["workload_id"], run["variant"]))

        # Ensure at least one baseline and one treatment per workload
        workload_ids = {wid for (wid, _variant) in seen_workload_variants}
        for wid in workload_ids:
            self.assertIn((wid, "baseline"), seen_workload_variants)
            self.assertIn((wid, "treatment"), seen_workload_variants)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
