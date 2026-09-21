from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.db.database import get_session
from app.db.models import Report

router = APIRouter(tags=["reports"])


@router.get("/reports")
def list_reports(report_type: Optional[str] = None, session: Session = Depends(get_session)):
    query = select(Report)
    if report_type:
        query = query.where(Report.report_type == report_type)
    reports = session.exec(query.order_by(Report.collected_at.desc())).all()
    return reports


@router.get("/reports/{report_id}")
def get_report(report_id: int, session: Session = Depends(get_session)):
    report = session.get(Report, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report
