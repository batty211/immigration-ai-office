from __future__ import annotations

import secrets

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import RedirectResponse
from googleapiclient.errors import HttpError
from sqlalchemy.orm import Session

from app.config import settings
from app.db import get_db
from app.gmail_service import (
    GmailConfigurationError,
    GmailIntegrationError,
    GmailService,
)

router = APIRouter(prefix="/gmail", tags=["gmail"])


def get_gmail_service(db: Session = Depends(get_db)) -> GmailService:
    return GmailService(db)


@router.get("/connect")
def connect_gmail(service: GmailService = Depends(get_gmail_service)) -> RedirectResponse:
    state = secrets.token_urlsafe(32)
    try:
        authorization_url = service.get_authorization_url(state=state)
    except GmailConfigurationError as error:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(error)) from error

    response = RedirectResponse(url=authorization_url, status_code=status.HTTP_302_FOUND)
    response.set_cookie(
        key="gmail_oauth_state",
        value=state,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=600,
    )
    return response


@router.get("/callback")
def gmail_callback(
    request: Request,
    code: str = Query(...),
    state: str = Query(...),
    service: GmailService = Depends(get_gmail_service),
) -> RedirectResponse:
    stored_state = request.cookies.get("gmail_oauth_state")
    if not stored_state or stored_state != state:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OAuth state mismatch. Please try connecting Gmail again.",
        )

    try:
        service.exchange_code(code=code, state=state)
    except GmailConfigurationError as error:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(error)) from error
    except GmailIntegrationError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error
    except HttpError as error:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(error)) from error

    redirect_url = f"{settings.frontend_base_url.rstrip('/')}/gmail-settings?connected=1"
    response = RedirectResponse(url=redirect_url, status_code=status.HTTP_302_FOUND)
    response.delete_cookie("gmail_oauth_state")
    return response


@router.post("/watch")
def watch_gmail(service: GmailService = Depends(get_gmail_service)) -> dict:
    try:
        return service.start_watch()
    except GmailConfigurationError as error:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(error)) from error
    except GmailIntegrationError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error
    except HttpError as error:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(error)) from error


@router.get("/status")
def gmail_status(service: GmailService = Depends(get_gmail_service)) -> dict:
    return service.get_status()
