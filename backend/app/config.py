import os
from pathlib import Path

from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BACKEND_DIR / ".env")


def _require(name):
    value = os.environ.get(name)
    if not value:
        raise RuntimeError("Missing required environment variable: {}".format(name))
    return value


class Settings:
    epic_client_id = _require("EPIC_CLIENT_ID")
    epic_client_secret = _require("EPIC_CLIENT_SECRET")
    epic_authorize_url = _require("EPIC_AUTHORIZE_URL")
    epic_token_url = _require("EPIC_TOKEN_URL")
    epic_fhir_base_url = _require("EPIC_FHIR_BASE_URL")
    epic_redirect_uri = _require("EPIC_REDIRECT_URI")
    epic_scopes = os.environ.get("EPIC_SCOPES", "openid fhirUser launch/patient offline_access")

    anthropic_api_key = os.environ.get("ANTHROPIC_API_KEY", "")

    frontend_origin = os.environ.get("FRONTEND_ORIGIN", "http://localhost:5173")
    database_path = BACKEND_DIR / os.environ.get("DATABASE_PATH", "./data/health.db")


settings = Settings()
