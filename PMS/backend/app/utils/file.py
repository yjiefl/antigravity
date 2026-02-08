"""
文件处理工具模块
"""
import os
import shutil
import uuid
from datetime import datetime
from pathlib import Path
from fastapi import UploadFile, HTTPException, status

from app.core.config import get_settings

settings = get_settings()
UPLOAD_DIR = Path("static/uploads")
MAX_FILE_SIZE = settings.max_file_size
ALLOWED_TYPES = settings.allowed_file_types

async def save_upload_file(file: UploadFile) -> dict:
    """
    保存上传的文件并返回元数据
    """
    # 验证文件类型
    is_allowed = False
    content_type = file.content_type or ""
    for allowed in ALLOWED_TYPES:
        if content_type.startswith(allowed):
            is_allowed = True
            break
    
    if not is_allowed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"文件类型 '{content_type}' 不在允许范围内"
        )
        
    today = datetime.now().strftime("%Y%m%d")
    save_dir = UPLOAD_DIR / today
    save_dir.mkdir(parents=True, exist_ok=True)
    
    ext = os.path.splitext(file.filename)[1].lower()
    if not ext:
        ext = ".bin"
        
    unique_filename = f"{uuid.uuid4().hex}{ext}"
    file_path = save_dir / unique_filename
    
    size = 0
    try:
        with open(file_path, "wb") as buffer:
            while content := await file.read(1024 * 1024):
                size += len(content)
                if size > MAX_FILE_SIZE:
                    buffer.close()
                    os.remove(file_path)
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=f"文件 '{file.filename}' 大小超过限制 ({MAX_FILE_SIZE/1024/1024}MB)"
                    )
                buffer.write(content)
    except Exception as e:
        if isinstance(e, HTTPException): raise e
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"文件保存失败: {str(e)}"
        )
    finally:
        await file.close()
        
    return {
        "filename": file.filename,
        "file_path": f"/static/uploads/{today}/{unique_filename}",
        "file_type": file.content_type or "application/octet-stream",
        "file_size": size
    }


async def save_multiple_files(files: list[UploadFile]) -> list[dict]:
    """
    保存多个上传文件
    """
    results = []
    for file in files:
        if file and file.filename:
            res = await save_upload_file(file)
            results.append(res)
    return results
