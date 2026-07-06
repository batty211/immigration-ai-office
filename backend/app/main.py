from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.db import Base, engine
from app import models  # noqa: F401
from app.routes.emails import router as emails_router
from app.routes.gmail import router as gmail_router


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(title="Immigration AI Office Backend", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_base_url.rstrip("/")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(gmail_router)
app.include_router(emails_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
