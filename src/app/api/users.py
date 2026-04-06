import hashlib
import os.path
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File as FastApiFile, Form
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_session, UserCRUD, get_user_crud, get_file_crud, FileCRUD
from src.app.schemas import FileInfoResponse
from src.core import get_logger, get_settings

router = APIRouter(prefix="/users", tags=["Users"])
logger = get_logger()


@router.get("/{user_id}/files")
async def get_files_by_user_id(
        user_id: UUID,
        user_crud: UserCRUD = Depends(get_user_crud),
        file_crud: FileCRUD = Depends(get_file_crud)
):
    """Получить информацию о всех файлах пользователя"""
    logger.info(f"Запрос на получение файлов пользователя (user_id={user_id})")
    user = await user_crud.get_by_id(user_id)
    logger.debug(user)

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")

    db_files = await file_crud.get_files_by_user_id(user_id)
    files_data = []
    for file in db_files:
        data = {
            "file_id": str(file.id),
            "filename": file.filename,
            "file_size": file.file_size,
            "file_category": file.file_category,
            "file_extension": file.file_extension,
            "created_at": file.created_at.isoformat() if file.created_at else None,
            "expires_at": file.expires_at.isoformat() if file.expires_at else None,
            "owner_id": str(file.owner_id)
        }
        files_data.append(data)

    return {
        "files": files_data,
        "count": len(db_files),
        "owner_id": user_id
    }
