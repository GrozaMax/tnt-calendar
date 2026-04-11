"""
Авторизация и аутентификация
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field

from web.config import WebConfig
from src.database import get_session
from src.database.repositories import UserRepository
router = APIRouter()
security = HTTPBearer()


class LoginRequest(BaseModel):
    """Вход: Telegram ID (цифры) или username Telegram (без @)."""

    login: str = Field(..., min_length=1, max_length=255)
    secret_code: str = Field(..., min_length=1)


class LoginResponse(BaseModel):
    """Ответ на авторизацию"""
    access_token: str
    user: dict


async def _resolve_user_by_login(user_repo: UserRepository, login: str):
    raw = (login or "").strip()
    if raw.startswith("@"):
        raw = raw[1:].strip()
    if not raw:
        return None
    if raw.isdigit():
        return await user_repo.get_by_telegram_id(int(raw))
    return await user_repo.get_by_username(raw)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Проверка токена и получение текущего пользователя
    
    В продакшене здесь должна быть полноценная проверка JWT.
    Пока делаем простую проверку по токену.
    """
    token = credentials.credentials
    
    if not WebConfig.validate_token(token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token"
        )
    
    # Извлекаем user_id из токена
    # Формат токена: {telegram_id}:{random_string}
    try:
        telegram_id = int(token.split(":")[0])
    except (ValueError, IndexError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token format"
        )
    
    # Проверяем пользователя в БД
    async with get_session() as session:
        user_repo = UserRepository(session)
        user = await user_repo.get_by_telegram_id(telegram_id)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        # Проверяем права (только тренеры и админы)
        if not user.has_trainer_permissions():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. Only trainers and admins allowed."
            )
        
        return user


@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """
    Авторизация пользователя
    
    Логин: числовой Telegram ID или username (как в Telegram, без @).
    Секрет задаётся в окружении WEB_LOGIN_SECRET.
    """
    async with get_session() as session:
        user_repo = UserRepository(session)
        user = await _resolve_user_by_login(user_repo, request.login)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Проверяем права
        if not user.has_trainer_permissions():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only trainers and admins can access web interface"
            )
        
        # Проверяем пароль: сначала индивидуальный, потом общий секрет
        password_ok = False
        if user.has_web_password:
            password_ok = user.check_web_password(request.secret_code)
        else:
            # Fallback: общий секрет из WEB_LOGIN_SECRET
            password_ok = (request.secret_code == WebConfig.get_web_login_secret())

        if not password_ok:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid password"
            )
        
        # Генерируем токен
        # Формат: telegram_id:random_string
        import secrets
        token = f"{user.telegram_id}:{secrets.token_urlsafe(32)}"
        
        return LoginResponse(
            access_token=token,
            user={
                "id": user.id,
                "telegram_id": user.telegram_id,
                "full_name": user.full_name,
                "role": user.ui_role_key(),
            }
        )


@router.get("/me")
async def get_me(user = Depends(get_current_user)):
    """Получить информацию о текущем пользователе"""
    return {
        "id": user.id,
        "telegram_id": user.telegram_id,
        "full_name": user.full_name,
        "username": user.username,
        "role": user.ui_role_key(),
        "language": user.language
    }
