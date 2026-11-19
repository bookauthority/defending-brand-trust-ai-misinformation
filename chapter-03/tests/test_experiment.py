import json
import os
import tempfile
import unittest

import run as experiment_run


class TestExperimentEvidence(unittest.TestCase):
    def test_run_produces_valid_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            os.environ["BOOKMAS_EVIDENCE_DIR"] = tmpdir
            # run the experiment
            experiment_run.main()

            evidence_path = os.path.join(tmpdir, "results.json")
            self.assertTrue(os.path.exists(evidence_path), "results.json not created")

            with open(evidence_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Top-level schema checks
            self.assertIn("chapter", data)
            self.assertIn("experiment_id", data)
            self.assertIn("environment", data)
            self.assertIn("runs", data)

            self.assertEqual(data["chapter"], 3)
            self.assertEqual(data["experiment_id"], "exp-ch03-signals-noise-detection-v1")

            env = data["environment"]
            self.assertIsInstance(env, dict)
            self.assertIn("os", env)
            self.assertIn("python", env)

            runs = data["runs"]
            self.assertIsInstance(runs, list)
            self.assertGreaterEqual(len(runs), 6)  # at least 3 workloads * 2 variants

            # Track presence of baseline and treatment per workload
            per_workload_variants = {}

            for run in runs:
                self.assertIn("variant", run)
                self.assertIn("workload_id", run)
                self.assertIn("run_id", run)
                self.assertIn("success", run)
                self.assertIn("metrics", run)

                variant = run["variant"]
                workload_id = run["workload_id"]
                self.assertIn(variant, ("baseline", "treatment"))
                self.assertIn(workload_id, ("WL1", "WL2", "WL3"))

                per_workload_variants.setdefault(workload_id, set()).add(variant)

                metrics = run["metrics"]
                self.assertIsInstance(metrics, dict)
                # Ensure metrics are numeric values
                for key, value in metrics.items():
                    self.assertIsInstance(
                        value,
                        (int, float),
                        msg=f"Metric {key} must be numeric, got {type(value)}",
                    )

            # check each workload has both baseline and treatment
            for wl in ("WL1", "WL2", "WL3"):
                self.assertIn(wl, per_workload_variants)
                self.assertIn("baseline", per_workload_variants[wl])
                self.assertIn("treatment", per_workload_variants[wl])


if __name__ == "__main__":
    unittest.main()
