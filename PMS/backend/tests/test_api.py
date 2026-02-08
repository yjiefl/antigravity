"""
API 功能测试
"""
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_login(client: AsyncClient, db_session):
    """测试用户登录"""
    # 创建用户在前置 fixture 中可能已经做过，这里直接测登录流程
    # 但 admin_token fixture 会创建 admin。我们创建一个普通用户测登录。
    from app.models import User
    from app.core.security import get_password_hash
    
    user = User(
        username="testuser",
        password_hash=get_password_hash("password123"),
        real_name="Test User",
    )
    db_session.add(user)
    await db_session.commit()
    
    response = await client.post(
        "/api/auth/login",
        data={"username": "testuser", "password": "password123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_get_me(client: AsyncClient, admin_token):
    """测试获取当前用户信息"""
    response = await client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "admin"
    assert data["role"] == "admin"


@pytest.mark.asyncio
async def test_create_task(client: AsyncClient, admin_token):
    """测试创建任务"""
    response = await client.post(
        "/api/tasks",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "title": "测试任务",
            "description": "这是一个单元测试创建的任务",
            "task_type": "performance",
            "category": "project",
            "plan_end": "2026-12-31T23:59:59"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "测试任务"
    assert data["status"] == "draft"


@pytest.mark.asyncio
async def test_task_lifecycle(client: AsyncClient, admin_token):
    """测试任务生命周期状态流转"""
    # 1. 创建任务
    create_res = await client.post(
        "/api/tasks",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"title": "流转测试任务"}
    )
    task_id = create_res.json()["id"]
    
    # 2. 提交审批 (draft -> pending_approval)
    submit_res = await client.post(
        f"/api/tasks/{task_id}/submit",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert submit_res.status_code == 200
    assert submit_res.json()["status"] == "pending_approval"
    
    # 3. 审批通过 (pending_approval -> in_progress)
    approve_res = await client.post(
        f"/api/tasks/{task_id}/approve",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"importance_i": 1.2, "difficulty_d": 1.0}
    )
    assert approve_res.status_code == 200
    assert approve_res.json()["status"] == "in_progress"
    
    # 4. 提交验收 (in_progress -> pending_review)
    complete_res = await client.post(
        f"/api/tasks/{task_id}/complete",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"comment": "完成"}
    )
    assert complete_res.status_code == 200
    assert complete_res.json()["status"] == "pending_review"
    
    # 5. 验收评分 (pending_review -> completed)
    review_res = await client.post(
        f"/api/tasks/{task_id}/review",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"quality_q": 1.1, "comment": "干得好"}
    )
    assert review_res.status_code == 200
    data = review_res.json()
    assert data["status"] == "completed"
    assert data["final_score"] > 0
