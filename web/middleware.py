"""
Middleware: безопасность и расширенное логирование.

SecurityMiddleware — молча блокирует сканеры (404/405 мусор исчезает из логов).
AccessLogMiddleware — заменяет стандартный uvicorn access log на подробный.
"""
import time
import logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, PlainTextResponse

logger = logging.getLogger("web.access")

# ---------------------------------------------------------------------------
# 1. Security: блокируем типичные сканер-паттерны
# ---------------------------------------------------------------------------

# Подозрительные подстроки в path
_BLOCKED_PATH_PARTS = (
    "/.env",
    "/.git",
    "/config.json",
    "/wp-",
    "/wordpress",
    "/wp-admin",
    "/wp-login",
    "/.aws",
    "/.docker",
    "/cgi-bin",
    "/phpMyAdmin",
    "/phpmyadmin",
    "/actuator",
    "/SDK/",
    "/.vscode",
    "/.well-known/security.txt",
    "/telescope",
    "/vendors/",
    "/vendor/",
    "/debug/",
    "/server-status",
    "/server-info",
    "/backup",
    "/admin.php",
    "/xmlrpc.php",
    "/.DS_Store",
    "/.htaccess",
    "/.htpasswd",
    "/web.config",
    "/elmah.axd",
    "/trace.axd",
)

# HTTP-методы, которые точно не нужны
_BLOCKED_METHODS = {"PROPFIND", "OPTIONS", "TRACE", "CONNECT", "MKCOL", "COPY", "MOVE", "LOCK", "UNLOCK"}


class SecurityMiddleware(BaseHTTPMiddleware):
    """
    Молча возвращает 403 для сканер-запросов.
    Логирует одной строкой на уровне DEBUG (чтобы можно было включить при
    необходимости, но по умолчанию не засоряло логи).
    """

    async def dispatch(self, request: Request, call_next):
        method = request.method.upper()
        path = request.url.path.lower()

        # Блокировка по методу
        if method in _BLOCKED_METHODS:
            logger.debug("BLOCKED method=%s path=%s ip=%s", method, path, _client_ip(request))
            return PlainTextResponse("Forbidden", status_code=403)

        # Блокировка по path
        for pattern in _BLOCKED_PATH_PARTS:
            if pattern in path:
                logger.debug("BLOCKED path=%s ip=%s", path, _client_ip(request))
                return PlainTextResponse("Forbidden", status_code=403)

        # Блокировка попыток open-redirect сканирования
        qs = str(request.url.query).lower()
        if "testdomain.com" in qs or "redirect" in path and "url=" in qs:
            logger.debug("BLOCKED redirect-scan path=%s ip=%s", path, _client_ip(request))
            return PlainTextResponse("Forbidden", status_code=403)

        return await call_next(request)


# ---------------------------------------------------------------------------
# 2. Access Log: подробный лог вместо стандартного uvicorn
# ---------------------------------------------------------------------------

class AccessLogMiddleware(BaseHTTPMiddleware):
    """
    Расширенный access-лог:
      ✅ 200  12ms  GET /api/users/  ip=1.2.3.4  ua=Mozilla/5.0…  auth=yes
      ❌ 401  3ms   POST /api/auth/login  ip=1.2.3.4  ua=python-requests…
    """

    async def dispatch(self, request: Request, call_next):
        start = time.monotonic()
        response: Response = await call_next(request)
        elapsed_ms = round((time.monotonic() - start) * 1000)

        status = response.status_code
        method = request.method
        path = request.url.path
        query = str(request.url.query)
        if query:
            path = f"{path}?{query}"

        ip = _client_ip(request)
        ua = (request.headers.get("user-agent") or "-")[:120]

        # Определяем наличие токена авторизации
        auth_header = request.headers.get("authorization", "")
        auth = "yes" if auth_header.startswith("Bearer ") else "no"

        # Иконка статуса
        if status < 300:
            icon = "✅"
            log_fn = logger.info
        elif status < 400:
            icon = "↗️"
            log_fn = logger.info
        elif status == 401 or status == 403:
            icon = "🔒"
            log_fn = logger.warning
        elif status == 404:
            icon = "❓"
            log_fn = logger.info
        else:
            icon = "❌"
            log_fn = logger.error

        log_fn(
            "%s %d  %4dms  %-6s %s  ip=%s  auth=%s  ua=%s",
            icon, status, elapsed_ms, method, path, ip, auth, ua,
        )

        return response


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _client_ip(request: Request) -> str:
    """Получить реальный IP клиента (с учётом проксирования)."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    real_ip = request.headers.get("x-real-ip")
    if real_ip:
        return real_ip.strip()
    if request.client:
        return request.client.host
    return "unknown"
