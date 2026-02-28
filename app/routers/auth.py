from fastapi import APIRouter, HTTPException, Depends, Header, Request, Form, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from typing import Optional

from app.services.user_service import service as user_service
from app.models import UserCreate, UserLogin, UserResponse, Token
from app.core.jwt import decode_token
from app.core.exceptions import AppError, ValidationError, ConflictError, NotFoundError, DatabaseError, AuthenticationError
from app.core.config import logger

templates = Jinja2Templates(directory="app/templates")

router = APIRouter()


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
@router.get("/register-page", response_class=HTMLResponse)
def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request, "error": None})


@router.post("/register-page", response_class=HTMLResponse)
def register_page_post(request: Request, email: str = Form(...), password: str = Form(...)):
    if not (5 <= len(password) <= 100):
        return templates.TemplateResponse("register.html", {"request": request, "error": "Mật khẩu phải có độ dài 5-100 ký tự"})
    if "@" not in email:
        return templates.TemplateResponse("register.html", {"request": request, "error": "Định dạng email không hợp lệ"})
    payload = UserCreate(email=email, password=password)
    try:
        user_service.register(payload)
    except ConflictError:
        return templates.TemplateResponse("register.html", {"request": request, "error": "Email đã tồn tại"})
    except AppError as exc:
        logger.error("Register page error", exc_info=True)
        return templates.TemplateResponse("register.html", {"request": request, "error": "Có lỗi hệ thống, vui lòng thử lại"})
    # Redirect to login page after successful register
    return RedirectResponse(url="/api/v1/auth/login-page", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/login-page", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "error": None})


@router.post("/login-page", response_class=HTMLResponse)
def login_page_post(request: Request, email: str = Form(...), password: str = Form(...)):
    payload = UserLogin(email=email, password=password)
    try:
        token = user_service.login(payload)
    except (ValidationError, AuthenticationError):
        return templates.TemplateResponse("login.html", {"request": request, "error": "Email hoặc mật khẩu không đúng"})
    except AppError as exc:
        logger.error("Login page error", exc_info=True)
        return templates.TemplateResponse("login.html", {"request": request, "error": "Có lỗi hệ thống, vui lòng thử lại"})
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

