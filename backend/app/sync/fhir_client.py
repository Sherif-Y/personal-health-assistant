import httpx

from app.auth.session import get_valid_access_token
from app.config import settings


def fhir_get(path, params=None):
    """GET a FHIR path (relative to the FHIR base URL, or a full next-page URL)."""
    access_token = get_valid_access_token()
    url = path if path.startswith("http") else "{}/{}".format(settings.epic_fhir_base_url, path)
    response = httpx.get(
        url,
        params=params,
        headers={
            "Authorization": "Bearer {}".format(access_token),
            "Accept": "application/fhir+json",
        },
        timeout=30,
    )
    if response.status_code >= 400:
        raise RuntimeError(
            "FHIR request failed ({}): {} -- headers: {} -- body: {}".format(
                response.status_code, url, dict(response.headers), response.text
            )
        )
    return response.json()


def fhir_search_all(resource_type, params):
    """Follow Bundle next-links to collect every page of a search.

    Search bundles can include non-matching entries (e.g. an informational
    OperationOutcome disclaimer) alongside real results, so entries are
    filtered to the requested resource type.
    """
    entries = []
    bundle = fhir_get(resource_type, params)
    while True:
        entries.extend(
            e["resource"]
            for e in bundle.get("entry", [])
            if e.get("resource", {}).get("resourceType") == resource_type
        )
        next_link = next((l["url"] for l in bundle.get("link", []) if l.get("relation") == "next"), None)
        if not next_link:
            break
        bundle = fhir_get(next_link)
    return entries
