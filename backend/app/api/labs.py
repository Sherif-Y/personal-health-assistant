from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlmodel import Session, select

from app.db.database import get_session
from app.db.models import LabResult

router = APIRouter(tags=["labs"])


def _is_out_of_range(result: LabResult) -> Optional[bool]:
    if result.value is None:
        return None
    if result.reference_range_low is not None and result.value < result.reference_range_low:
        return True
    if result.reference_range_high is not None and result.value > result.reference_range_high:
        return True
    if result.reference_range_low is None and result.reference_range_high is None:
        return None
    return False


def _serialize(result: LabResult):
    data = result.dict()
    data["out_of_range"] = _is_out_of_range(result)
    return data


@router.get("/labs")
def list_labs(
    category: Optional[str] = None,
    search: Optional[str] = None,
    session: Session = Depends(get_session),
):
    query = select(LabResult)
    if category:
        query = query.where(LabResult.category == category)
    if search:
        query = query.where(LabResult.display_name.contains(search))
    results = session.exec(query.order_by(LabResult.collected_at.desc())).all()

    grouped = {}
    for result in results:
        grouped.setdefault(result.category or "Uncategorized", []).append(_serialize(result))

    return {"categories": [{"category": name, "results": rows} for name, rows in grouped.items()]}
