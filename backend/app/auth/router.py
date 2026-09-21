import time

from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse

from app.auth import token_store
from app.auth.epic_oauth import build_authorize_url, exchange_code_for_tokens, refresh_tokens
from app.auth.pkce import generate_code_challenge, generate_code_verifier, generate_state
from app.auth.session import store_tokens

router = APIRouter(prefix="/auth", tags=["auth"])

# Single-user local app: one pending authorization at a time is enough.
_pending_auth = {}


@router.get("/login")
def login():
    state = generate_state()
    code_verifier = generate_code_verifier()
    code_challenge = generate_code_challenge(code_verifier)
    _pending_auth[state] = code_verifier
    return RedirectResponse(build_authorize_url(state, code_challenge))


@router.get("/callback")
def callback(code: str = None, state: str = None, error: str = None, error_description: str = None):
    if error:
        raise HTTPException(status_code=400, detail="Epic returned an error: {} ({})".format(error, error_description))

    code_verifier = _pending_auth.pop(state, None)
    if not code_verifier:
        raise HTTPException(status_code=400, detail="Unknown or expired state parameter")

    tokens = exchange_code_for_tokens(code, code_verifier)
    store_tokens(tokens)

    return HTMLResponse(
        "<html><body style='font-family: sans-serif; padding: 40px;'>"
        "<h2>Connected to MyChart</h2>"
        "<p>Authorization succeeded. You can close this tab and return to the app.</p>"
        "</body></html>"
    )


@router.get("/status")
def status():
    has_refresh_token = token_store.get_refresh_token() is not None
    access_token, expires_at = token_store.get_access_token()
    return {
        "connected": has_refresh_token,
        "access_token_valid": bool(access_token and expires_at and expires_at > time.time()),
        "granted_scope": token_store.get_granted_scope(),
    }


@router.post("/refresh")
def refresh():
    current_refresh_token = token_store.get_refresh_token()
    if not current_refresh_token:
        raise HTTPException(status_code=400, detail="No stored refresh token; complete /auth/login first")

    tokens = refresh_tokens(current_refresh_token)
    store_tokens(tokens)
    return {"refreshed": True}
