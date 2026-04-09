from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from src.core.scheduler import scheduler
from src.app.api import files_router, users_router
from src.core import get_logger, initialize_storage
from src.database import close_db, get_engine, migration

logger = get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Запуск приложения")
    await migration()
    await initialize_storage()
    await get_engine()

    scheduler.start()

    yield

    logger.info("Остановка приложения")
    await close_db()


app = FastAPI(
    title="StorageBox",
    description="Сервис управления файловым хранилищем",
    version="1.0.0",
    lifespan=lifespan,
)
app.include_router(files_router)
app.include_router(users_router)


if __name__ == "__main__":
    uvicorn.run("src.app.main:app", host="0.0.0.0", port=8001, reload=True)
