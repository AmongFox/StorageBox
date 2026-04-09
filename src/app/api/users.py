from uuid import UUID

from fastapi import APIRouter, Depends
from fastapi import HTTPException, status

from src.app.schemas import FileListResponse
from src.core import get_logger
from src.database import FileCRUD, UserCRUD, get_file_crud, get_user_crud

router = APIRouter(prefix="/users", tags=["Users"])
logger = get_logger()


@router.get(
    "/{user_id}/files",
    response_model=FileListResponse,
    status_code=status.HTTP_200_OK,
)
async def get_files_by_user_id(
    user_id: UUID,
    user_crud: UserCRUD = Depends(get_user_crud),
    file_crud: FileCRUD = Depends(get_file_crud),
):
    """Получить информацию о всех файлах пользователя"""
    logger.info(f"Запрос на получение файлов пользователя (user_id={user_id})")
    user = await user_crud.get_by_id(user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден"
        )

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
            "owner_id": str(file.owner_id),
        }
        files_data.append(data)

    return {"files": files_data, "total": len(db_files)}


@router.delete("/{user_id}", status_code=status.HTTP_200_OK)
async def delete_user(user_id: UUID, user_crud: UserCRUD = Depends(get_user_crud)):
    """Удаление пользователя"""
    logger.debug(f"Запрос на удаление пользователя (user_id={user_id})")
    user = await user_crud.get_by_id(user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Пользователь {user_id} не найден",
        )

    result = await user_crud.delete(user_id)

    if not result:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при удалении пользователя",
        )

    logger.info(f"Пользователь {user_id} удалён")
    return {"message": "Пользователь успешно удалён"}
