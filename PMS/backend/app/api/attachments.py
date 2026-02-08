"""
附件管理 API
"""
import uuid
from typing import Annotated, List

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.auth import get_current_user
from app.models import User, Attachment

router = APIRouter()


@router.get("/{attachment_id}/download")
async def download_attachment(
    attachment_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """
    下载附件并增加下载统计
    """
    result = await db.execute(
        select(Attachment).where(Attachment.id == attachment_id)
    )
    attachment = result.scalar_one_or_none()
    
    if not attachment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="附件不存在"
        )
    
    # 增加下载计数
    await db.execute(
        update(Attachment)
        .where(Attachment.id == attachment_id)
        .values(download_count=Attachment.download_count + 1)
    )
    await db.commit()
    
    # 返回文件
    # 注意: attachment.file_path 是相对路径，如 /static/uploads/...
    # 我们需要将其转换为物理路径。假设 static 目录在项目根目录。
    physical_path = attachment.file_path.lstrip("/")
    
    return FileResponse(
        path=physical_path,
        filename=attachment.filename,
        media_type=attachment.file_type
    )


@router.delete("/{attachment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_attachment(
    attachment_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """
    删除附件记录 (物理文件保留或可选删除)
    """
    result = await db.execute(
        select(Attachment).where(Attachment.id == attachment_id)
    )
    attachment = result.scalar_one_or_none()
    
    if not attachment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="附件不存在"
        )
    
    # 鉴权: 只有上传人或管理员可删除
    if attachment.uploader_id != current_user.id and current_user.role != "admin":
         raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权删除该附件"
        )
         
    await db.delete(attachment)
    await db.commit()
    
    return None
