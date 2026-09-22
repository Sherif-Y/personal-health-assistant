def _coding_text(codeable_concept):
    if not codeable_concept:
        return None
    if codeable_concept.get("text"):
        return codeable_concept["text"]
    codings = codeable_concept.get("coding") or []
    return codings[0].get("display") if codings else None


def _loinc_code(codeable_concept):
    for coding in (codeable_concept or {}).get("coding", []):
        if coding.get("system") == "http://loinc.org":
            return coding.get("code")
    return None


def _category_text(resource):
    categories = resource.get("category") or []
    if not categories:
        return None
    first = categories[0]
    return _coding_text(first) if isinstance(first, dict) else None


def diagnostic_report_panel_name(report):
    """The human-readable panel name (e.g. 'Comprehensive Metabolic Panel')."""
    return _coding_text(report.get("code"))


def extract_result_observation_ids(report):
    """FHIR ids of the Observations grouped under this DiagnosticReport's `result` list."""
    ids = []
    for ref in report.get("result") or []:
        reference = ref.get("reference", "")
        if reference:
            ids.append(reference.split("/")[-1])
    return ids


def observation_to_lab_result(obs, panel_name=None):
    """Normalize a FHIR Observation (US Core Laboratory Result) into LabResult fields.

    `panel_name` (the parent DiagnosticReport's name, e.g. 'CBC With Differential')
    is preferred over the generic FHIR category ('laboratory') for grouping in the UI.
    """
    ref_low = ref_high = ref_text = None
    ranges = obs.get("referenceRange") or []
    if ranges:
        ref_low = ranges[0].get("low", {}).get("value")
        ref_high = ranges[0].get("high", {}).get("value")
        ref_text = ranges[0].get("text")

    value = None
    value_text = None
    unit = None
    if "valueQuantity" in obs:
        value = obs["valueQuantity"].get("value")
        unit = obs["valueQuantity"].get("unit")
    elif "valueString" in obs:
        value_text = obs["valueString"]
    elif "valueCodeableConcept" in obs:
        value_text = _coding_text(obs["valueCodeableConcept"])

    return {
        "fhir_id": obs["id"],
        "loinc_code": _loinc_code(obs.get("code")),
        "display_name": _coding_text(obs.get("code")) or "Unknown test",
        "category": panel_name or _category_text(obs) or "Other Labs",
        "value": value,
        "value_text": value_text,
        "unit": unit,
        "reference_range_low": ref_low,
        "reference_range_high": ref_high,
        "reference_range_text": ref_text,
        "collected_at": obs.get("effectiveDateTime") or obs.get("issued"),
    }


def diagnostic_report_to_report(report):
    """Normalize a FHIR DiagnosticReport into Report fields."""
    presented_forms = report.get("presentedForm") or []
    attachment = presented_forms[0] if presented_forms else {}

    return {
        "fhir_id": report["id"],
        "resource_type": "DiagnosticReport",
        "report_type": _category_text(report) or "Report",
        "title": _coding_text(report.get("code")) or "Untitled report",
        "narrative_text": report.get("conclusion"),
        "source_attachment_url": attachment.get("url"),
        "source_attachment_content_type": attachment.get("contentType"),
        "collected_at": report.get("effectiveDateTime") or report.get("issued"),
    }


def document_reference_to_report(doc):
    """Normalize a FHIR DocumentReference (US Core Clinical Notes) into Report fields."""
    contents = doc.get("content") or []
    attachment = contents[0].get("attachment", {}) if contents else {}

    return {
        "fhir_id": doc["id"],
        "resource_type": "DocumentReference",
        "report_type": _category_text(doc) or _coding_text(doc.get("type")) or "Clinical Note",
        "title": _coding_text(doc.get("type")) or attachment.get("title") or "Untitled note",
        "narrative_text": None,  # DocumentReference rarely carries inline text; see source_attachment_url
        "source_attachment_url": attachment.get("url"),
        "source_attachment_content_type": attachment.get("contentType"),
        "collected_at": doc.get("date"),
    }
