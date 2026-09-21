from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.auth.session import get_patient_id
from app.db.database import get_session
from app.sync.fhir_client import fhir_get, fhir_search_all
from app.sync.service import run_sync

router = APIRouter(prefix="/sync", tags=["sync"])


@router.post("")
def sync(session: Session = Depends(get_session)):
    return run_sync(session)


@router.get("/debug/patient")
def debug_patient():
    return fhir_get("Patient/{}".format(get_patient_id()))


@router.get("/debug/observations")
def debug_observations():
    return fhir_search_all("Observation", {"patient": get_patient_id(), "category": "laboratory"})


@router.get("/debug/reports")
def debug_reports():
    return fhir_search_all("DiagnosticReport", {"patient": get_patient_id()})


@router.get("/debug/documents")
def debug_documents():
    return fhir_search_all("DocumentReference", {"patient": get_patient_id()})
