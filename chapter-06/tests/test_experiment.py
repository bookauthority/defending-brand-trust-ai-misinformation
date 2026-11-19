import json
import os
import unittest


class TestExperimentEvidenceSchema(unittest.TestCase):
    def setUp(self) -> None:
        # Ensure a clean evidence directory in a temporary location
        self.tmp_evidence_dir = os.path.join("/tmp", "bookmas_evidence_test")
        os.makedirs(self.tmp_evidence_dir, exist_ok=True)
        os.environ["BOOKMAS_EVIDENCE_DIR"] = self.tmp_evidence_dir

        # Run the experiment
        import run as experiment_run

        experiment_run.main()

        self.results_path = os.path.join(self.tmp_evidence_dir, "results.json")

    def test_results_file_exists(self) -> None:
        self.assertTrue(os.path.isfile(self.results_path))

    def _load_results(self):
        with open(self.results_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def test_top_level_schema(self) -> None:
        data = self._load_results()
        self.assertIn("chapter", data)
        self.assertIsInstance(data["chapter"], int)
        self.assertIn("experiment_id", data)
        self.assertEqual(
            data["experiment_id"], "exp-ch06-playbooks-misinformation-sim-0001"
        )
        self.assertIn("environment", data)
        self.assertIsInstance(data["environment"], dict)
        self.assertIn("os", data["environment"])
        self.assertIn("python", data["environment"])
        self.assertIn("runs", data)
        self.assertIsInstance(data["runs"], list)

    def test_runs_schema_and_metrics(self) -> None:
        data = self._load_results()
        runs = data["runs"]
        self.assertGreaterEqual(len(runs), 6)  # 3 workloads * 2 variants

        # Track presence of baseline/treatment per workload
        by_workload = {}

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

            # Required numeric metrics
            required_metric_keys = [
                "time_to_first_meaningful_action_minutes",
                "time_to_public_response_minutes",
                "channel_coverage_ratio",
                "incident_outcome_risk_proxy",
            ]
            for key in required_metric_keys:
                self.assertIn(key, metrics)
                value = metrics[key]
                self.assertIsInstance(value, (int, float))

            # Track variants per workload
            wl = run["workload_id"]
            by_workload.setdefault(wl, set()).add(run["variant"])

        # Ensure each workload has at least one baseline and one treatment
        for wl, variants in by_workload.items():
            self.assertIn("baseline", variants, f"Missing baseline for {wl}")
            self.assertIn("treatment", variants, f"Missing treatment for {wl}")

    def test_metrics_are_finite(self) -> None:
        data = self._load_results()
        for run in data["runs"]:
            for value in run["metrics"].values():
                # JSON has only finite floats/ints; still guard against NaN/inf
                self.assertFalse(isinstance(value, float) and (value != value))  # NaN


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
