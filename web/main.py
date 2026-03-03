"""
Главный файл веб-приложения (FastAPI)
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from web.api import workouts, users, auth, schedule_template
from web.config import WebConfig
from src.database.connection import init_db

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Инициализация БД при старте
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Жизненный цикл приложения"""
    logger.info("Инициализация базы данных...")
    await init_db()
    logger.info("База данных инициализирована")
    yield
    logger.info("Завершение работы веб-приложения")

# Создание приложения
app = FastAPI(
    title="TNT Admin panel",
    description="Веб-интерфейс для управления тренировками и пользователями",
    version="1.0.0",
    lifespan=lifespan
)

# Подключение роутеров
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(workouts.router, prefix="/api/workouts", tags=["workouts"])
app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(schedule_template.router, prefix="/api/schedule-template", tags=["schedule-template"])

# Статические файлы
app.mount("/static", StaticFiles(directory="web/static"), name="static")


@app.get("/", response_class=HTMLResponse)
async def root():
    """Главная страница"""
    with open("web/templates/index.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())


@app.get("/health")
async def health_check():
    """Проверка работоспособности"""
    return {"status": "ok", "service": "crossfit-hub-web"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "web.main:app",
        host=WebConfig.HOST,
        port=WebConfig.PORT,
        reload=WebConfig.DEBUG
    )

