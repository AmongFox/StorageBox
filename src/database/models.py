import uuid
from sqlalchemy import Column, ForeignKey, String, BigInteger, DateTime, func, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID

from src.core import get_settings
from .database import Base


class User(Base):
    """Модель пользователя системы"""

    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # === ПЕРСОНАЛЬНЫЕ ДАННЫЕ ===
    username = Column(String(255), nullable=False, index=True)

    # === КВОТЫ / ЛИМИТЫ ===
    storage_used = Column(BigInteger, default=0)
    storage_limit = Column(BigInteger, nullable=False, default=get_settings().MAX_TOTAL_SIZE_FOR_USER_MB * 1024 * 1024)

    # === ВРЕМЕННЫЕ МЕТКИ ===
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False, index=True)

    # === БЕЗОПАСНОСТЬ ===
    is_active = Column(Boolean, default=True)

    files = relationship("File", back_populates="owner")


class File(Base):
    """Модель файлов системы"""
    __tablename__ = "files"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True)

    # === МЕТАДАННЫЕ ===
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(BigInteger, nullable=False)

    # === КАТЕГОРИЯ / РАСШИРЕНИЕ ===
    file_category = Column(String(20), nullable=False)
    file_extension = Column(String(10), nullable=False)

    # === ХЕШ ===
    md5_hash = Column(String(32), nullable=True, index=True)
    sha256_hash = Column(String(64), nullable=True)

    # === ВРЕМЕННЫЕ МЕТКИ ===
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())
    expires_at = Column(DateTime(timezone=True), default=None, nullable=True)

    owner = relationship("User", back_populates="files")
