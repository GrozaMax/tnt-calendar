"""
API для управления картинкой расписания (только администратор).
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from fastapi.responses import FileResponse

from web.api.auth import get_current_user
from src.models import User, UserRole
from src.services.schedule_image_service import (
    save_image, get_image_path, delete_image, image_exists
)

router = APIRouter()


def _require_admin(user: User) -> None:
    if user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Only admins can manage the schedule image")


@router.get("/status")
async def get_status(user: User = Depends(get_current_user)):
    """Проверить, загружена ли картинка."""
    path = get_image_path()
    return {
        "exists": path is not None,
        "filename": path.name if path else None,
    }


@router.get("/file")
async def get_image(user: User = Depends(get_current_user)):
    """Получить текущую картинку."""
    path = get_image_path()
    if not path:
        raise HTTPException(status_code=404, detail="Schedule image not found")
    ext = path.suffix.lstrip(".")
    media_type = "image/jpeg" if ext in ("jpg", "jpeg") else f"image/{ext}"
    return FileResponse(str(path), media_type=media_type)


@router.post("/", status_code=status.HTTP_201_CREATED)
async def upload_image(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user)
):
    """Загрузить новую картинку расписания (старая удаляется)."""
    _require_admin(user)
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="File is empty")
    ext = ""
    if file.filename and "." in file.filename:
        ext = file.filename.rsplit(".", 1)[-1]
    path = save_image(content, ext or "jpg")
    return {"status": "ok", "filename": path.name}


@router.delete("/", status_code=status.HTTP_204_NO_CONTENT)
async def remove_image(user: User = Depends(get_current_user)):
    """Удалить текущую картинку расписания."""
    _require_admin(user)
    if not image_exists():
        raise HTTPException(status_code=404, detail="No image to delete")
    delete_image()
