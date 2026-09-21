import keyring

_SERVICE = "personal-health-assistant"
_REFRESH_TOKEN_KEY = "epic_refresh_token"
_PATIENT_ID_KEY = "epic_patient_id"

# Access tokens are short-lived (typically ~1hr) and are kept in memory only,
# not persisted to the keychain. They are re-derived from the refresh token
# on backend restart via /auth/refresh.
_access_token_cache = {"token": None, "expires_at": None, "granted_scope": None}


def save_refresh_token(token):
    keyring.set_password(_SERVICE, _REFRESH_TOKEN_KEY, token)


def get_refresh_token():
    return keyring.get_password(_SERVICE, _REFRESH_TOKEN_KEY)


def delete_refresh_token():
    try:
        keyring.delete_password(_SERVICE, _REFRESH_TOKEN_KEY)
    except keyring.errors.PasswordDeleteError:
        pass


def set_access_token(token, expires_at, granted_scope=None):
    _access_token_cache["token"] = token
    _access_token_cache["expires_at"] = expires_at
    _access_token_cache["granted_scope"] = granted_scope


def get_access_token():
    return _access_token_cache["token"], _access_token_cache["expires_at"]


def get_granted_scope():
    return _access_token_cache["granted_scope"]


def save_patient_id(patient_id):
    keyring.set_password(_SERVICE, _PATIENT_ID_KEY, patient_id)


def get_patient_id():
    return keyring.get_password(_SERVICE, _PATIENT_ID_KEY)
