import json
import os
import unittest
from pathlib import Path


class TestExperimentEvidenceSchema(unittest.TestCase):
    def setUp(self) -> None:
        # Ensure a clean evidence dir for tests
        self.tmp_dir = Path("evidence_test")
        if self.tmp_dir.exists():
            # Remove old file if present
            results_file = self.tmp_dir / "results.json"
            if results_file.exists():
                results_file.unlink()
        self.tmp_dir.mkdir(exist_ok=True)
        os.environ["BOOKMAS_EVIDENCE_DIR"] = str(self.tmp_dir)

    def tearDown(self) -> None:
        # Clean up environment variable
        if "BOOKMAS_EVIDENCE_DIR" in os.environ:
            del os.environ["BOOKMAS_EVIDENCE_DIR"]

    def test_run_produces_valid_results_json(self) -> None:
        # Import run after setting env to ensure it uses our evidence dir
        import run  # type: ignore

        run.main()

        results_path = self.tmp_dir / "results.json"
        self.assertTrue(results_path.exists(), "results.json should be created")

        with results_path.open("r", encoding="utf-8") as f:
            data = json.load(f)

        # Top-level keys
        self.assertIn("chapter", data)
        self.assertIn("experiment_id", data)
        self.assertIn("environment", data)
        self.assertIn("runs", data)

        self.assertIsInstance(data["chapter"], int)
        self.assertEqual(data["chapter"], 7)
        self.assertEqual(
            data["experiment_id"], "exp-ch07-comms-under-fire-ab-testing-v1"
        )

        env = data["environment"]
        self.assertIsInstance(env, dict)
        self.assertIn("os", env)
        self.assertIn("python", env)

        runs = data["runs"]
        self.assertIsInstance(runs, list)
        self.assertGreaterEqual(len(runs), 6)

        # Check that each workload has at least one baseline and one treatment run
        workload_variant_pairs = {}
        for run_entry in runs:
            self.assertIn("variant", run_entry)
            self.assertIn(run_entry["variant"], ("baseline", "treatment"))
            self.assertIn("workload_id", run_entry)
            self.assertIn("run_id", run_entry)
            self.assertIn("success", run_entry)
            self.assertIsInstance(run_entry["success"], bool)
            self.assertIn("metrics", run_entry)

            workload_id = run_entry["workload_id"]
            variant = run_entry["variant"]
            workload_variant_pairs.setdefault(workload_id, set()).add(variant)

            metrics = run_entry["metrics"]
            self.assertIsInstance(metrics, dict)
            # All metric values must be numbers (int or float)
            for k, v in metrics.items():
                self.assertIsInstance(
                    v,
                    (int, float),
                    msg=f"Metric '{k}' should be numeric, got {type(v)}",
                )

        # Verify baseline and treatment present for each workload
        for workload_id, variants in workload_variant_pairs.items():
            self.assertIn("baseline", variants, f"{workload_id} missing baseline run")
            self.assertIn("treatment", variants, f"{workload_id} missing treatment run")


if __name__ == "__main__":
    unittest.main()
