from functools import lru_cache
from pathlib import Path
from typing import Dict, List

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    class Config:
        env_file = Path(__file__).parents[2] / ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

    # === БАЗА ДАННЫХ PostgreSQL ===
    POSTGRES_HOST: str = Field(default="localhost")
    POSTGRES_PORT: str = Field(default="5432")
    POSTGRES_DB: str = Field(default="StorageBox")
    POSTGRES_USER: str = Field(default="postgres")
    POSTGRES_PASSWORD: str = Field(default="admin")

    @property
    def database_url(self) -> str:
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    # === ХРАНИЛИЩЕ ФАЙЛОВ ===
    STORAGE_TYPE: str = "local"
    STORAGE_PATH: Path = Path(__file__).parents[2] / "storage"

    MAX_FILE_SIZE_MB: int = 250

    MAX_DOCUMENT_SIZE_MB: int = Field(default=MAX_FILE_SIZE_MB)
    MAX_ARCHIVE_SIZE_MB: int = Field(default=MAX_FILE_SIZE_MB)
    MAX_IMAGE_SIZE_MB: int = Field(default=MAX_FILE_SIZE_MB)
    MAX_VIDEO_SIZE_MB: int = Field(default=MAX_FILE_SIZE_MB)
    MAX_AUDIO_SIZE_MB: int = Field(default=MAX_FILE_SIZE_MB)

    MAX_TOTAL_SIZE_FOR_USER_MB: int = 1024

    @property
    def get_max_total_size_for_user_byte(self):
        return self.MAX_TOTAL_SIZE_FOR_USER_MB * 1024 * 1024

    @property
    def get_max_files_size_byte(self):
        return {
            "file": self.MAX_FILE_SIZE_MB * 1024 * 1024,
            "document": self.MAX_DOCUMENT_SIZE_MB * 1024 * 1024,
            "archive": self.MAX_ARCHIVE_SIZE_MB * 1024 * 1024,
            "image": self.MAX_IMAGE_SIZE_MB * 1024 * 1024,
            "video": self.MAX_VIDEO_SIZE_MB * 1024 * 1024,
            "audio": self.MAX_AUDIO_SIZE_MB * 1024 * 1024,
        }

    ALLOWED_EXTENSIONS: Dict[str, List[str]] = {
        # Документы
        "documents": [
            ".pdf",
            ".doc",
            ".docx",
            ".txt",
            ".rtf",
            ".odt",
            ".xls",
            ".xlsx",
            ".ods",
            ".csv",
            ".ppt",
            ".pptx",
            ".odp",
            ".log",
        ],
        # Архивы
        "archives": [".zip", ".rar", ".7z", ".tar", ".gz", ".bz2"],
        # Изображения
        "images": [
            ".jpg",
            ".jpeg",
            ".png",
            ".gif",
            ".bmp",
            ".svg",
            ".webp",
            ".ico",
            ".tiff",
            ".heic",
        ],
        # Видео
        "video": [".mp4", ".avi", ".mkv", ".mov", ".wmv", ".flv", ".webm", ".m4v"],
        # Аудио
        "audio": [".mp3", ".wav", ".flac", ".ogg", ".m4a", ".aac", ".wma"],
    }

    # === === ИНТЕГРАЦИЯ СЕРВИСОВ === ===

    # === ЛОГГЕР ===
    NOISY_LOGGERS: str = ""

    @property
    def noisy_loggers_list(self) -> List[str]:
        """Получить список шумных логгеров из строки"""
        if not self.NOISY_LOGGERS:
            return []
        value = self.NOISY_LOGGERS.strip().strip("'\"")
        if not value:
            return []
        return [logger.strip() for logger in value.split(",") if logger.strip()]


@lru_cache
def get_settings() -> Settings:
    """Получить настройки (кэшируется)"""
    return Settings()
