from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date, timedelta
from typing import Dict, List

from .utils import build_weekly_buckets, mean


@dataclass
class MetricCatalogEntry:
    metric_name: str
    business_question: str
    definition: str
    formula: str
    data_sources: List[str]
    unit: str
    frequency: str
    owner_role: str
    primary_audience: str
    indicator_class: str  # leading, lagging, neutral
    status: str  # defined, implemented, planned


def build_metric_catalog() -> List[MetricCatalogEntry]:
    """Define a small but non-trivial metric catalog for the treatment condition."""

    entries = [
        MetricCatalogEntry(
            metric_name="channel_weighted_sentiment_index",
            business_question="How is overall brand trust evolving across channels?",
            definition="Volume-weighted average sentiment across all channels per period.",
            formula="sum(sentiment * volume) / sum(volume)",
            data_sources=["sentiment"],
            unit="index_points",
            frequency="weekly",
            owner_role="head_of_comms",
            primary_audience="exec_team",
            indicator_class="leading",
            status="implemented",
        ),
        MetricCatalogEntry(
            metric_name="misinformation_mention_rate",
            business_question="How prominent are misinformation narratives in observed conversations?",
            definition="Proportion of mentions that explicitly reference misinformation-related terms.",
            formula="misinformation_mentions / volume",
            data_sources=["sentiment"],
            unit="ratio",
            frequency="weekly",
            owner_role="trust_and_safety_lead",
            primary_audience="exec_team",
            indicator_class="leading",
            status="implemented",
        ),
        MetricCatalogEntry(
            metric_name="trust_volatility",
            business_question="How unstable is trust sentiment over time?",
            definition="Standard deviation of channel-weighted sentiment over a rolling window.",
            formula="std(channel_weighted_sentiment_index[window])",
            data_sources=["sentiment"],
            unit="index_points",
            frequency="weekly",
            owner_role="analytics_lead",
            primary_audience="exec_team",
            indicator_class="leading",
            status="defined",
        ),
        MetricCatalogEntry(
            metric_name="incident_ttd_hours",
            business_question="How quickly do we detect misinformation incidents?",
            definition="Median time from first alert to detection across incidents in period.",
            formula="median(detection_time - alert_time)",
            data_sources=["incident_log"],
            unit="hours",
            frequency="quarterly",
            owner_role="head_of_security_ops",
            primary_audience="exec_team",
            indicator_class="neutral",
            status="implemented",
        ),
        MetricCatalogEntry(
            metric_name="incident_ttr_hours",
            business_question="How quickly do we respond publicly to misinformation incidents?",
            definition="Median time from detection to first public statement.",
            formula="median(public_statement_time - detection_time)",
            data_sources=["incident_log"],
            unit="hours",
            frequency="quarterly",
            owner_role="head_of_comms",
            primary_audience="exec_team",
            indicator_class="neutral",
            status="implemented",
        ),
        MetricCatalogEntry(
            metric_name="incident_recovery_half_life_days",
            business_question="How quickly do key KPIs recover after an incident?",
            definition="Median days for sentiment index to recover half of incident-induced loss.",
            formula="median(recovery_half_life_days)",
            data_sources=["sentiment", "incident_log"],
            unit="days",
            frequency="quarterly",
            owner_role="analytics_lead",
            primary_audience="exec_team",
            indicator_class="lagging",
            status="defined",
        ),
        MetricCatalogEntry(
            metric_name="revenue_trust_correlation",
            business_question="How strongly is revenue associated with trust index movements?",
            definition="Pearson correlation between trust index and revenue over time.",
            formula="corr(channel_weighted_sentiment_index, revenue)",
            data_sources=["sentiment", "financial"],
            unit="correlation_coefficient",
            frequency="quarterly",
            owner_role="fp_and_a_lead",
            primary_audience="board",
            indicator_class="neutral",
            status="implemented",
        ),
        MetricCatalogEntry(
            metric_name="revenue",
            business_question="What is our top-line performance?",
            definition="Total recognized revenue per week.",
            formula="sum(revenue)",
            data_sources=["financial"],
            unit="currency",
            frequency="weekly",
            owner_role="cfo",
            primary_audience="board",
            indicator_class="lagging",
            status="implemented",
        ),
        MetricCatalogEntry(
            metric_name="nps",
            business_question="How satisfied are customers overall?",
            definition="Net Promoter Score based on periodic surveys (synthetic here).",
            formula="mean(nps)",
            data_sources=["financial"],
            unit="index_points",
            frequency="monthly",
            owner_role="head_of_customer_experience",
            primary_audience="exec_team",
            indicator_class="lagging",
            status="implemented",
        ),
    ]
    return entries


def _enrich_incidents(incidents: List[object]) -> List[Dict[str, object]]:
    """Compute durations (TTD, TTR, containment, total)."""

    enriched: List[Dict[str, object]] = []
    for inc in incidents:
        ttd = (inc.detection_time - inc.alert_time).total_seconds() / 3600.0
        ttr = (inc.public_statement_time - inc.detection_time).total_seconds() / 3600.0
        contain = (
            inc.containment_time - inc.public_statement_time
        ).total_seconds() / 3600.0
        total = (inc.resolved_time - inc.alert_time).total_seconds() / 3600.0
        record = {
            "incident_id": inc.incident_id,
            "type": inc.type,
            "severity": inc.severity,
            "channel": inc.channel,
            "is_misinformation": inc.is_misinformation,
            "alert_time": inc.alert_time,
            "detection_time": inc.detection_time,
            "classification_time": inc.classification_time,
            "public_statement_time": inc.public_statement_time,
            "containment_time": inc.containment_time,
            "resolved_time": inc.resolved_time,
            "ttd_hours": float(ttd),
            "ttr_hours": float(ttr),
            "containment_duration_hours": float(contain),
            "total_duration_hours": float(total),
        }
        enriched.append(record)
    return enriched


def _build_weekly_trust_financial(data: Dict[str, object]) -> List[Dict[str, float]]:
    days = data["time_index"]
    sentiment = data["sentiment"]
    financial = data["financial"]

    buckets = build_weekly_buckets(days)
    sent_by_day = {i: [] for i in range(len(days))}
    for rec in sentiment:
        idx = (rec.day - days[0]).days
        sent_by_day.setdefault(idx, []).append(rec)

    fin_by_day = {i: None for i in range(len(days))}
    for rec in financial:
        idx = (rec.day - days[0]).days
        fin_by_day[idx] = rec

    weekly: List[Dict[str, float]] = []
    for bucket in buckets:
        if not bucket.indices:
            continue
        total_sentiment = 0.0
        total_volume = 0.0
        misinfo_mentions = 0.0
        revenues = []
        for idx in bucket.indices:
            for s in sent_by_day.get(idx, []):
                total_sentiment += s.sentiment * s.volume
                total_volume += s.volume
                misinfo_mentions += s.misinformation_mentions
            f = fin_by_day.get(idx)
            if f is not None:
                revenues.append(f.revenue)
        if total_volume == 0:
            trust_index = 0.0
            misinfo_rate = 0.0
        else:
            trust_index = total_sentiment / total_volume
            misinfo_rate = misinfo_mentions / total_volume
        weekly.append(
            {
                "week_start_ordinal": float(bucket.start_date.toordinal()),
                "channel_weighted_sentiment_index": float(trust_index),
                "misinformation_mention_rate": float(misinfo_rate),
                "revenue": float(mean(revenues) if revenues else 0.0),
            }
        )
    return weekly


def _build_attribution_views(
    weekly_trust_financial: List[Dict[str, float]],
    incidents_enriched: List[Dict[str, object]],
) -> List[Dict[str, object]]:
    views: List[Dict[str, object]] = []
    if not weekly_trust_financial or not incidents_enriched:
        return views

    for inc in incidents_enriched:
        alert = inc["alert_time"].date()
        resolved = inc["resolved_time"].date()
        baseline_start = alert - timedelta(days=28)
        baseline_end = alert - timedelta(days=1)
        comparison_start = alert
        comparison_end = resolved

        for metric_name in ("channel_weighted_sentiment_index", "revenue"):
            base_vals = []
            comp_vals = []
            for row in weekly_trust_financial:
                wk_start = date.fromordinal(int(row["week_start_ordinal"]))
                if baseline_start <= wk_start <= baseline_end:
                    base_vals.append(row[metric_name])
                if comparison_start <= wk_start <= comparison_end:
                    comp_vals.append(row[metric_name])
            if not base_vals or not comp_vals:
                continue
            base_avg = mean(base_vals)
            comp_avg = mean(comp_vals)
            delta = comp_avg - base_avg
            delta_pct = 0.0 if base_avg == 0 else (delta / base_avg) * 100.0
            views.append(
                {
                    "view_id": f"{inc['incident_id']}_{metric_name}",
                    "incident_id": inc["incident_id"],
                    "metric_name": metric_name,
                    "baseline_window": {
                        "start": baseline_start.isoformat(),
                        "end": baseline_end.isoformat(),
                    },
                    "comparison_window": {
                        "start": comparison_start.isoformat(),
                        "end": comparison_end.isoformat(),
                    },
                    "baseline_value": float(base_avg),
                    "comparison_value": float(comp_avg),
                    "delta_value": float(delta),
                    "delta_percentage": float(delta_pct),
                    "notes": "Simple pre/post average comparison; not a causal estimate.",
                    "method": "pre_post",
                }
            )
    return views


def run_treatment_pipeline(data: Dict[str, object]) -> Dict[str, object]:
    """Run the treatment metric framework on synthetic data and return artifacts.

    This corresponds to the treatment pipeline workload in the specification.
    """

    metric_catalog = build_metric_catalog()
    incidents_enriched = _enrich_incidents(data["incidents"])
    weekly_trust_financial = _build_weekly_trust_financial(data)
    attribution_views = _build_attribution_views(
        weekly_trust_financial, incidents_enriched
    )

    # The return value is a simple container of data structures used by metrics.py
    return {
        "metric_catalog": [asdict(e) for e in metric_catalog],
        "incidents_enriched": incidents_enriched,
        "weekly_trust_financial": weekly_trust_financial,
        "attribution_views": attribution_views,
    }
