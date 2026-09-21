from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlmodel import Session

from app.db.database import get_session
from app.llm.client import ask

router = APIRouter(tags=["chat"])


class ChatRequest(BaseModel):
    message: str


@router.post("/chat")
def chat(request: ChatRequest, session: Session = Depends(get_session)):
    return {"reply": ask(session, request.message)}
