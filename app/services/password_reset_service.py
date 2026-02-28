from __future__ import annotations

from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
import secrets
import smtplib

from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import Session, select

from app.core.config import settings, logger
from app.core.exceptions import DatabaseError, ValidationError, EmailError
from app.core.jwt import hash_password
from app.models import User
from app.models.password_reset import PasswordResetToken

RESET_TOKEN_EXPIRATION_MINUTES = 30
GENERIC_MESSAGE = "If the email exists, a reset link has been sent."


class PasswordResetService:
    def __init__(self, session: Session):
        self.session = session

    def request_reset(self, email: str) -> None:
        user = self._get_user_by_email(email)
        if not user:
            return
        token = self._create_token(user.id)
        reset_link = self._build_reset_link(token.token)
        body = (
            "We received a request to reset your password.\n\n"
            f"Use the link below to set a new password (expires in {RESET_TOKEN_EXPIRATION_MINUTES} minutes):\n"
            f"{reset_link}\n\n"
            "If you did not request this change, you can ignore this email."
        )
        send_email(
            to_email=user.email,
            subject=f"{settings.APP_NAME} password reset",
            body=body,
        )

    def reset_password(self, token: str, new_password: str) -> None:
        if not (8 <= len(new_password) <= 128):
            raise ValidationError("password length must be 8-128 characters", field="new_password")
        reset_record = self._get_token(token)
        now = datetime.now(timezone.utc)
        if reset_record.used:
            raise ValidationError("token already used")
        if reset_record.expires_at < now:
            raise ValidationError("token expired")
        user = self.session.get(User, reset_record.user_id)
        if not user:
            raise ValidationError("invalid token")
        user.hashed_password = hash_password(new_password)
        reset_record.used = True
        try:
            self.session.add(user)
            self.session.add(reset_record)
            self.session.commit()
        except SQLAlchemyError as exc:
            self.session.rollback()
            logger.error("DB error while updating password", exc_info=True)
            raise DatabaseError("Failed to reset password", original=exc) from exc

    def _get_user_by_email(self, email: str) -> User | None:
        try:
            stmt = select(User).where(User.email == email)
            return self.session.exec(stmt).first()
        except SQLAlchemyError as exc:
            logger.error("DB error while querying user", exc_info=True)
            raise DatabaseError("Failed to lookup user", original=exc) from exc

    def _create_token(self, user_id: int) -> PasswordResetToken:
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=RESET_TOKEN_EXPIRATION_MINUTES)
        stored_token = None
        try:
            while stored_token is None:
                token_value = secrets.token_urlsafe(32)
                stored_token = PasswordResetToken(user_id=user_id, token=token_value, expires_at=expires_at)
                self.session.add(stored_token)
                try:
                    self.session.commit()
                except SQLAlchemyError as exc:
                    self.session.rollback()
                    if "UNIQUE" in str(exc).upper():
                        stored_token = None
                        continue
                    logger.error("DB error while creating password reset token", exc_info=True)
                    raise DatabaseError("Failed to create password reset token", original=exc) from exc
            self.session.refresh(stored_token)
            return stored_token
        except DatabaseError:
            raise

    def _get_token(self, token: str) -> PasswordResetToken:
        try:
            stmt = select(PasswordResetToken).where(PasswordResetToken.token == token)
            record = self.session.exec(stmt).first()
        except SQLAlchemyError as exc:
            logger.error("DB error while fetching password reset token", exc_info=True)
            raise DatabaseError("Failed to lookup password reset token", original=exc) from exc
        if not record:
            raise ValidationError("invalid token")
        return record

    def _build_reset_link(self, token: str) -> str:
        base = settings.APP_DOMAIN.rstrip('/')
        return f"{base}/reset-password?token={token}"


def send_email(*, to_email: str, subject: str, body: str) -> None:
    if not settings.SMTP_HOST:
        logger.error("SMTP_HOST not configured; cannot send email")
        raise EmailError("SMTP configuration missing")
    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = settings.SMTP_USER or f"no-reply@{settings.APP_NAME.lower().replace(' ', '')}.local"
    message["To"] = to_email
    message.set_content(body)
    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=15) as server:
            server.starttls()
            if settings.SMTP_USER and settings.SMTP_PASSWORD:
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.send_message(message)
    except Exception as exc:
        logger.error("Failed to send password reset email", exc_info=True)
        raise EmailError("Unable to send email") from exc
