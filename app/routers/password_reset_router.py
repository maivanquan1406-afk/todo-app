from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Form, Body
from pydantic import (
    BaseModel,
    EmailStr,
    Field,
    TypeAdapter,
    ValidationError as PydanticValidationError,
)
from sqlmodel import Session

from app.core.config import logger
from app.core.exceptions import AppError, ValidationError, DatabaseError, EmailError
from app.db import get_session
from app.services.password_reset_service import (
    PasswordResetService,
    GENERIC_MESSAGE,
)

_email_adapter = TypeAdapter(EmailStr)

router = APIRouter(prefix="/auth", tags=["auth"])


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class VerifyOtpRequest(BaseModel):
    email: EmailStr
    otp: str = Field(min_length=6, max_length=6)


class ResetPasswordRequest(BaseModel):
    email: EmailStr
    new_password: str = Field(min_length=8, max_length=128)
    confirm_password: str | None = Field(default=None, min_length=8, max_length=128)


def _get_db_session():
    session = get_session()
    try:
        yield session
    finally:
        session.close()


def _map_error(exc: AppError) -> HTTPException:
    message = str(exc)
    code = exc.code or "app_error"
    status = 400
    if isinstance(exc, DatabaseError):
        message = "database error"
        code = exc.code
        status = 500
    elif isinstance(exc, EmailError):
        message = "email error"
        status = 500
    return HTTPException(status_code=status, detail={"message": message, "code": code})


@router.post("/forgot-password")
def forgot_password(
    payload: ForgotPasswordRequest | None = Body(default=None),
    email: str | None = Form(default=None),
    session: Session = Depends(_get_db_session)
):
    service = PasswordResetService(session)
    try:
        raw_email = email or (payload.email if payload else None)
        if not raw_email:
            raise ValidationError("email is required", field="email")
        try:
            normalized_email = str(_email_adapter.validate_python(raw_email)).lower()
        except PydanticValidationError:
            raise ValidationError("invalid email", field="email")

        service.request_reset(normalized_email)
    except ValidationError as exc:
        logger.warning("Forgot password validation error: %s", exc, exc_info=True)
        raise HTTPException(status_code=400, detail={"message": str(exc), "code": exc.code or "validation_error"})
    except EmailError:
        logger.warning("Email delivery issue during forgot password", exc_info=True)
    except DatabaseError as exc:
        logger.exception("Database error during forgot password", exc_info=True)
        raise _map_error(exc)
    except AppError as exc:
        logger.exception("Application error during forgot password", exc_info=True)
        raise _map_error(exc)
    except Exception:
        logger.exception("Unexpected error while handling forgot password request")
        raise HTTPException(status_code=500, detail={"message": "unexpected error", "code": "unexpected_error"})
    return {"message": GENERIC_MESSAGE}


@router.post("/verify-otp")
def verify_otp(
    payload: VerifyOtpRequest | None = Body(default=None),
    email: str | None = Form(default=None),
    otp: str | None = Form(default=None),
    session: Session = Depends(_get_db_session)
):
    service = PasswordResetService(session)
    try:
        raw_email = email or (payload.email if payload else None)
        if not raw_email:
            raise ValidationError("email is required", field="email")
        try:
            normalized_email = str(_email_adapter.validate_python(raw_email)).lower()
        except PydanticValidationError:
            raise ValidationError("invalid email", field="email")

        otp_value = otp or (payload.otp if payload else None)
        if not otp_value:
            raise ValidationError("otp is required", field="otp", code="invalid_otp")

        service.verify_otp(normalized_email, otp_value)
    except ValidationError as exc:
        logger.warning("OTP verification failed: %s", exc, exc_info=True)
        raise HTTPException(status_code=400, detail={"message": str(exc), "code": exc.code or "validation_error"})
    except DatabaseError as exc:
        logger.exception("Database error during OTP verify", exc_info=True)
        raise _map_error(exc)
    except AppError as exc:
        logger.exception("Application error during OTP verify", exc_info=True)
        raise _map_error(exc)
    except Exception:
        logger.exception("Unexpected error while verifying OTP")
        raise HTTPException(status_code=500, detail={"message": "unexpected error", "code": "unexpected_error"})
    return {"message": "OTP verified successfully."}


@router.post("/reset-password")
def reset_password(
    payload: ResetPasswordRequest | None = Body(default=None),
    email: str | None = Form(default=None),
    new_password: str | None = Form(default=None),
    confirm_password: str | None = Form(default=None),
    session: Session = Depends(_get_db_session)
):
    service = PasswordResetService(session)
    try:
        raw_email = email or (payload.email if payload else None)
        if not raw_email:
            raise ValidationError("email is required", field="email")
        try:
            normalized_email = str(_email_adapter.validate_python(raw_email)).lower()
        except PydanticValidationError:
            raise ValidationError("invalid email", field="email")

        password_value = new_password or (payload.new_password if payload else None)
        confirm_value = confirm_password or (payload.confirm_password if payload else None)
        if not password_value:
            raise ValidationError("new_password is required", field="new_password")
        if confirm_value is not None and confirm_value != password_value:
            raise ValidationError("passwords do not match", field="confirm_password")

        service.reset_password(normalized_email, password_value)
    except AppError as exc:
        raise _map_error(exc)
    except Exception:
        logger.exception("Unexpected error while handling reset password request")
        raise HTTPException(status_code=500, detail={"message": "unexpected error", "code": "unexpected_error"})
    return {"message": "Password has been updated."}
