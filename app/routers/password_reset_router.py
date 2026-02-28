from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr, Field
from sqlmodel import Session

from app.core.config import logger
from app.core.exceptions import AppError, ValidationError, DatabaseError, EmailError
from app.db import get_session
from app.services.password_reset_service import (
    PasswordResetService,
    GENERIC_MESSAGE,
)

router = APIRouter(prefix="/auth", tags=["auth"])


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str = Field(min_length=10, max_length=256)
    new_password: str = Field(min_length=8, max_length=128)


def _get_db_session():
    session = get_session()
    try:
        yield session
    finally:
        session.close()


def _map_error(exc: AppError) -> HTTPException:
    if isinstance(exc, ValidationError):
        return HTTPException(status_code=400, detail=str(exc))
    if isinstance(exc, (DatabaseError, EmailError)):
        return HTTPException(status_code=500, detail="internal server error")
    return HTTPException(status_code=500, detail="internal server error")


@router.post("/forgot-password")
def forgot_password(
    payload: ForgotPasswordRequest,
    session: Session = Depends(_get_db_session)
):
    service = PasswordResetService(session)
    try:
        service.request_reset(payload.email)
    except AppError as exc:
        raise _map_error(exc)
    except Exception:
        logger.exception("Unexpected error while handling forgot password request")
        raise HTTPException(status_code=500, detail="internal server error")
    return {"message": GENERIC_MESSAGE}


@router.post("/reset-password")
def reset_password(
    payload: ResetPasswordRequest,
    session: Session = Depends(_get_db_session)
):
    service = PasswordResetService(session)
    try:
        service.reset_password(payload.token, payload.new_password)
    except AppError as exc:
        raise _map_error(exc)
    except Exception:
        logger.exception("Unexpected error while handling reset password request")
        raise HTTPException(status_code=500, detail="internal server error")
    return {"message": "Password has been updated."}
