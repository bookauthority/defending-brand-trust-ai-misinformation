import json
import os
import tempfile
import unittest

import run as experiment_run


class TestExperimentEvidence(unittest.TestCase):
    def setUp(self) -> None:
        # Use a temporary directory for evidence
        self.tmpdir = tempfile.TemporaryDirectory()
        os.environ["BOOKMAS_EVIDENCE_DIR"] = self.tmpdir.name

    def tearDown(self) -> None:
        self.tmpdir.cleanup()
        if "BOOKMAS_EVIDENCE_DIR" in os.environ:
            del os.environ["BOOKMAS_EVIDENCE_DIR"]

    def test_run_produces_valid_evidence_file(self):
        # Execute experiment logic
        evidence = experiment_run.run_experiment()

        # Write file as the main() would
        out_path = os.path.join(self.tmpdir.name, "results.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(evidence, f)

        # Reload and validate schema
        with open(out_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Top-level keys
        self.assertIn("chapter", data)
        self.assertIsInstance(data["chapter"], int)
        self.assertEqual(data["chapter"], 4)

        self.assertIn("experiment_id", data)
        self.assertEqual(
            data["experiment_id"], "chap4-alert-to-incident-triage-matrix-v1"
        )

        self.assertIn("environment", data)
        self.assertIsInstance(data["environment"], dict)
        self.assertIn("os", data["environment"])
        self.assertIn("python", data["environment"])

        self.assertIn("runs", data)
        self.assertIsInstance(data["runs"], list)
        self.assertGreaterEqual(len(data["runs"]), 4)

        # Ensure at least one baseline and one treatment per workload
        by_workload = {}
        for run in data["runs"]:
            self.assertIn("variant", run)
            self.assertIn(run["variant"], ("baseline", "treatment"))
            self.assertIn("workload_id", run)
            self.assertIn("run_id", run)
            self.assertIn("success", run)
            self.assertIsInstance(run["success"], bool)
            self.assertIn("metrics", run)
            self.assertIsInstance(run["metrics"], dict)

            workload = run["workload_id"]
            by_workload.setdefault(workload, set()).add(run["variant"])

            # Metrics must be numeric
            for key, value in run["metrics"].items():
                self.assertIsInstance(
                    value, (int, float), f"Metric {key} must be numeric"
                )

        for workload, variants in by_workload.items():
            self.assertIn("baseline", variants, f"Missing baseline for {workload}")
            self.assertIn("treatment", variants, f"Missing treatment for {workload}")


if __name__ == "__main__":
    unittest.main()
