from fastapi import APIRouter, Request, HTTPException, Depends, Response, Cookie
from fastapi.responses import JSONResponse, RedirectResponse
from authlib.integrations.starlette_client import OAuth
from app.core.config import settings
from app.core.db import get_session
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
from app.models import User
from app.auth.jwt import create_access_token, create_refresh_token, verify_token, REFRESH_TOKEN_EXPIRE_DAYS
from app.schemas import Token
from typing import Optional
import secrets

# Инициализация OAuth-клиента Google
oauth = OAuth()
oauth.register(
    name="google",
    client_id=settings.GOOGLE_CLIENT_ID,
    client_secret=settings.GOOGLE_CLIENT_SECRET,
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)

router = APIRouter()

# Маршрут для перенаправления пользователя на страницу авторизации Google
@router.get("/login")
async def login(request: Request):
    print(request.url_for("auth"));
    print(settings.GOOGLE_CLIENT_ID);
    print(settings.GOOGLE_CLIENT_SECRET);
    redirect_uri = "http://147.45.66.207.nip.io:8000/auth/auth"
    print(redirect_uri)
    return await oauth.google.authorize_redirect(request, redirect_uri)


# Маршрут колбэка Google
@router.get("/auth")
async def auth(request: Request, session: AsyncSession = Depends(get_session)):
    try:
        token_data = await oauth.google.authorize_access_token(request)
    except Exception as e:
        print(e)
        raise HTTPException(status_code=400, detail="Could not authorize Google token")

    user_info = token_data.get("userinfo")
    if not user_info:
        raise HTTPException(status_code=400, detail="Could not get user info from Google")

    email = user_info.get("email")
    name = user_info.get("name")
    if not email:
        raise HTTPException(status_code=400, detail="Email not provided by Google")

    stmt = select(User).where(User.email == email)
    result = await session.exec(stmt)
    user = result.one_or_none()
    if not user:
        user = User(email=email, name=name)
        session.add(user)
        await session.commit()
        await session.refresh(user)

    if not user or user.id is None:
        raise HTTPException(status_code=500, detail="Failed to create or retrieve user")

    refresh_token = create_refresh_token(user.id)

    response = RedirectResponse(url=settings.FRONTEND_BASE_URL)

    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        samesite="lax",
        secure=settings.ENVIRONMENT != "development",
        max_age=REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        path="/"
    )
    return response

# Маршрут для обновления токена
@router.post("/refresh", response_model=Token)
async def refresh_token_endpoint(
    refresh_token_cookie: Optional[str] = Cookie(None, alias="refresh_token")
):
    if not refresh_token_cookie:
        raise HTTPException(status_code=401, detail="Refresh token missing")

    payload = verify_token(refresh_token_cookie, expected_type="refresh")
    if not payload:
        response = JSONResponse(content={"detail": "Invalid or expired refresh token"}, status_code=401)
        response.delete_cookie("refresh_token", path="/")
        return response

    user_id = payload.get("user_id")
    if user_id is None:
        response = JSONResponse(content={"detail": "Invalid refresh token payload"}, status_code=401)
        response.delete_cookie("refresh_token", path="/")
        return response

    new_access_token = create_access_token(user_id)

    return JSONResponse(content={"access_token": new_access_token, "token_type": "bearer"})

# Маршрут для выхода из системы
@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie(
        key="refresh_token",
        httponly=True,
        samesite="lax",
        secure=settings.ENVIRONMENT != "development",
        path="/"
    )
    response.status_code = 200
    return {"message": "Logged out successfully"}
