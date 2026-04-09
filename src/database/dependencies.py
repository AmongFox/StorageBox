from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import FileCRUD, UserCRUD, get_session


async def get_user_crud(session: AsyncSession = Depends(get_session)) -> UserCRUD:
    return UserCRUD(session)


async def get_file_crud(session: AsyncSession = Depends(get_session)) -> FileCRUD:
    return FileCRUD(session)
