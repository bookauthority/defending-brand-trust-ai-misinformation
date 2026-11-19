from __future__ import annotations

"""Metric helpers for the Chapter 12 readiness simulation."""

from typing import Union


Number = Union[int, float]


def clamp_score(value: Number, minimum: Number = 1.0, maximum: Number = 5.0) -> float:
    """Clamp a numeric score into the given range and return as float."""

    if value < minimum:
        return float(minimum)
    if value > maximum:
        return float(maximum)
    return float(value)
