from sqlmodel import select

from app.db.models import LabResult, Report

TOOL_SCHEMAS = [
    {
        "name": "get_lab_history",
        "description": "Get the full historical record of a specific lab test, including every past value and date.",
        "input_schema": {
            "type": "object",
            "properties": {
                "display_name": {"type": "string", "description": "The lab test name, e.g. 'LDL Cholesterol'"},
                "loinc_code": {"type": "string", "description": "The LOINC code, if known"},
            },
        },
    },
    {
        "name": "get_latest_panel",
        "description": "Get the most recent set of lab results (the latest panel/visit).",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "get_reference_range",
        "description": "Get the normal reference range for a specific lab test.",
        "input_schema": {
            "type": "object",
            "properties": {
                "display_name": {"type": "string"},
                "loinc_code": {"type": "string"},
            },
        },
    },
    {
        "name": "list_reports",
        "description": "List diagnostic reports and clinical notes (radiology, pathology, cardiology, etc.).",
        "input_schema": {
            "type": "object",
            "properties": {
                "report_type": {
                    "type": "string",
                    "description": "Optional filter, e.g. 'Imaging', 'Pathology and Cytology', 'Clinical Note'",
                }
            },
        },
    },
    {
        "name": "get_report",
        "description": "Get the full detail of a specific report by its id, including narrative text if available.",
        "input_schema": {
            "type": "object",
            "properties": {"report_id": {"type": "integer"}},
            "required": ["report_id"],
        },
    },
]


def _lab_result_query(session, display_name=None, loinc_code=None):
    query = select(LabResult)
    if loinc_code:
        query = query.where(LabResult.loinc_code == loinc_code)
    elif display_name:
        query = query.where(LabResult.display_name.contains(display_name))
    return session.exec(query.order_by(LabResult.collected_at.asc())).all()


def _serialize_lab_result(r: LabResult):
    return {
        "display_name": r.display_name,
        "loinc_code": r.loinc_code,
        "value": r.value,
        "value_text": r.value_text,
        "unit": r.unit,
        "reference_range_low": r.reference_range_low,
        "reference_range_high": r.reference_range_high,
        "reference_range_text": r.reference_range_text,
        "collected_at": str(r.collected_at) if r.collected_at else None,
    }


def _serialize_report(r: Report):
    return {
        "id": r.id,
        "report_type": r.report_type,
        "title": r.title,
        "narrative_text": r.narrative_text,
        "collected_at": str(r.collected_at) if r.collected_at else None,
    }


def get_lab_history(session, display_name=None, loinc_code=None):
    results = _lab_result_query(session, display_name, loinc_code)
    if not results:
        return {"found": False, "message": "No matching lab history found."}
    return {"found": True, "history": [_serialize_lab_result(r) for r in results]}


def get_latest_panel(session):
    latest = session.exec(select(LabResult).order_by(LabResult.collected_at.desc())).first()
    if not latest:
        return {"found": False, "message": "No lab results found."}
    same_visit = session.exec(
        select(LabResult).where(LabResult.collected_at == latest.collected_at)
    ).all()
    return {"found": True, "collected_at": str(latest.collected_at), "results": [_serialize_lab_result(r) for r in same_visit]}


def get_reference_range(session, display_name=None, loinc_code=None):
    results = _lab_result_query(session, display_name, loinc_code)
    if not results:
        return {"found": False, "message": "No matching lab test found."}
    latest = results[-1]
    return {
        "found": True,
        "display_name": latest.display_name,
        "reference_range_low": latest.reference_range_low,
        "reference_range_high": latest.reference_range_high,
        "reference_range_text": latest.reference_range_text,
        "unit": latest.unit,
    }


def list_reports(session, report_type=None):
    query = select(Report)
    if report_type:
        query = query.where(Report.report_type == report_type)
    reports = session.exec(query.order_by(Report.collected_at.desc())).all()
    return {"reports": [_serialize_report(r) for r in reports]}


def get_report(session, report_id):
    report = session.get(Report, report_id)
    if not report:
        return {"found": False, "message": "No report found with that id."}
    return {"found": True, "report": _serialize_report(report)}


DISPATCH = {
    "get_lab_history": get_lab_history,
    "get_latest_panel": get_latest_panel,
    "get_reference_range": get_reference_range,
    "list_reports": list_reports,
    "get_report": get_report,
}


def execute_tool(session, name, tool_input):
    handler = DISPATCH.get(name)
    if not handler:
        return {"error": "Unknown tool: {}".format(name)}
    return handler(session, **tool_input)
