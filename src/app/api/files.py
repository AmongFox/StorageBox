import hashlib
import os.path
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends
from fastapi import File as FastApiFile
from fastapi import Form, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.schemas import FileInfoResponse
from src.core import get_logger, get_settings
from src.database import FileCRUD, UserCRUD, get_file_crud, get_session, get_user_crud

router = APIRouter(prefix="/files", tags=["Files"])
logger = get_logger()


def _get_file_path(file_id: str, user_id: str) -> str:
    return os.path.join(get_settings().STORAGE_PATH, user_id, file_id)


def _get_file_category(extension: str) -> str:
    extension = extension.lower()

    for key, value in get_settings().ALLOWED_EXTENSIONS.items():
        if extension in value:
            return key

    return "documents"


def _calculate_file_hashes(content: bytes) -> tuple[str, str]:
    """Вычисление MD5 и SHA256"""
    md5_hash = hashlib.md5(content).hexdigest()
    sha256_hash = hashlib.sha256(content).hexdigest()
    return md5_hash, sha256_hash


def _from_mb_to_bytes(size: int):
    return size * 1024 * 1024


def _from_bytes_to_mb(size: int):
    return size / 1024 / 1024


@router.post(
    "/upload", response_model=FileInfoResponse, status_code=status.HTTP_201_CREATED
)
async def upload_file(
    file: UploadFile = FastApiFile(...),
    user_id: UUID = Form(...),
    expires_at: Optional[datetime] = Form(None),
    session: AsyncSession = Depends(get_session),
    file_crud: FileCRUD = Depends(get_file_crud),
    user_crud: UserCRUD = Depends(get_user_crud),
):
    """
    Роутер загрузки файла.
    Формат: storage/user_<username>/<category>/<filename>
    """
    logger.info(f"Запрос на загрузку файла: {user_id}")
    settings = get_settings()

    content = await file.read()

    filename = file.filename

    if not filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ошибка чтения пути файла",
        )

    file_extension = Path(filename).suffix.lower()

    if not any(
        file_extension in extensions
        for extensions in settings.ALLOWED_EXTENSIONS.values()
    ):
        logger.info("Недопустимое расширение")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Недопустимое расширение файла: {file_extension}",
        )

    file_size = len(content)
    logger.debug(f"Размер файла: {file_size}")

    if file_size > _from_mb_to_bytes(settings.MAX_FILE_SIZE_MB):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Размер файла ({round(_from_bytes_to_mb(file_size), 3)} MB)"
            f" превышает лимит ({settings.MAX_FILE_SIZE_MB} MB)",
        )

    if expires_at:
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if expires_at < datetime.now(timezone.utc):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Срок действия не может быть в прошлом",
            )

    user = await user_crud.get_by_id(user_id)

    if not user:
        logger.info(f"Пользователь {user_id} не найден")
        user = await user_crud.create(
            user_id=user_id, username=f"user_{str(user_id)[:12]}"
        )
        await session.commit()
        user_id = user.id
        logger.info(f"Создан новый пользователь (user={user})")

    if not await user_crud.increase_storage_used(user_id=user_id, size_bytes=file_size):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Превышен лимит хранилища. Использовано: {_from_bytes_to_mb(user.storage_used)} MB"
            f" из {_from_bytes_to_mb(user.storage_limit)} MB",
        )

    md5_hash, sha256_hash = _calculate_file_hashes(content)

    file_category = _get_file_category(file_extension)
    storage_path = Path(settings.STORAGE_PATH / f"user_{user.username}" / file_category)

    iterable = 0
    while True:
        name_without_ext = Path(filename).stem

        new_filename = f"{md5_hash[:8]}_{name_without_ext}"

        if iterable > 0:
            new_filename += f"_{iterable}"
        new_filename += file_extension

        file_path = Path(storage_path / new_filename)

        if not file_path.exists():
            break
        iterable += 1

    logger.info(f"Путь сохранения: {file_path}")

    storage_path.mkdir(parents=True, exist_ok=True)

    try:
        with open(file_path, "wb") as buffer:
            buffer.write(content)
    except Exception as e:
        logger.error(f"Ошибка во время сохранения файла: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка сохранения файла",
        )

    try:
        db_file = await file_crud.create(
            owner_id=user_id,
            filename=new_filename,
            file_path=str(file_path),
            file_size=file_size,
            file_category=file_category,
            file_extension=file_extension,
            expires_at=expires_at,
        )

        db_file.md5_hash = md5_hash
        db_file.sha256_hash = sha256_hash

        await session.flush()
    except Exception as e:
        logger.error(f"Ошибка записи файла в базу данных: {e}")
        if file_path.exists():
            file_path.unlink()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка регистрации файла",
        )

    logger.info(f"Файл {new_filename} загружен")

    return {
        "file_id": str(db_file.id),
        "filename": new_filename,
        "file_size": file_size,
        "file_category": file_category,
        "file_extension": file_extension,
        "created_at": db_file.created_at.isoformat() if db_file.created_at else None,
        "expires_at": db_file.expires_at.isoformat() if db_file.expires_at else None,
        "owner_id": str(db_file.owner_id),
    }


@router.get("/{file_id}/download")
async def download_file(file_id: UUID, file_crud: FileCRUD = Depends(get_file_crud)):
    logger.debug(f"Запрос на скачивание файла (file_id={file_id})")
    db_file = await file_crud.get_by_id(file_id)

    if not db_file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Файл не найден"
        )

    file_path = Path(db_file.file_path)

    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Файл не найден"
        )

    return FileResponse(path=file_path, filename=db_file.filename)


@router.get("/{file_id}")
async def get_file(file_id: UUID, file_crud: FileCRUD = Depends(get_file_crud)):
    """Получить информацию о файле"""
    logger.info(f"Запрос на получение информации о файле (file_id={file_id})")
    file = await file_crud.get_by_id(file_id)

    if not file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Файл не найден"
        )

    return {
        "file_id": str(file.id),
        "filename": file.filename,
        "file_size": file.file_size,
        "file_category": file.file_category,
        "file_extension": file.file_extension,
        "md5_hash": file.md5_hash,
        "sha256_hash": file.sha256_hash,
        "owner_id": str(file.owner_id) if file.owner_id else None,
        "created_at": file.created_at.isoformat() if file.created_at else None,
        "updated_at": file.updated_at.isoformat() if file.updated_at else None,
    }


@router.delete("/{file_id}")
async def delete_file(file_id: UUID, file_crud: FileCRUD = Depends(get_file_crud)):
    """Удаление файла"""
    logger.debug(f"Запрос на удаление файла (file_id={file_id})")
    file = await file_crud.get_by_id(file_id)

    if not file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Файл {file_id} не найден"
        )

    file_path = Path(file.file_path)
    if file_path.exists():
        try:
            file_path.unlink()
        except Exception as e:
            logger.error(f"Ошибка удаления файла с диска: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Ошибка при удалении файла",
            )

    result = await file_crud.delete(file_id)

    if not result:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при удалении файла",
        )

    logger.info(f"Файл {file_id} удалён")
    return {"message": "Файл успешно удалён"}
