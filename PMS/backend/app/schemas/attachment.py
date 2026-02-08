"""
附件 Pydantic 模型
"""
import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class AttachmentBase(BaseModel):
    filename: str = Field(..., description="原始文件名")
    file_type: str = Field(..., description="文件类型")
    file_size: int = Field(..., description="文件大小 (Bytes)")


class AttachmentCreate(AttachmentBase):
    file_path: str = Field(..., description="存储相对路径")
    task_id: Optional[uuid.UUID] = None
    log_id: Optional[uuid.UUID] = None
    uploader_id: Optional[uuid.UUID] = None


class AttachmentResponse(AttachmentBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    file_path: str = Field(..., description="文件URL/路径")
    download_count: int
    created_at: datetime
    uploader_id: Optional[uuid.UUID] = None
