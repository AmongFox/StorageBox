from pathlib import Path

from src.core import get_settings, get_logger

logger = get_logger()

STORAGE_CATALOGS = [
    "documents",
    "archives",
    "images",
    "video",
    "audio"
]


def _init_dirs():
    logger.info("Создание каталогов")

    base_path = Path(get_settings().STORAGE_PATH)
    base_path.mkdir(parents=True, exist_ok=True)

    for catalog in STORAGE_CATALOGS:
        logger.info(f"{(base_path / catalog)} [SUCCESS]")
        (base_path / catalog).mkdir(exist_ok=True)


async def initialize_storage():
    logger.info("Инициализация хранилища")
    _init_dirs()
