import time

from app.auth import token_store
from app.auth.epic_oauth import refresh_tokens


def store_tokens(tokens):
    access_token = tokens["access_token"]
    expires_in = tokens.get("expires_in", 3600)
    token_store.set_access_token(access_token, time.time() + expires_in, tokens.get("scope"))

    # Epic issues rolling refresh tokens: always persist the newest one.
    new_refresh_token = tokens.get("refresh_token")
    if new_refresh_token:
        token_store.save_refresh_token(new_refresh_token)

    patient_id = tokens.get("patient")
    if patient_id:
        token_store.save_patient_id(patient_id)

    return access_token


class NotConnectedError(Exception):
    pass


def get_valid_access_token():
    access_token, expires_at = token_store.get_access_token()
    if access_token and expires_at and expires_at > time.time() + 30:
        return access_token

    refresh_token = token_store.get_refresh_token()
    if not refresh_token:
        raise NotConnectedError("Not connected to MyChart; complete /auth/login first")

    tokens = refresh_tokens(refresh_token)
    return store_tokens(tokens)


def get_patient_id():
    patient_id = token_store.get_patient_id()
    if not patient_id:
        raise NotConnectedError("No patient context stored; complete /auth/login first")
    return patient_id
