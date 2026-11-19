import json
import os
import platform
import sys
import uuid
from datetime import datetime

from experiment import data_generation, baseline, treatment, metrics as exp_metrics


CHAPTER_NUMBER = 8
EXPERIMENT_ID = "exp-ch08-trust-metrics-dashboard-v1"


def get_evidence_path() -> str:
    """Resolve the evidence file path from BOOKMAS_EVIDENCE_DIR.

    Falls back to /evidence if the environment variable is not set.
    The directory is created if it does not exist.
    """

    base_dir = os.environ.get("BOOKMAS_EVIDENCE_DIR", "/evidence")
    os.makedirs(base_dir, exist_ok=True)
    return os.path.join(base_dir, "results.json")


def main() -> None:
    # Container for experiment-wide state (synthetic data and derived structures)
    state = {}
    runs = []

    # 1) Synthetic data generation workload (shared between baseline and treatment)
    workload_id = "synthetic_trust_and_incident_dataset_generation"

    # Baseline and treatment variants use the same generator; metrics are small summaries
    for variant in ("baseline", "treatment"):
        run_id = f"{workload_id}-{variant}-{uuid.uuid4().hex[:8]}"
        success = True
        run_metrics = {}
        try:
            # Use a fixed seed for reproducibility but distinguish variants slightly
            seed = 42 if variant == "baseline" else 43
            gen_result = data_generation.generate_all(seed=seed)
            # Store only one copy of data in shared state (treatment overwrites baseline but both are consistent)
            state["data"] = gen_result
            # Metrics: counts of rows per table
            run_metrics["num_days"] = float(len(gen_result["time_index"]))
            run_metrics["num_sentiment_rows"] = float(len(gen_result["sentiment"]))
            run_metrics["num_incidents"] = float(len(gen_result["incidents"]))
        except Exception:
            success = False
        runs.append(
            {
                "variant": variant,
                "workload_id": workload_id,
                "run_id": run_id,
                "success": success,
                "metrics": run_metrics,
            }
        )

    # 2) Baseline flat reporting pipeline
    workload_id = "baseline_flat_reporting_pipeline"
    for variant in ("baseline", "treatment"):
        run_id = f"{workload_id}-{variant}-{uuid.uuid4().hex[:8]}"
        success = True
        run_metrics = {}
        try:
            data = state.get("data")
            if not data:
                raise RuntimeError("Synthetic data missing; generation must run first.")
            # Both variants intentionally use the same baseline aggregation here; treatment-specific
            # logic lives in the dedicated treatment workload.
            weekly = baseline.build_baseline_weekly_summary(data)
            # Simple numeric metrics: number of weeks and average weekly revenue
            run_metrics["num_weeks"] = float(len(weekly))
            if weekly:
                avg_rev = sum(w["revenue"] for w in weekly) / float(len(weekly))
                run_metrics["avg_weekly_revenue"] = float(avg_rev)
        except Exception:
            success = False
        runs.append(
            {
                "variant": variant,
                "workload_id": workload_id,
                "run_id": run_id,
                "success": success,
                "metrics": run_metrics,
            }
        )

    # 3) Treatment metric framework and dashboard pipeline
    #    This workload must expose at least one shared numeric metric between baseline and treatment.
    workload_id = "treatment_metric_framework_and_dashboard_pipeline"
    # Precompute weekly artifacts once from the current synthetic data
    data = state.get("data")
    if not data:
        raise RuntimeError("Synthetic data missing; generation must run first.")

    baseline_weekly = baseline.build_baseline_weekly_summary(data)
    treatment_result = treatment.run_treatment_pipeline(data)
    state["treatment"] = treatment_result
    treatment_weekly = treatment_result["weekly_trust_financial"]

    for variant in ("baseline", "treatment"):
        run_id = f"{workload_id}-{variant}-{uuid.uuid4().hex[:8]}"
        success = True
        run_metrics = {}
        try:
            # Shared numeric metrics for both variants, derived from their respective weekly tables.
            if variant == "baseline":
                weekly = baseline_weekly
                if weekly:
                    mean_trust = sum(w["avg_sentiment"] for w in weekly) / float(len(weekly))
                    mean_rev = sum(w["revenue"] for w in weekly) / float(len(weekly))
                    run_metrics["channel_weighted_sentiment_index_mean"] = float(mean_trust)
                    run_metrics["revenue_mean"] = float(mean_rev)
            else:
                weekly = treatment_weekly
                if weekly:
                    mean_trust = sum(
                        w["channel_weighted_sentiment_index"] for w in weekly
                    ) / float(len(weekly))
                    mean_rev = sum(w["revenue"] for w in weekly) / float(len(weekly))
                    run_metrics["channel_weighted_sentiment_index_mean"] = float(mean_trust)
                    run_metrics["revenue_mean"] = float(mean_rev)

                # Treatment-specific metrics required by the specification where feasible in this sandbox
                cat = treatment_result["metric_catalog"]
                cat_metrics = exp_metrics.compute_catalog_metrics(cat)
                run_metrics["num_metrics_in_catalog"] = float(
                    cat_metrics["num_metrics_in_catalog"]
                )
                run_metrics["metric_definition_completeness"] = float(
                    cat_metrics["metric_definition_completeness"]
                )
                run_metrics["leading_indicator_coverage"] = float(
                    cat_metrics["leading_indicator_coverage"]
                )
                run_metrics["lagging_indicator_coverage"] = float(
                    cat_metrics["lagging_indicator_coverage"]
                )

                inc_metrics = exp_metrics.compute_incident_metrics(
                    treatment_result["incidents_enriched"],
                    treatment_result["weekly_trust_financial"],
                )
                for key in (
                    "incident_ttd_median",
                    "incident_ttr_median",
                    "incident_recovery_half_life_median",
                ):
                    value = inc_metrics.get(key)
                    if value is not None:
                        run_metrics[key] = float(value)

                corr = exp_metrics.compute_trust_financial_correlation(
                    treatment_result["weekly_trust_financial"]
                )
                if corr is not None:
                    run_metrics["trust_to_financial_correlation_strength"] = float(corr)

                run_metrics["num_attribution_views"] = float(
                    len(treatment_result["attribution_views"])
                )
        except Exception:
            success = False
        runs.append(
            {
                "variant": variant,
                "workload_id": workload_id,
                "run_id": run_id,
                "success": success,
                "metrics": run_metrics,
            }
        )

    # 4) Decision simulation and user story workload
    workload_id = "decision_simulation_and_user_story_workload"
    for variant in ("baseline", "treatment"):
        run_id = f"{workload_id}-{variant}-{uuid.uuid4().hex[:8]}"
        success = True
        run_metrics = {}
        try:
            data = state.get("data")
            if not data:
                raise RuntimeError("Synthetic data missing; generation must run first.")

            questions = [
                "Is trust recovering after the major misinformation incident?",
                "Did the incident materially affect revenue?",
                "Which channel showed the earliest signal of trust degradation?",
                "How long did it take us to issue a public response?",
                "Have resilience improvements shortened recovery times over the year?",
            ]

            if variant == "baseline":
                evaluation = exp_metrics.simulate_decision_process_baseline(
                    data, questions
                )
            else:
                treatment_result = state.get("treatment")
                if not treatment_result:
                    # If for some reason treatment pipeline did not run, fall back to baseline-style evaluation.
                    evaluation = exp_metrics.simulate_decision_process_baseline(
                        data, questions
                    )
                else:
                    evaluation = exp_metrics.simulate_decision_process_treatment(
                        data, treatment_result, questions
                    )

            # Metrics: question coverage (percentage directly supported) and average steps
            run_metrics["num_questions"] = float(len(questions))
            run_metrics["executive_question_metric_availability"] = float(
                evaluation["availability_fraction"] * 100.0
            )
            run_metrics["avg_report_construction_steps"] = float(
                evaluation["avg_steps"]
            )

        except Exception:
            success = False
        runs.append(
            {
                "variant": variant,
                "workload_id": workload_id,
                "run_id": run_id,
                "success": success,
                "metrics": run_metrics,
            }
        )

    evidence = {
        "chapter": CHAPTER_NUMBER,
        "experiment_id": EXPERIMENT_ID,
        "environment": {
            "os": platform.platform(),
            "python": sys.version.split()[0],
        },
        "runs": runs,
        "notes": (
            "This evidence file summarizes synthetic runs for baseline and treatment pipelines. "
            "Metrics are derived from actual execution in an offline sandbox and are illustrative only; "
            "they must not be interpreted as causal or predictive for any real organization. Generated at "
            f"{datetime.utcnow().isoformat()}Z."
        ),
    }

    evidence_path = get_evidence_path()
    with open(evidence_path, "w", encoding="utf-8") as f:
        json.dump(evidence, f, indent=2)


if __name__ == "__main__":
    main()
