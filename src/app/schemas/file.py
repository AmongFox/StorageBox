import uuid
from datetime import datetime
from typing import Optional, List

from pydantic import Field, BaseModel


class FileCreate(BaseModel):
    filename: str = Field(..., min_length=1, max_length=255)
    file_size: int = Field(..., gt=0)
    file_category: str = Field(..., max_length=20)
    file_extension: str = Field(..., max_length=10)


class FileUpdate(BaseModel):
    filename: Optional[str] = Field(None, min_length=1, max_length=255)
    file_category: Optional[str] = Field(None, max_length=20)


class FileInfoResponse(BaseModel):
    file_id: uuid.UUID
    filename: str
    file_size: int
    file_category: str
    created_at: datetime
    expires_at: Optional[datetime] = None
    owner_id: uuid.UUID

    class Config:
        from_attributes = True


class FileListResponse(BaseModel):
    files: List[FileInfoResponse]
    total: int
