import uuid
from datetime import datetime

from sqlalchemy import BigInteger, Boolean, Column, DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped, mapped_column

from src.core import get_settings

from .database import Base


class User(Base):
    """Модель пользователя системы"""

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # === ПЕРСОНАЛЬНЫЕ ДАННЫЕ ===
    username: Mapped[str] = mapped_column(String(255), nullable=False, index=True)

    # === КВОТЫ / ЛИМИТЫ ===
    storage_used: Mapped[int] = mapped_column(BigInteger, default=0)
    storage_limit: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        default=get_settings().MAX_TOTAL_SIZE_FOR_USER_MB * 1024 * 1024,
    )

    # === ВРЕМЕННЫЕ МЕТКИ ===
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now(), nullable=False, index=True
    )

    # === БЕЗОПАСНОСТЬ ===
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    files: Mapped[list["File"]] = relationship("File", back_populates="owner")


class File(Base):
    """Модель файлов системы"""

    __tablename__ = "files"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )

    # === МЕТАДАННЫЕ ===
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_size: Mapped[int] = mapped_column(BigInteger, nullable=False)

    # === КАТЕГОРИЯ / РАСШИРЕНИЕ ===
    file_category: Mapped[str] = mapped_column(String(20), nullable=False)
    file_extension: Mapped[str] = mapped_column(String(10), nullable=False)

    # === ХЕШ ===
    md5_hash: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    sha256_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)

    # === ВРЕМЕННЫЕ МЕТКИ ===
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now(), nullable=False, index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now(), onupdate=func.now()
    )
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None, nullable=True)

    owner: Mapped["User"] = relationship("User", back_populates="files")
