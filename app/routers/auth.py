from fastapi import APIRouter, HTTPException, Depends, Header, Request, Form, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from typing import Optional
from app.services.user_service import service as user_service
from app.models import UserCreate, UserLogin, UserResponse, Token
from app.core.jwt import decode_token

templates = Jinja2Templates(directory="app/templates")

router = APIRouter()

@router.post("/register", response_model=UserResponse)
def register(payload: UserCreate):
    if not (5 <= len(payload.password) <= 100):
        raise HTTPException(status_code=422, detail="password length must be 5-100")
    if "@" not in payload.email:
        raise HTTPException(status_code=422, detail="invalid email format")
    user = user_service.register(payload)
    if not user:
        raise HTTPException(status_code=409, detail="email already exists")
    return user

@router.post("/login", response_model=Token)
def login(payload: UserLogin):
    token = user_service.login(payload)
    if not token:
        raise HTTPException(status_code=401, detail="invalid email or password")
    return {"access_token": token, "token_type": "bearer"}

@router.get("/me", response_model=UserResponse)
def me(authorization: Optional[str] = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="missing or invalid token")
    token = authorization[7:]  # Remove "Bearer " prefix
    email = decode_token(token)
    if not email:
        raise HTTPException(status_code=401, detail="invalid token")
    user = user_service.get_by_email(email)
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
    user = user_service.get_by_email(email)
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
    user = user_service.register(payload)
    if not user:
        return templates.TemplateResponse("register.html", {"request": request, "error": "Email đã tồn tại"})
    # Redirect to login page after successful register
    return RedirectResponse(url="/api/v1/auth/login-page", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/login-page", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "error": None})


@router.post("/login-page", response_class=HTMLResponse)
def login_page_post(request: Request, email: str = Form(...), password: str = Form(...)):
    payload = UserLogin(email=email, password=password)
    token = user_service.login(payload)
    if not token:
        return templates.TemplateResponse("login.html", {"request": request, "error": "Email hoặc mật khẩu không đúng"})
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

