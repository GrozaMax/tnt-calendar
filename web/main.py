"""
Главный файл веб-приложения (FastAPI)
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, PlainTextResponse, Response

from web.api import workouts, users, auth, schedule_template, schedule_image, business_settings
from web.config import WebConfig
from web.middleware import SecurityMiddleware, AccessLogMiddleware
from src.database.connection import init_db

# ---------------------------------------------------------------------------
# Логирование
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s  %(name)-18s  %(levelname)-7s  %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)
logger = logging.getLogger(__name__)

# Глушим стандартный access-лог uvicorn — мы заменяем его своим middleware
logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
# Но оставляем uvicorn.error, чтобы видеть старты/рестарты
logging.getLogger("uvicorn.error").setLevel(logging.INFO)


# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Жизненный цикл приложения"""
    logger.info("Инициализация базы данных...")
    await init_db()
    logger.info("База данных инициализирована")
    yield
    logger.info("Завершение работы веб-приложения")


# ---------------------------------------------------------------------------
# Создание приложения
# ---------------------------------------------------------------------------
# В production скрываем Swagger/ReDoc, чтобы не палить API-схему наружу
_show_docs = WebConfig.DEBUG

app = FastAPI(
    title="TNT Admin panel",
    description="Веб-интерфейс для управления тренировками и пользователями",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if _show_docs else None,
    redoc_url="/redoc" if _show_docs else None,
    openapi_url="/openapi.json" if _show_docs else None,
)

# ---------------------------------------------------------------------------
# Middleware (порядок важен: первый добавленный — последний вызванный)
# → сначала AccessLog оборачивает ответ, потом Security фильтрует запрос
# ---------------------------------------------------------------------------
app.add_middleware(AccessLogMiddleware)
app.add_middleware(SecurityMiddleware)

# ---------------------------------------------------------------------------
# Роутеры API
# ---------------------------------------------------------------------------
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(workouts.router, prefix="/api/workouts", tags=["workouts"])
app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(schedule_template.router, prefix="/api/schedule-template", tags=["schedule-template"])
app.include_router(schedule_image.router, prefix="/api/schedule-image", tags=["schedule-image"])
app.include_router(business_settings.router, prefix="/api/settings", tags=["settings"])

# ---------------------------------------------------------------------------
# Статические файлы
# ---------------------------------------------------------------------------
app.mount("/static", StaticFiles(directory="web/static"), name="static")


# ---------------------------------------------------------------------------
# Служебные маршруты
# ---------------------------------------------------------------------------
@app.get("/", response_class=HTMLResponse)
async def root():
    """Главная страница"""
    with open("web/templates/index.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())


@app.get("/health")
async def health_check():
    """Проверка работоспособности"""
    return {"status": "ok", "service": "tnt-admin-panel"}


@app.get("/robots.txt", response_class=PlainTextResponse)
async def robots_txt():
    """robots.txt — запрещаем индексацию (это внутренняя админ-панель)."""
    return "User-agent: *\nDisallow: /\n"


@app.get("/favicon.ico")
async def favicon():
    """Отдаём пустой favicon, чтобы браузеры не генерировали 404."""
    # 1x1 transparent ICO (минимальный валидный файл — 70 байт)
    # Если захотите свою иконку — замените файлом web/static/favicon.ico
    # и поменяйте этот route на StaticFiles.
    ICO = (
        b'\x00\x00\x01\x00\x01\x00\x01\x01\x00\x00\x01\x00 \x00'
        b'0\x00\x00\x00\x16\x00\x00\x00(\x00\x00\x00\x01\x00\x00'
        b'\x00\x02\x00\x00\x00\x01\x00 \x00\x00\x00\x00\x00\x04'
        b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
        b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
        b'\x00\x00\x00'
    )
    return Response(content=ICO, media_type="image/x-icon")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "web.main:app",
        host=WebConfig.HOST,
        port=WebConfig.PORT,
        reload=WebConfig.DEBUG
    )
