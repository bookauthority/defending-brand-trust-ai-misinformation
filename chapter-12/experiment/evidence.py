from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict


def _get_evidence_dir() -> Path:
    """Return the directory where evidence should be written.

    Respects the BOOKMAS_EVIDENCE_DIR environment variable if set,
    otherwise defaults to /evidence.
    """

    env_dir = os.environ.get("BOOKMAS_EVIDENCE_DIR")
    if env_dir:
        base = Path(env_dir)
    else:
        base = Path("/evidence")
    return base


def write_evidence(evidence: Dict[str, Any]) -> None:
    """Write the evidence JSON document to results.json in the evidence dir."""

    evidence_dir = _get_evidence_dir()
    evidence_dir.mkdir(parents=True, exist_ok=True)
    output_path = evidence_dir / "results.json"

    with output_path.open("w", encoding="utf-8") as f:
        json.dump(evidence, f, indent=2, sort_keys=True)
