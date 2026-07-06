from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.services.mail_officer import (
    MailOfficerAnalysisError,
    MailOfficerConfigurationError,
    MailOfficerService,
)

router = APIRouter(prefix="/emails", tags=["emails"])


def get_mail_officer_service(db: Session = Depends(get_db)) -> MailOfficerService:
    return MailOfficerService(db)


@router.post("/{email_id}/analyze")
def analyze_email(
    email_id: int,
    service: MailOfficerService = Depends(get_mail_officer_service),
) -> dict:
    try:
        analysis = service.analyze_email_by_id(email_id)
        return service.serialize_analysis(analysis)
    except MailOfficerConfigurationError as error:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(error)) from error
    except MailOfficerAnalysisError as error:
        detail = str(error)
        status_code = status.HTTP_404_NOT_FOUND if "was not found" in detail else status.HTTP_400_BAD_REQUEST
        raise HTTPException(status_code=status_code, detail=detail) from error


@router.get("/{email_id}/analysis")
def get_email_analysis(
    email_id: int,
    service: MailOfficerService = Depends(get_mail_officer_service),
) -> dict:
    try:
        analysis = service.get_analysis_by_email_id(email_id)
    except MailOfficerAnalysisError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error

    if analysis is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analysis not found for this email")

    return service.serialize_analysis(analysis)


@router.post("/analyze-pending")
def analyze_pending_emails(
    service: MailOfficerService = Depends(get_mail_officer_service),
) -> dict:
    try:
        return service.analyze_pending()
    except MailOfficerConfigurationError as error:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(error)) from error
    except MailOfficerAnalysisError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error
