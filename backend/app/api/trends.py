from typing import Optional

from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from app.db.database import get_session
from app.db.models import LabResult

router = APIRouter(tags=["trends"])


@router.get("/trends/metrics")
def list_trend_metrics(session: Session = Depends(get_session)):
    """Distinct trackable metrics (grouped by LOINC code, falling back to name), tagged
    with the category from their most recent draw so the picker can group the same way
    as Lab Results."""
    all_results = session.exec(select(LabResult).order_by(LabResult.collected_at.asc())).all()

    by_key = {}
    for r in all_results:
        key = r.loinc_code or r.display_name
        by_key.setdefault(key, []).append(r)

    metrics = []
    for history in by_key.values():
        latest = history[-1]
        metrics.append(
            {
                "loinc_code": latest.loinc_code,
                "display_name": latest.display_name,
                "category": latest.category or "Other Labs",
                "data_points": len(history),
            }
        )
    metrics.sort(key=lambda m: (m["category"], m["display_name"]))
    return metrics


@router.get("/trends")
def get_trend(loinc_code: Optional[str] = None, display_name: Optional[str] = None, session: Session = Depends(get_session)):
    query = select(LabResult)
    if loinc_code:
        query = query.where(LabResult.loinc_code == loinc_code)
    elif display_name:
        query = query.where(LabResult.display_name == display_name)
    else:
        return {"error": "loinc_code or display_name is required"}

    results = session.exec(query.order_by(LabResult.collected_at.asc())).all()
    return {
        "display_name": results[0].display_name if results else display_name,
        "unit": results[0].unit if results else None,
        "points": [
            {
                "collected_at": r.collected_at,
                "value": r.value,
                "value_text": r.value_text,
                "reference_range_low": r.reference_range_low,
                "reference_range_high": r.reference_range_high,
            }
            for r in results
        ],
    }
