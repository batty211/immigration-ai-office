from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.db import Base, engine
from app import models  # noqa: F401
from app.routes.gmail import router as gmail_router


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(title="Immigration AI Office Backend", lifespan=lifespan)

app.include_router(gmail_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
