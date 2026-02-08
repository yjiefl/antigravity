"""
文件上传与证据链功能测试
"""
import os
import shutil
import pytest
from httpx import AsyncClient
from app.models import Task, TaskStatus

@pytest.fixture(scope="module")
def cleanup_uploads():
    """测试后清理上传目录"""
    yield
    # 清理 static/uploads 中测试产生的文件
    # 注意：这里简单起见不自动清理，以免误删。实际 CI/CD 中应使用临时目录。
    pass

@pytest.mark.asyncio
async def test_update_progress_with_multiple_files(client: AsyncClient, admin_token, db_session):
    """测试带多个附件更新进度"""
    # 1. 创建任务并推进到进行中...
    create_res = await client.post(
        "/api/tasks",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"title": "多文件上传测试"}
    )
    task_id = create_res.json()["id"]
    await client.post(f"/api/tasks/{task_id}/submit", headers={"Authorization": f"Bearer {admin_token}"})
    await client.post(
        f"/api/tasks/{task_id}/approve",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"importance_i": 1.0, "difficulty_d": 1.0}
    )
    
    # 3. 准备多个测试文件
    files = [
        ('files', ('test1.txt', b'content 1', 'text/plain')),
        ('files', ('test2.jpg', b'fake image data', 'image/jpeg'))
    ]
    data = {'progress': 30, 'content': '更新进度带两个附件'}
    
    # 4. 更新进度
    response = await client.post(
        f"/api/tasks/{task_id}/progress",
        headers={"Authorization": f"Bearer {admin_token}"},
        data=data,
        files=files
    )
    
    assert response.status_code == 200
    
    # 5. 验证日志中的附件记录
    logs_res = await client.get(
        f"/api/tasks/{task_id}/logs",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    logs = logs_res.json()
    progress_log = next(l for l in logs if l["action"] == "progress_updated")
    
    assert len(progress_log["attachments"]) == 2
    assert progress_log["attachments"][0]["filename"] == "test1.txt"
    assert progress_log["attachments"][1]["filename"] == "test2.jpg"
    
    # 6. 测试下载
    att_id = progress_log["attachments"][0]["id"]
    dl_res = await client.get(
        f"/api/attachments/{att_id}/download",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert dl_res.status_code == 200
    assert dl_res.content == b'content 1'
