from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlmodel import Session, func, select

from app.db.database import get_session
from app.db.models import LabResult

router = APIRouter(tags=["trends"])


@router.get("/trends/metrics")
def list_trend_metrics(session: Session = Depends(get_session)):
    """Distinct trackable metrics (grouped by LOINC code, falling back to name)."""
    rows = session.exec(
        select(LabResult.loinc_code, LabResult.display_name, func.count(LabResult.id)).group_by(
            LabResult.loinc_code, LabResult.display_name
        )
    ).all()
    return [
        {"loinc_code": loinc_code, "display_name": display_name, "data_points": count}
        for loinc_code, display_name, count in rows
    ]


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
