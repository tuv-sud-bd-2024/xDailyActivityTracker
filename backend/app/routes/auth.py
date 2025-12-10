from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta
from sqlmodel import Session, select

from ..config import settings
from ..db import engine
from ..models import User
from ..auth import (
    verify_password,
    get_password_hash,
    create_access_token,
    get_current_active_user,
)

router = APIRouter()


@router.get("/login")
def login_page(request: Request):
    """Render simple login form."""
    from fastapi.templating import Jinja2Templates
    templates = Jinja2Templates(directory="backend/app/templates")
    return templates.TemplateResponse("login.html", {"request": request})


@router.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """API endpoint for login; returns JWT token."""
    with Session(engine) as session:
        user = session.exec(select(User).where(User.email == form_data.username)).first()
        if not user:
            raise HTTPException(status_code=400, detail="Incorrect email or password")
        if not verify_password(form_data.password, user.hashed_password):
            raise HTTPException(status_code=400, detail="Incorrect email or password")

        access_token_expires = timedelta(minutes=60)
        access_token = create_access_token(data={"sub": user.email}, expires_delta=access_token_expires)
        response = RedirectResponse(url="/", status_code=302)
        response.set_cookie(key="access_token", value=access_token, max_age=3600, httponly=True)
        return response


@router.post("/logout")
def logout():
    """Clear auth cookie."""
    response = RedirectResponse(url="/api/auth/login", status_code=302)
    response.delete_cookie(key="access_token")
    return response


@router.post("/register")
def register(email: str, password: str, current_user=Depends(get_current_active_user)):
    # only allow admin to create users
    if not current_user or 'admin' not in (current_user.roles or 'admin'):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin privileges required")
    with Session(engine) as session:
        existing = session.exec(select(User).where(User.email == email)).first()
        if existing:
            raise HTTPException(status_code=400, detail="User already exists")
        user = User(email=email, hashed_password=get_password_hash(password), is_active=True, roles='["viewer"]')
        session.add(user)
        session.commit()
        session.refresh(user)
        return {"email": user.email, "id": str(user.id)}
