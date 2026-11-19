import json
import math
import random
import string
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Iterable, List


ISO_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime(ISO_FORMAT)


def isoformat(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    dt = dt.astimezone(timezone.utc)
    return dt.strftime(ISO_FORMAT)


def parse_iso(ts: str) -> datetime:
    return datetime.strptime(ts, ISO_FORMAT).replace(tzinfo=timezone.utc)


def gen_id(prefix: str, rng: random.Random) -> str:
    suffix = "".join(rng.choices(string.ascii_lowercase + string.digits, k=8))
    return f"{prefix}_{suffix}"


@dataclass
class SyntheticAlert:
    alert_id: str
    timestamp_detected: datetime
    severity_score: int
    source_channel: str


def median(values: List[float]) -> float:
    if not values:
        return math.nan
    sorted_vals = sorted(values)
    n = len(sorted_vals)
    mid = n // 2
    if n % 2 == 1:
        return float(sorted_vals[mid])
    return float((sorted_vals[mid - 1] + sorted_vals[mid]) / 2.0)


def percentile(values: List[float], p: float) -> float:
    if not values:
        return math.nan
    if p <= 0:
        return float(min(values))
    if p >= 100:
        return float(max(values))
    sorted_vals = sorted(values)
    k = (len(sorted_vals) - 1) * (p / 100.0)
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return float(sorted_vals[int(k)])
    d0 = sorted_vals[f] * (c - k)
    d1 = sorted_vals[c] * (k - f)
    return float(d0 + d1)


def write_jsonl(path: str, rows: Iterable[Dict[str, Any]]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row) + "\n")


def read_jsonl(path: str) -> List[Dict[str, Any]]:
    data: List[Dict[str, Any]] = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            data.append(json.loads(line))
    return data
