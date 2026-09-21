from urllib.parse import urlencode

import httpx

from app.config import settings


def build_authorize_url(state, code_challenge):
    params = {
        "response_type": "code",
        "client_id": settings.epic_client_id,
        "redirect_uri": settings.epic_redirect_uri,
        "scope": settings.epic_scopes,
        "state": state,
        "aud": settings.epic_fhir_base_url,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
    }
    return "{}?{}".format(settings.epic_authorize_url, urlencode(params))


def exchange_code_for_tokens(code, code_verifier):
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": settings.epic_redirect_uri,
        "client_id": settings.epic_client_id,
        "code_verifier": code_verifier,
    }
    response = httpx.post(
        settings.epic_token_url,
        data=data,
        auth=(settings.epic_client_id, settings.epic_client_secret),
        timeout=30,
    )
    if response.status_code >= 400:
        raise RuntimeError(
            "Token exchange failed ({}): headers={} body={}".format(
                response.status_code, dict(response.headers), response.text
            )
        )
    return response.json()


def refresh_tokens(refresh_token):
    data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": settings.epic_client_id,
    }
    response = httpx.post(
        settings.epic_token_url,
        data=data,
        auth=(settings.epic_client_id, settings.epic_client_secret),
        timeout=30,
    )
    response.raise_for_status()
    return response.json()
