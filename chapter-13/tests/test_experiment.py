import json
import os
import unittest


class TestExperimentResultsSchema(unittest.TestCase):
    def setUp(self) -> None:
        # Ensure evidence dir is set
        evidence_dir = os.environ.get("BOOKMAS_EVIDENCE_DIR", "/evidence")
        os.makedirs(evidence_dir, exist_ok=True)
        self.results_path = os.path.join(evidence_dir, "results.json")

        # Run the experiment if results do not exist yet
        if not os.path.exists(self.results_path):
            import run

            # Explicit call to main; importing the module alone does not
            # execute the experiment.
            run.main()

        with open(self.results_path, "r", encoding="utf-8") as f:
            self.results = json.load(f)

    def test_top_level_keys(self) -> None:
        self.assertIsInstance(self.results, dict)
        self.assertIn("chapter", self.results)
        self.assertIn("experiment_id", self.results)
        self.assertIn("environment", self.results)
        self.assertIn("runs", self.results)

        self.assertEqual(self.results["chapter"], 13)
        self.assertEqual(
            self.results["experiment_id"],
            "exp-13-incident-learning-postmortem-analytics-v1",
        )

        env = self.results["environment"]
        self.assertIsInstance(env, dict)
        self.assertIn("os", env)
        self.assertIn("python", env)
        self.assertIsInstance(env["os"], str)
        self.assertIsInstance(env["python"], str)

    def test_runs_structure_and_metrics(self) -> None:
        runs = self.results["runs"]
        self.assertIsInstance(runs, list)
        self.assertGreaterEqual(len(runs), 6)  # at least 3 workloads * 2 variants

        # Track presence of baseline/treatment per workload
        workload_variants = {}

        for run in runs:
            self.assertIsInstance(run, dict)
            for key in ["variant", "workload_id", "run_id", "success", "metrics"]:
                self.assertIn(key, run)

            variant = run["variant"]
            workload_id = run["workload_id"]
            run_id = run["run_id"]
            success = run["success"]
            metrics = run["metrics"]

            self.assertIn(variant, ("baseline", "treatment"))
            self.assertIsInstance(workload_id, str)
            self.assertIsInstance(run_id, str)
            self.assertIsInstance(success, bool)

            self.assertIsInstance(metrics, dict)
            # At least one numeric metric must exist
            self.assertGreaterEqual(len(metrics), 1)

            # Metrics dict must contain only numeric measurements; no textual
            # or structured fields are allowed here.
            disallowed_metric_keys = {"notes", "stdout", "environment_metadata"}

            for m_name, m_value in metrics.items():
                self.assertIsInstance(m_name, str)
                self.assertNotIn(
                    m_name,
                    disallowed_metric_keys,
                    msg=f"Non-metric field '{m_name}' must not appear inside metrics",
                )
                self.assertIsInstance(
                    m_value,
                    (int, float),
                    msg=f"Metric {m_name} should be numeric",
                )

            workload_variants.setdefault(workload_id, set()).add(variant)

        # Each workload must have both baseline and treatment variants
        for workload_id, variants in workload_variants.items():
            self.assertIn("baseline", variants, msg=f"missing baseline for {workload_id}")
            self.assertIn("treatment", variants, msg=f"missing treatment for {workload_id}")

    def test_required_metric_names_present(self) -> None:
        # Ensure core hypothesis-related metrics are included somewhere
        runs = self.results["runs"]
        required_metrics = {
            "number_of_concrete_follow_through_actions",
            "average_action_specificity_score",
            "postmortem_effort_hours",
        }

        present_metrics = set()
        for run in runs:
            present_metrics.update(run.get("metrics", {}).keys())

        for metric in required_metrics:
            self.assertIn(metric, present_metrics)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
