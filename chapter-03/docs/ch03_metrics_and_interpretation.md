# Chapter 3 Metrics and Interpretation

This document explains the core metrics produced by this experiment in executive-friendly terms.

## Key Concepts

### Baseline vs. Integrated Stack

- **Baseline (Heuristics-only Monitoring)**
  - Uses simple keyword matches (e.g., "BrandX", "fake", "boycott").
  - Raises alerts when enough keyword hits occur in a 15-minute window.
  - Treats all channels the same.

- **Integrated Stack (Heuristics + ML-like Score + Human Review)**
  - Still considers keywords and volumes,
  - Adds a deterministic "ML-like" score per event (based on language, reputation, bot-likelihood, engagement),
  - Adjusts sensitivity by channel (e.g., more sensitive to dark_web and owned),
  - Routes borderline cases for human review (simulated here by labels embedded in the synthetic data).

In practice, the integrated stack is closer to what a modern vendor or in-house system would look like.

## Metrics in This Prototype

The synthetic experiment reports a compact set of numeric metrics that are robust in an offline sandbox. They are intended as stand-ins for the richer metrics described in the chapter.

### detected_misinfo_events

> Number of true misinformation events that were associated with at least one alert.

- Higher is better: indicates better coverage of harmful content.
- Normalized in other contexts as part of **recall**.

### total_alerts

> Total number of alerts raised in the run.

- Includes both helpful and noisy alerts.
- Important for understanding alert fatigue and workload.

### true_alerts

> Alerts that included at least one true misinformation event.

- Indicates how often the system is "right" when it complains.

### false_alerts

> Alerts whose events contained no true misinformation.

- Direct measure of noise.
- High false-alert counts translate into wasted analyst time and frustrated executives.

### precision

> `true_alerts / total_alerts` (0 if no alerts).

- Answers: **When the system alerts, how often is it about real misinformation?**
- High precision = fewer "cry wolf" moments.

### recall_event_level

> `detected_misinfo_events / total_true_misinfo_events` (0 if no true events).

- Answers: **Of all misinformation events, what fraction did we catch?**
- Higher recall = better coverage.

## How to Use These Metrics in Discussion

- **Comparing Baseline vs. Integrated**
  - If the integrated stack shows meaningfully higher `recall_event_level` with similar or better `precision`, it supports investment in layered detection.
  - If precision drops but recall increases, discuss whether your organization is willing to tolerate more noise to catch more threats.

- **Per-workload Storytelling**
  - **WL1 (Slow-burn deepfake)**: Look for improved detection of early dark_web and low-volume signals under the integrated stack.
  - **WL2 (Flash boycott)**: Examine whether the integrated stack can prioritize real risk in the spike without overwhelming executives.
  - **WL3 (Background chatter)**: Ensure that the integrated stack does not generate more noise than the baseline when nothing significant is happening.

These simplified metrics are meant to enable clear conversations about **coverage**, **latency**, **precision**, and **operational cost** without requiring you to become a technologist.
