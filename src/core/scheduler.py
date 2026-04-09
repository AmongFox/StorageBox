from pathlib import Path

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from src.core import get_logger
from src.database import FileCRUD, UserCRUD, get_session_factory

logger = get_logger()
scheduler = AsyncIOScheduler()


async def _cleanup_expired_files():
    logger.info("Запуск задачи: Очистка просроченных файлов")

    factory = await get_session_factory()
    async with factory() as session:
        file_crud = FileCRUD(session)
        user_crud = UserCRUD(session)

        expired_files = await file_crud.get_expired()

        for file in expired_files:
            try:
                file_path = Path(file.file_path)
                if file_path.exists():
                    file_path.unlink()
                    logger.info(f"Файл {file_path} удалён с диска")

                await file_crud.delete(file.id)
                logger.info(f"Файл {file_path} удалён с базы данных")
            except Exception as e:
                logger.error(f"Ошибка во время удаления файла: {file_path}: {e}")
                continue

            await user_crud.decrement_storage_used(file.owner_id, file.file_size)

        logger.info("Очистка завершена")


scheduler.add_job(
    _cleanup_expired_files,
    "interval",
    hours=1,
    id="cleanup_expired_files",
    replace_existing=True,
)
