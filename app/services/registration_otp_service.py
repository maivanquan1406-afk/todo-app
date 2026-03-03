from __future__ import annotations

from datetime import datetime, timedelta, timezone
import secrets
from threading import Lock

from app.core.config import settings, logger
from app.core.exceptions import ValidationError
from app.services.password_reset_service import send_email

OTP_LENGTH = 6
OTP_EXPIRATION_MINUTES = 5

_otp_store: dict[str, tuple[str, datetime]] = {}
_store_lock = Lock()


def _generate_otp() -> str:
    value = secrets.randbelow(10 ** OTP_LENGTH)
    return str(value).zfill(OTP_LENGTH)


def request_otp(email: str) -> None:
    code = _generate_otp()
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=OTP_EXPIRATION_MINUTES)
    with _store_lock:
        _otp_store[email] = (code, expires_at)
    html_body = (
        "Cảm ơn bạn đã đăng ký tài khoản tại {app}.\n\n"
        "Mã OTP xác thực email của bạn là {otp}.\n"
        "Mã sẽ hết hạn sau {minutes} phút. Nếu bạn không thực hiện đăng ký, vui lòng bỏ qua email này."
    ).format(app=settings.APP_NAME, otp=code, minutes=OTP_EXPIRATION_MINUTES)
    send_email(
        to_email=email,
        subject="Your OTP Code",
        html_content=html_body,
    )
    logger.info("Registration OTP sent to %s", email)


def validate_otp(email: str, otp: str) -> None:
    cleaned = (otp or "").strip()
    if not cleaned or len(cleaned) != OTP_LENGTH or not cleaned.isdigit():
        raise ValidationError("OTP phải gồm 6 chữ số", field="otp")
    now = datetime.now(timezone.utc)
    with _store_lock:
        record = _otp_store.get(email)
    if not record:
        raise ValidationError("OTP không hợp lệ hoặc đã hết hạn", field="otp")
    code, expires_at = record
    if expires_at < now:
        with _store_lock:
            _otp_store.pop(email, None)
        raise ValidationError("OTP đã hết hạn", field="otp")
    if cleaned != code:
        raise ValidationError("OTP không đúng", field="otp")
    with _store_lock:
        _otp_store.pop(email, None)
