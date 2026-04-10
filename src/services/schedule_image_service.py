"""
Сервис управления картинкой расписания.
Хранится только один файл; при загрузке нового старый удаляется.
"""
from __future__ import annotations

import os
from pathlib import Path

# В Docker оба контейнера должны указывать один путь (общий volume), например /app/data/uploads
_UPLOADS_DIR = Path(os.getenv("UPLOADS_DIR", "uploads")).expanduser()
_IMAGE_STEM = "schedule_image"
_ALLOWED_EXTS = {"jpg", "jpeg", "png", "webp", "gif"}


def _dir() -> Path:
    _UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    return _UPLOADS_DIR


def get_image_path() -> Path | None:
    """Вернуть путь к текущей картинке или None, если не загружена."""
    for ext in _ALLOWED_EXTS:
        p = _dir() / f"{_IMAGE_STEM}.{ext}"
        if p.exists():
            return p
    return None


def image_exists() -> bool:
    return get_image_path() is not None


def _delete_existing() -> None:
    for p in _dir().glob(f"{_IMAGE_STEM}.*"):
        p.unlink(missing_ok=True)


def save_image(file_bytes: bytes, extension: str = "jpg") -> Path:
    """Сохранить новую картинку (старая удаляется). Возвращает путь к файлу."""
    ext = extension.lower().lstrip(".")
    if ext not in _ALLOWED_EXTS:
        ext = "jpg"
    _delete_existing()
    path = _dir() / f"{_IMAGE_STEM}.{ext}"
    path.write_bytes(file_bytes)
    return path


def delete_image() -> None:
    """Удалить текущую картинку."""
    _delete_existing()
