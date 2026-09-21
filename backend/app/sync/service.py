from datetime import datetime, timezone

from sqlmodel import Session, select

from app.auth.session import get_patient_id
from app.db.models import LabResult, Report, SyncMetadata
from app.sync.binary import fetch_narrative_text
from app.sync.fhir_client import fhir_search_all
from app.sync.normalize import diagnostic_report_to_report, document_reference_to_report, observation_to_lab_result


def _parse_fhir_datetime(value):
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _upsert(session, model, fhir_id, fields):
    existing = session.exec(select(model).where(model.fhir_id == fhir_id)).first()
    fields["collected_at"] = _parse_fhir_datetime(fields.get("collected_at"))
    if existing:
        for key, value in fields.items():
            setattr(existing, key, value)
        session.add(existing)
    else:
        session.add(model(**fields))


def _fill_narrative(fields):
    if not fields.get("narrative_text") and fields.get("source_attachment_url"):
        try:
            fields["narrative_text"] = fetch_narrative_text(
                fields["source_attachment_url"], fields.get("source_attachment_content_type")
            )
        except Exception:
            # Binary resource access isn't granted yet (out of scope for now) — keep
            # report metadata (title/type/date) rather than failing the whole sync.
            pass
    return fields


def _mark_synced(session, resource_type):
    existing = session.exec(select(SyncMetadata).where(SyncMetadata.resource_type == resource_type)).first()
    now = datetime.now(timezone.utc)
    if existing:
        existing.last_synced_at = now
        session.add(existing)
    else:
        session.add(SyncMetadata(resource_type=resource_type, last_synced_at=now))


def run_sync(session: Session):
    patient_id = get_patient_id()
    counts = {}

    observations = fhir_search_all("Observation", {"patient": patient_id, "category": "laboratory"})
    for obs in observations:
        _upsert(session, LabResult, obs["id"], observation_to_lab_result(obs))
    counts["lab_results"] = len(observations)
    _mark_synced(session, "Observation")

    reports = fhir_search_all("DiagnosticReport", {"patient": patient_id})
    for report in reports:
        _upsert(session, Report, report["id"], _fill_narrative(diagnostic_report_to_report(report)))
    counts["diagnostic_reports"] = len(reports)
    _mark_synced(session, "DiagnosticReport")

    documents = fhir_search_all("DocumentReference", {"patient": patient_id})
    for doc in documents:
        _upsert(session, Report, doc["id"], _fill_narrative(document_reference_to_report(doc)))
    counts["documents"] = len(documents)
    _mark_synced(session, "DocumentReference")

    session.commit()
    return counts
