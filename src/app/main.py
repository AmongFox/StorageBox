from contextlib import asynccontextmanager

from fastapi import FastAPI
import uvicorn

from src.core import get_logger, initialize_storage
from src.database import migration, get_engine, close_db

logger = get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Запуск приложения")
    await migration()
    await initialize_storage()
    await get_engine()

    yield

    logger.info("Остановка приложения")
    await close_db()


app = FastAPI(
    title="StorageBox",
    description="Сервис управления файловым хранилищем",
    version="1.0.0",
    lifespan=lifespan
)


if __name__ == "__main__":
    uvicorn.run("src.app.main:app", host="0.0.0.0", port=8000, reload=True)
