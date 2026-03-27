from typing import Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.core import get_logger
from src.database.models import User, File

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

    async def create(self, username: str) -> User:
        logger.debug(f"Запись пользователя (username={username})")
        user = User(username=username)

        self.session.add(user)
        await self.session.flush()
        await self.session.refresh(user)

        logger.debug(f"Успешно (User={user})")
        return user

    async def get_by_id(self, user_id: int) -> Optional[User]:
        logger.debug(f"Получение пользователя (user_id={user_id})")
        result = await self.session.execute(select(User).where(User.id == user_id))
        logger.debug(f"Успешно (User={result})")
        return result.scalar_one_or_none()

    async def get_by_username(self, username: str) -> Optional[User]:
        logger.debug(f"Получение пользователя (username={username})")
        result = await self.session.execute(select(User).where(User.username == username))
        logger.debug(f"Успешно (User={result})")
        return result.scalar_one_or_none()

    async def update(
        self,
        user_id: int,
        username: Optional[str] = None,
        email: Optional[str] = None,
        is_active: Optional[bool] = None
    ):
        logger.debug(f"Обновление пользователя (user_id={user_id})")
        update_data = {}

        if username is not None:
            update_data["username"] = username
        if email is not None:
            update_data["email"] = email
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

    async def delete(self, user_id: int) -> bool:
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
        filename: str,
        file_path: str,
        file_size: str,
        file_category: str,
        file_extension: str,
    ):
        logger.debug(f"Запись файла (filename={filename})")
        file = File(
            filename=filename,
            file_path=file_path,
            file_size=file_size,
            file_category=file_category,
            file_extension=file_extension
        )

        self.session.add(file)
        await self.session.flush()
        await self.session.refresh(file)

        logger.debug(f"Успешно (File={file})")
        return file

    async def get_by_id(self, file_id: int) -> Optional[File]:
        logger.debug(f"Получение файла (file_id={file_id})")
        result = await self.session.execute(select(File).where(File.id == file_id))
        logger.debug(f"Успешно (File={result})")
        return result.scalar_one_or_none()

    async def update(
            self,
            file_id: int,
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

    async def delete(self, file_id: int) -> bool:
        logger.debug(f"Удаление файла (file_id={file_id})")
        file = await self.get_by_id(file_id)

        if not file:
            return False

        await self.session.delete(file)
        await self.session.flush()

        logger.debug("Успешно")
        return True
