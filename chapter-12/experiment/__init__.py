from __future__ import annotations

"""Experiment package for Chapter 12 readiness simulations.

This package provides a small offline simulation used by ``run.py`` to
produce evidence for the experiment:

    exp-ch12-readiness-sim-tabletop-redteam-v1

The intent is pedagogical: we model high-level incident response dynamics for
three workloads and compare baseline vs. treatment variants.
"""

from .config import CHAPTER_NUMBER, EXPERIMENT_ID

__all__ = ["CHAPTER_NUMBER", "EXPERIMENT_ID"]
