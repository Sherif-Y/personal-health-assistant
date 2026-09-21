from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.db.database import get_session
from app.llm.client import ask
from app.llm.prompts import SUMMARY_REQUEST

router = APIRouter(tags=["summary"])

# Simple in-memory cache: regenerated whenever a new sync completes (Phase 2 can
# invalidate this once wired up); avoids re-calling the LLM on every dashboard load.
_cache = {"text": None}


@router.get("/summary")
def get_summary(session: Session = Depends(get_session), refresh: bool = False):
    if _cache["text"] is None or refresh:
        _cache["text"] = ask(session, SUMMARY_REQUEST)
    return {"summary": _cache["text"]}
