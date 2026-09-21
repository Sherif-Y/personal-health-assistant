from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.chat import router as chat_router
from app.api.labs import router as labs_router
from app.api.reports import router as reports_router
from app.api.summary import router as summary_router
from app.api.trends import router as trends_router
from app.auth.router import router as auth_router
from app.config import settings
from app.db.database import create_db_and_tables
from app.sync.router import router as sync_router

app = FastAPI(title="Personal Health Assistant")


@app.on_event("startup")
def on_startup():
    create_db_and_tables()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(sync_router)
app.include_router(labs_router)
app.include_router(trends_router)
app.include_router(reports_router)
app.include_router(summary_router)
app.include_router(chat_router)


@app.get("/api/health")
def health():
    return {"status": "ok"}
