from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from app.db.database import get_session
from app.db.models import LabResult

router = APIRouter(tags=["labs"])


def _is_out_of_range(value, low, high):
    if value is None:
        return None
    if low is not None and value < low:
        return True
    if high is not None and value > high:
        return True
    if low is None and high is None:
        return None
    return False


def _trend(current: LabResult, previous: Optional[LabResult]):
    if previous is None or previous.value is None or current.value is None or previous.value == 0:
        return None, None
    pct_change = (current.value - previous.value) / abs(previous.value) * 100
    direction = "up" if pct_change > 1 else "down" if pct_change < -1 else "flat"
    return round(pct_change, 1), direction


def _serialize(current: LabResult, previous: Optional[LabResult]):
    data = current.dict()
    data["out_of_range"] = _is_out_of_range(current.value, current.reference_range_low, current.reference_range_high)
    pct_change, direction = _trend(current, previous)
    data["previous_value"] = previous.value if previous else None
    data["previous_collected_at"] = previous.collected_at if previous else None
    data["pct_change"] = pct_change
    data["trend_direction"] = direction
    return data


@router.get("/labs")
def list_labs(
    category: Optional[str] = None,
    search: Optional[str] = None,
    session: Session = Depends(get_session),
):
    """One row per distinct test — its latest value plus trend vs. the prior draw.
    Full history per test lives in /trends, not here."""
    all_results = session.exec(select(LabResult).order_by(LabResult.collected_at.asc())).all()

    by_key = {}
    for r in all_results:
        key = r.loinc_code or r.display_name
        by_key.setdefault(key, []).append(r)

    latest_rows = []
    for history in by_key.values():
        current = history[-1]
        previous = history[-2] if len(history) > 1 else None
        latest_rows.append(_serialize(current, previous))

    if category:
        latest_rows = [r for r in latest_rows if r["category"] == category]
    if search:
        needle = search.lower()
        latest_rows = [r for r in latest_rows if needle in r["display_name"].lower()]

    latest_rows.sort(key=lambda r: r["collected_at"] or datetime.min, reverse=True)

    grouped = {}
    for row in latest_rows:
        grouped.setdefault(row["category"] or "Uncategorized", []).append(row)

    categories = [{"category": name, "results": rows} for name, rows in grouped.items()]
    categories.sort(key=lambda c: c["category"])

    return {"categories": categories}
