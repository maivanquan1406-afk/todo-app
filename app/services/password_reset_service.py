from __future__ import annotations

from datetime import datetime, timedelta, timezone
from contextlib import contextmanager
from email.message import EmailMessage
import secrets
import smtplib
import ssl

from threading import Lock

from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import Session, select

from app.core.config import settings, logger
from app.core.exceptions import DatabaseError, ValidationError, EmailError
from app.core.jwt import hash_password
from app.models import User


_registry_lock = Lock()
_email_locks: dict[str, Lock] = {}


@contextmanager
def _email_lock(email: str):
    with _registry_lock:
        lock = _email_locks.get(email)
        if lock is None:
            lock = Lock()
            _email_locks[email] = lock
    lock.acquire()
    try:
        yield
    finally:
        lock.release()


def _ensure_timezone(value: datetime | str | None) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, str):
        try:
            value = datetime.fromisoformat(value)
        except ValueError:
            return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value

OTP_EXPIRATION_MINUTES = 5
OTP_LENGTH = 6
GENERIC_MESSAGE = "If the email exists, an OTP has been sent."


class PasswordResetService:
    def __init__(self, session: Session):
        self.session = session

    def request_reset(self, email: str) -> None:
        with _email_lock(email):
            user = self._get_user_by_email(email)
            if not user:
                return
            now = datetime.now(timezone.utc)
            expire_at = _ensure_timezone(user.otp_expire)
            reuse_existing = (
                user.otp_code
                and expire_at
                and expire_at > now
                and not user.otp_used
            )
            if reuse_existing:
                otp_value = user.otp_code
            else:
                otp_value = self._generate_otp()
                user.otp_code = otp_value
                user.otp_used = False
            user.otp_expire = now + timedelta(minutes=OTP_EXPIRATION_MINUTES)
            self._commit_user(user, action="create OTP")
        body = (
            "We received a request to reset your password.\n\n"
            f"Your OTP code is {otp_value}.\n"
            f"It expires in {OTP_EXPIRATION_MINUTES} minutes.\n\n"
            "If you did not request this change, you can ignore this email."
        )
        try:
            send_email(
                to_email=email,
                subject=f"{settings.APP_NAME} password reset OTP",
                body=body,
            )
        except EmailError:
            logger.warning("OTP email could not be sent", exc_info=True)

    def verify_otp(self, email: str, otp: str) -> None:
        cleaned_otp = otp.strip()
        if len(cleaned_otp) != OTP_LENGTH or not cleaned_otp.isdigit():
            raise ValidationError("OTP must be 6 digits", field="otp", code="invalid_otp")
        user = self._get_user_by_email(email)
        if not user or not user.otp_code:
            raise ValidationError("OTP không hợp lệ hoặc đã hết hạn", field="otp", code="invalid_otp")
        now = datetime.now(timezone.utc)
        if user.otp_code != cleaned_otp:
            raise ValidationError("OTP không hợp lệ hoặc đã hết hạn", field="otp", code="invalid_otp")
        expire_at = _ensure_timezone(user.otp_expire)
        user.otp_expire = expire_at
        if not expire_at or expire_at < now:
            raise ValidationError("OTP đã hết hạn", field="otp", code="invalid_otp")
        if user.otp_used:
            raise ValidationError("OTP đã được sử dụng", field="otp", code="invalid_otp")
        user.otp_used = True
        self._commit_user(user, action="verify OTP")

    def reset_password(self, email: str, new_password: str) -> None:
        if not (8 <= len(new_password) <= 128):
            raise ValidationError("password length must be 8-128 characters", field="new_password")
        user = self._get_user_by_email(email)
        if not user:
            raise ValidationError("Email không tồn tại", field="email")
        now = datetime.now(timezone.utc)
        expire_at = _ensure_timezone(user.otp_expire)
        user.otp_expire = expire_at
        if not user.otp_used or not user.otp_code:
            raise ValidationError("OTP chưa được xác thực", field="otp", code="otp_not_verified")
        if not expire_at or expire_at < now:
            raise ValidationError("OTP đã hết hạn", field="otp", code="invalid_otp")
        user.hashed_password = hash_password(new_password)
        user.otp_code = None
        user.otp_expire = None
        user.otp_used = False
        self._commit_user(user, action="reset password")

    def _generate_otp(self) -> str:
        value = secrets.randbelow(10 ** OTP_LENGTH)
        return str(value).zfill(OTP_LENGTH)

    def _get_user_by_email(self, email: str) -> User | None:
        try:
            stmt = select(User).where(User.email == email)
            return self.session.exec(stmt).first()
        except SQLAlchemyError as exc:
            logger.error("DB error while querying user", exc_info=True)
            raise DatabaseError("Failed to lookup user", original=exc) from exc

    def _commit_user(self, user: User, *, action: str) -> None:
        try:
            self.session.add(user)
            self.session.commit()
            self.session.refresh(user)
        except SQLAlchemyError as exc:
            self.session.rollback()
            logger.error("DB error while processing %s", action, exc_info=True)
            raise DatabaseError("Failed to persist user changes", original=exc) from exc


def _require_smtp_config() -> dict:
    missing: list[str] = []
    host = settings.SMTP_HOST
    port = settings.SMTP_PORT
    username = settings.SMTP_USERNAME
    password = settings.SMTP_PASSWORD
    sender = settings.SMTP_FROM or username
    if not host:
        missing.append("SMTP_HOST")
    if not username:
        missing.append("SMTP_USERNAME")
    if not password:
        missing.append("SMTP_PASSWORD")
    if not sender:
        missing.append("SMTP_FROM")
    if missing:
        raise RuntimeError(f"Missing SMTP configuration values: {', '.join(missing)}")
    return {
        "host": host,
        "port": port,
        "username": username,
        "password": password,
        "sender": sender,
        "use_ssl": settings.SMTP_USE_SSL,
        "use_tls": settings.SMTP_USE_TLS,
    }


def send_email(*, to_email: str, subject: str, body: str) -> None:
    config = _require_smtp_config()
    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = config["sender"]
    message["To"] = to_email
    message.set_content(body)

    use_ssl = config["use_ssl"] or config["port"] == 465
    use_tls = config["use_tls"] and not use_ssl
    smtp_cls = smtplib.SMTP_SSL if use_ssl else smtplib.SMTP
    ssl_context = ssl.create_default_context()

    try:
        with smtp_cls(config["host"], config["port"], timeout=15) as server:
            server.ehlo()
            if use_tls:
                server.starttls(context=ssl_context)
                server.ehlo()
            server.login(config["username"], config["password"])
            server.send_message(message)
        logger.info("Password reset email sent to %s via %s:%s", to_email, config["host"], config["port"])
    except Exception as exc:
        logger.error(
            "SMTP send failed (host=%s port=%s): %s",
            config["host"],
            config["port"],
            exc,
            exc_info=True,
        )
        raise EmailError("Unable to send email") from exc
