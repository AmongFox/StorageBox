import sys
from functools import lru_cache
from pathlib import Path
from typing import Optional

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import declarative_base

from alembic import command
from alembic.config import Config as AlembicConfig
from src.core import get_logger, get_settings

logger = get_logger()

Base = declarative_base()

IS_WINDOWS = sys.platform == "win32"


@lru_cache
def get_db_config():
    """Получает настройки БД только когда они действительно нужны"""
    return {
        "url": get_settings().database_url,
        "debug": False,
        "pool_config": get_pool_config(),
    }


def get_pool_config():
    """Получение конфигурации пула с использованием настроек"""
    if IS_WINDOWS:
        return {
            "pool_size": 5,
            "max_overflow": 10,
            "pool_pre_ping": True,
            "pool_recycle": 300,  # 5 минут
            "pool_timeout": 30,
        }
    else:
        return {
            "pool_size": 10,
            "max_overflow": 20,
            "pool_pre_ping": True,
            "pool_recycle": 3600,  # 1 час
            "pool_timeout": 30,
        }


_engine: Optional[AsyncEngine] = None
_async_session_factory = None


async def get_engine():
    """Ленивое создание engine"""
    global _engine
    if _engine is None:
        db_config = get_db_config()

        engine_kwargs = {
            "future": True,
            "echo": False,
            "echo_pool": False,
            **db_config["pool_config"],
        }

        if "postgresql" in db_config["url"]:
            engine_kwargs["connect_args"] = {
                "command_timeout": 60,
                "server_settings": {
                    "application_name": "storagebox",
                    "statement_timeout": "30000",
                    "lock_timeout": "10000",
                },
            }

        _engine = create_async_engine(db_config["url"], **engine_kwargs)
        logger.debug("Database engine created")

    return _engine


async def get_session_factory():
    """Ленивое создание фабрики сессий"""
    global _async_session_factory
    if _async_session_factory is None:
        engine = await get_engine()
        _async_session_factory = async_sessionmaker(
            engine,
            expire_on_commit=False,
            class_=AsyncSession,
            autoflush=False,
            autocommit=False,
        )
        logger.debug("Session factory created")

    return _async_session_factory


async def get_session() -> AsyncSession:
    """Получение сессии базы данных (Обеспечение атомарности)"""
    factory = await get_session_factory()
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def close_db():
    """Закрытие соединений при остановке приложения"""
    global _engine, _async_session_factory
    if _engine:
        await _engine.dispose()
        logger.debug("Database engine disposed")
        _engine = None
        _async_session_factory = None


async def migration():
    """Применение миграций базы данных"""
    logger.info("Применение миграций базы данных")
    root_dir = Path(__file__).resolve().parents[2]
    alembic_ini = root_dir / "alembic.ini"
    alembic_dir = root_dir / "alembic"

    alembic_cfg = AlembicConfig(str(alembic_ini))
    alembic_cfg.set_main_option("sqlalchemy.url", get_settings().database_url)
    alembic_cfg.set_main_option("script_location", str(alembic_dir))
    command.upgrade(alembic_cfg, "head")
    logger.info("Миграции успешно применены")
