"""
Авторизация и аутентификация
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

from web.config import WebConfig
from src.database import get_session
from src.database.repositories import UserRepository
from src.models import UserRole

router = APIRouter()
security = HTTPBearer()


class LoginRequest(BaseModel):
    """Запрос на авторизацию"""
    telegram_id: int
    secret_code: str


class LoginResponse(BaseModel):
    """Ответ на авторизацию"""
    access_token: str
    user: dict


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
        if user.role == UserRole.ATHLETE:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. Only trainers and admins allowed."
            )
        
        return user


@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """
    Авторизация пользователя
    
    Для входа нужен telegram_id и секретный код.
    Возвращает access_token для использования в API.
    """
    async with get_session() as session:
        user_repo = UserRepository(session)
        user = await user_repo.get_by_telegram_id(request.telegram_id)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Проверяем права
        if user.role == UserRole.ATHLETE:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only trainers and admins can access web interface"
            )
        
        # Проверяем секретный код (пока просто "secret123")
        # В продакшене здесь должна быть проверка пароля
        if request.secret_code != "secret123":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid secret code"
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
                "role": user.role.value
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
        "role": user.role.value,
        "language": user.language
    }

