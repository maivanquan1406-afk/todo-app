from fastapi import APIRouter, HTTPException, Depends, Header, Request, Form, status, Body
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from typing import Optional
from urllib.parse import quote

from pydantic import BaseModel, EmailStr, TypeAdapter, ValidationError as PydanticValidationError

from app.services.user_service import service as user_service
from app.services import registration_otp_service
from app.models import UserCreate, UserLogin, UserResponse, Token
from app.core.jwt import decode_token
from app.core.exceptions import (
    AppError,
    ValidationError,
    ConflictError,
    NotFoundError,
    DatabaseError,
    AuthenticationError,
    EmailError,
)
from app.core.config import logger

templates = Jinja2Templates(directory="app/templates")

router = APIRouter()
_email_adapter = TypeAdapter(EmailStr)


def _map_app_error(exc: AppError) -> HTTPException:
    if isinstance(exc, ValidationError):
        return HTTPException(status_code=400, detail=str(exc))
    if isinstance(exc, AuthenticationError):
        return HTTPException(status_code=401, detail=str(exc))
    if isinstance(exc, NotFoundError):
        return HTTPException(status_code=404, detail=str(exc))
    if isinstance(exc, ConflictError):
        return HTTPException(status_code=409, detail=str(exc))
    if isinstance(exc, DatabaseError):
        return HTTPException(status_code=500, detail="internal server error")
    return HTTPException(status_code=500, detail="internal server error")

@router.post("/register", response_model=UserResponse)
def register(payload: UserCreate):
    try:
        if not (5 <= len(payload.password) <= 100):
            raise ValidationError("password length must be 5-100", field="password")
        if "@" not in payload.email:
            raise ValidationError("invalid email format", field="email")
        user = user_service.register(payload)
        return user
    except AppError as exc:
        raise _map_app_error(exc)

@router.post("/login", response_model=Token)
def login(payload: UserLogin):
    try:
        token = user_service.login(payload)
        return {"access_token": token, "token_type": "bearer"}
    except AppError as exc:
        raise _map_app_error(exc)

@router.get("/me", response_model=UserResponse)
def me(authorization: Optional[str] = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="missing or invalid token")
    token = authorization[7:]  # Remove "Bearer " prefix
    email = decode_token(token)
    if not email:
        raise HTTPException(status_code=401, detail="invalid token")
    try:
        user = user_service.get_by_email(email)
    except AppError as exc:
        raise _map_app_error(exc)
    if not user:
        raise HTTPException(status_code=404, detail="user not found")
    return user

def get_current_user(authorization: Optional[str] = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="missing or invalid token")
    token = authorization[7:]
    email = decode_token(token)
    if not email:
        raise HTTPException(status_code=401, detail="invalid token")
    try:
        user = user_service.get_by_email(email)
    except AppError as exc:
        raise _map_app_error(exc)
    if not user:
        raise HTTPException(status_code=404, detail="user not found")
    return user


# HTML pages for simple login/register UI (form-based)
class RegistrationOtpRequest(BaseModel):
    email: EmailStr


@router.post("/register/send-otp")
def register_send_otp(
    payload: RegistrationOtpRequest | None = Body(default=None),
    email: str | None = Form(default=None),
):
    try:
        raw_email = email or (payload.email if payload else None)
        if not raw_email:
            raise ValidationError("Email là bắt buộc", field="email")
        try:
            normalized_email = str(_email_adapter.validate_python(raw_email.strip().lower()))
        except PydanticValidationError:
            raise ValidationError("Định dạng email không hợp lệ", field="email")
        registration_otp_service.request_otp(normalized_email)
    except ValidationError as exc:
        raise HTTPException(status_code=400, detail={"message": str(exc)})
    except EmailError:
        logger.warning("Không thể gửi OTP đăng ký", exc_info=True)
        raise HTTPException(status_code=500, detail={"message": "Không thể gửi email OTP"})
    except Exception:
        logger.exception("Lỗi không mong đợi khi gửi OTP đăng ký")
        raise HTTPException(status_code=500, detail={"message": "unexpected error"})
    return {"message": "OTP đã được gửi nếu email hợp lệ."}


@router.get("/register-page", response_class=HTMLResponse)
def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request, "error": None, "prefill_email": ""})


@router.post("/register-page", response_class=HTMLResponse)
def register_page_post(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    otp: str = Form(...),
):
    normalized_email = email.strip().lower()
    if not (5 <= len(password) <= 100):
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "error": "Mật khẩu phải có độ dài 5-100 ký tự", "prefill_email": normalized_email},
        )
    try:
        validated_email = _email_adapter.validate_python(normalized_email)
    except PydanticValidationError:
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "error": "Định dạng email không hợp lệ", "prefill_email": normalized_email},
        )
    try:
        registration_otp_service.validate_otp(str(validated_email), otp)
    except ValidationError as exc:
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "error": str(exc), "prefill_email": normalized_email},
        )
    payload = UserCreate(email=str(validated_email), password=password)
    try:
        user_service.register(payload)
    except ConflictError:
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "error": "Email đã tồn tại", "prefill_email": normalized_email},
        )
    except AppError:
        logger.error("Register page error", exc_info=True)
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "error": "Có lỗi hệ thống, vui lòng thử lại", "prefill_email": normalized_email},
        )
    # Redirect to login page after successful register with email prefilled
    redirect_url = f"/api/v1/auth/login-page?email={quote(str(validated_email))}"
    return RedirectResponse(url=redirect_url, status_code=status.HTTP_303_SEE_OTHER)


@router.get("/login-page", response_class=HTMLResponse)
def login_page(request: Request, email: Optional[str] = None):
    return templates.TemplateResponse(
        "login.html",
        {"request": request, "error": None, "prefill_email": (email or "").lower()},
    )


@router.post("/login-page", response_class=HTMLResponse)
def login_page_post(request: Request, email: str = Form(...), password: str = Form(...)):
    payload = UserLogin(email=email, password=password)
    try:
        token = user_service.login(payload)
    except (ValidationError, AuthenticationError):
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Email hoặc mật khẩu không đúng", "prefill_email": email.lower()},
        )
    except AppError as exc:
        logger.error("Login page error", exc_info=True)
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Có lỗi hệ thống, vui lòng thử lại", "prefill_email": email.lower()},
        )
    # Set token in a HttpOnly cookie and redirect to home
    response = RedirectResponse(url='/dashboard', status_code=status.HTTP_303_SEE_OTHER)
    # store raw token; in production consider secure flags and proper session management
    response.set_cookie(key='access_token', value=token, httponly=True, samesite='lax')
    return response


@router.get('/logout')
def logout():
    response = RedirectResponse(url='/api/v1/auth/login-page', status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie('access_token')
    return response


@router.get("/forgot-password-page", response_class=HTMLResponse)
def forgot_password_page(request: Request):
    return templates.TemplateResponse("forgot_password.html", {"request": request})


@router.get("/verify-otp-page", response_class=HTMLResponse)
def verify_otp_page(request: Request, email: Optional[str] = None):
    return templates.TemplateResponse(
        "verify_otp.html",
        {"request": request, "email": email or ""}
    )


@router.get("/reset-password-page", response_class=HTMLResponse)
def reset_password_page(request: Request, email: Optional[str] = None):
    context = {
        "request": request,
        "email": email or "",
        "email_missing": email is None or email.strip() == ""
    }
    return templates.TemplateResponse("reset_password.html", context)

