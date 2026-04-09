from datetime import datetime, timezone
from typing import Optional, Sequence
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.core import get_logger
from src.database.models import File, User

logger = get_logger()


class UserCRUD:
    """CRUD операции над User"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            await self.session.rollback()
        else:
            await self.session.commit()
        return False

    async def create(self, user_id: UUID, username: str) -> User:
        logger.debug(f"Запись пользователя (user_id={user_id}; username={username})")
        user = User(id=user_id, username=username)

        self.session.add(user)
        await self.session.flush()
        await self.session.refresh(user)

        logger.debug(f"Успешно (User={user})")
        return user

    async def get_by_id(self, user_id: UUID) -> Optional[User]:
        logger.debug(f"Получение пользователя (user_id={user_id})")
        result = await self.session.execute(select(User).where(User.id == user_id))
        logger.debug(f"Успешно (User={result})")
        return result.scalar_one_or_none()

    async def get_by_username(self, username: str) -> Optional[User]:
        logger.debug(f"Получение пользователя (username={username})")
        result = await self.session.execute(
            select(User).where(User.username == username)
        )
        logger.debug(f"Успешно (User={result})")
        return result.scalar_one_or_none()

    async def update(
        self,
        user_id: UUID,
        username: Optional[str] = None,
        is_active: Optional[bool] = None,
    ):
        logger.debug(f"Обновление пользователя (user_id={user_id})")
        update_data = {}

        if username is not None:
            update_data["username"] = username
        if is_active is not None:
            update_data["is_active"] = is_active

        if not update_data:
            return None

        result = await self.session.execute(
            update(User).where(User.id == user_id).values(**update_data).returning(User)
        )
        await self.session.flush()

        logger.debug(f"Успешно (User={result})")
        return result.scalar_one_or_none()

    async def increase_storage_used(self, user_id: UUID, size_bytes: int) -> bool:
        user = await self.get_by_id(user_id)
        if user.storage_used + size_bytes > user.storage_limit:
            return False
        user.storage_used += size_bytes
        await self.session.flush()
        return True

    async def decrement_storage_used(self, user_id: UUID, size_bytes: int) -> bool:
        user = await self.get_by_id(user_id)
        if user.storage_used - size_bytes < 0:
            return False
        user.storage_used -= size_bytes
        await self.session.flush()
        return True

    async def delete(self, user_id: UUID) -> bool:
        logger.debug(f"Удаление пользователя (user_id={user_id})")
        user = await self.get_by_id(user_id)

        if not user:
            return False

        await self.session.delete(user)
        await self.session.flush()

        logger.debug("Успешно")
        return True


class FileCRUD:
    """CRUD операции над File"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            await self.session.rollback()
        else:
            await self.session.commit()
        return False

    async def create(
        self,
        owner_id: UUID,
        filename: str,
        file_path: str,
        file_size: int,
        file_category: str,
        file_extension: str,
        expires_at: Optional[datetime] = None,
    ):
        logger.debug(f"Запись файла (filename={filename})")
        file = File(
            owner_id=owner_id,
            filename=filename,
            file_path=file_path,
            file_size=file_size,
            file_category=file_category,
            file_extension=file_extension,
            expires_at=expires_at,
        )

        self.session.add(file)
        await self.session.flush()
        await self.session.refresh(file)

        logger.debug(f"Успешно (File={file})")
        return file

    async def get_by_id(self, file_id: UUID) -> Optional[File]:
        logger.debug(f"Получение файла (file_id={file_id})")
        result = await self.session.execute(select(File).where(File.id == file_id))
        logger.debug(f"Успешно (File={result})")
        return result.scalar_one_or_none()

    async def get_files_by_user_id(self, user_id: UUID) -> Sequence[File]:
        logger.debug(f"Получение списка файлов пользователя (user_id={user_id})")
        result = await self.session.execute(
            select(File).where(File.owner_id == user_id)
        )
        logger.debug(f"Успешно (File={result})")
        return result.scalars().all()

    async def get_expired(self):
        logger.debug("Получение просроченных файлов")
        now = datetime.now(timezone.utc)
        result = await self.session.execute(
            select(File).where(File.expires_at.isnot(None), File.expires_at < now)
        )
        files = list(result.scalars().all())
        logger.debug(f"Успешно. Найдено: {len(files)}")
        return files

    async def update(
        self,
        file_id: UUID,
        filename: Optional[str] = None,
        file_path: Optional[str] = None,
        file_size: Optional[str] = None,
        file_category: Optional[str] = None,
        file_extension: Optional[str] = None,
    ):
        logger.debug(f"Обновление файла (file_id={file_id})")
        update_data = {}

        if filename is not None:
            update_data["filename"] = filename
        if file_path is not None:
            update_data["file_path"] = file_path
        if file_size is not None:
            update_data["file_size"] = file_size
        if file_category is not None:
            update_data["file_category"] = file_category
        if file_extension is not None:
            update_data["file_extension"] = file_extension

        if not update_data:
            return None

        result = await self.session.execute(
            update(File).where(File.id == file_id).values(**update_data).returning(File)
        )
        await self.session.flush()

        logger.debug(f"Успешно (File={result})")
        return result.scalar_one_or_none()

    async def delete(self, file_id: UUID) -> bool:
        logger.debug(f"Удаление файла (file_id={file_id})")
        file = await self.get_by_id(file_id)

        if not file:
            return False

        await self.session.delete(file)
        await self.session.flush()

        logger.debug("Успешно")
        return True
