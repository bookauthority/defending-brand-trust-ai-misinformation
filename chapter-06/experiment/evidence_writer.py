import os


def ensure_evidence_dir() -> str:
    """Return the directory where evidence should be written.

    Uses BOOKMAS_EVIDENCE_DIR if set, otherwise /evidence. Ensures the
    directory exists.
    """

    evidence_dir = os.environ.get("BOOKMAS_EVIDENCE_DIR", "/evidence")
    os.makedirs(evidence_dir, exist_ok=True)
    return evidence_dir
