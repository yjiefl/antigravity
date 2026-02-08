"""
任务工作流测试 (Task Workflow Tests)
"""
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_withdraw_success(client: AsyncClient, staff_token):
    """测试撤回申请 (Staff)"""
    # 1. 创建任务
    create_res = await client.post(
        "/api/tasks",
        headers={"Authorization": f"Bearer {staff_token}"},
        json={"title": "撤回测试任务"}
    )
    assert create_res.status_code == 201
    task_id = create_res.json()["id"]
    
    # 2. 提交审批
    await client.post(
        f"/api/tasks/{task_id}/submit",
        headers={"Authorization": f"Bearer {staff_token}"}
    )
    
    # 3. 撤回
    withdraw_res = await client.post(
        f"/api/tasks/{task_id}/withdraw",
        headers={"Authorization": f"Bearer {staff_token}"}
    )
    assert withdraw_res.status_code == 200
    assert withdraw_res.json()["status"] == "draft"


@pytest.mark.asyncio
async def test_withdraw_forbidden(client: AsyncClient, staff_token, admin_token):
    """测试非创建者/负责人不可撤回"""
    # 1. Staff 创建并提交
    create_res = await client.post(
        "/api/tasks",
        headers={"Authorization": f"Bearer {staff_token}"},
        json={"title": "撤回权限测试"}
    )
    task_id = create_res.json()["id"]
    await client.post(
        f"/api/tasks/{task_id}/submit",
        headers={"Authorization": f"Bearer {staff_token}"}
    )
    
    # 2. Admin 尝试撤回 (Admin 不是 creator/owner)
    # 注意：Admin 虽然权限高，但 withdraw 接口目前限制死只能 creator/owner
    withdraw_res = await client.post(
        f"/api/tasks/{task_id}/withdraw",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert withdraw_res.status_code == 403


@pytest.mark.asyncio
async def test_return_approval_success(client: AsyncClient, staff_token, manager_token):
    """测试退回任务 - 待审批阶段 (Manager)"""
    # 1. Staff 创建并提交
    create_res = await client.post(
        "/api/tasks",
        headers={"Authorization": f"Bearer {staff_token}"},
        json={"title": "退回测试任务"}
    )
    task_id = create_res.json()["id"]
    await client.post(
        f"/api/tasks/{task_id}/submit",
        headers={"Authorization": f"Bearer {staff_token}"}
    )
    
    # 2. Manager 退回
    return_res = await client.post(
        f"/api/tasks/{task_id}/return?reason=不合格",
        headers={"Authorization": f"Bearer {manager_token}"}
    )
    assert return_res.status_code == 200
    assert return_res.json()["status"] == "draft"


@pytest.mark.asyncio
async def test_return_review_success(client: AsyncClient, staff_token, manager_token):
    """测试退回任务 - 待验收阶段 (Manager)"""
    # 1. Create -> Submit -> Approve -> Progress -> Complete
    create_res = await client.post(
        "/api/tasks",
        headers={"Authorization": f"Bearer {staff_token}"},
        json={"title": "验收退回测试"}
    )
    task_id = create_res.json()["id"]
    
    await client.post(f"/api/tasks/{task_id}/submit", headers={"Authorization": f"Bearer {staff_token}"})
    
    # Manager Approve
    await client.post(
        f"/api/tasks/{task_id}/approve",
        headers={"Authorization": f"Bearer {manager_token}"},
        json={"importance_i": 1.0, "difficulty_d": 1.0}
    )
    
    # Staff Update Progress & Complete
    await client.post(
        f"/api/tasks/{task_id}/progress",
         headers={"Authorization": f"Bearer {staff_token}"},
         data={"progress": 100}
    )
    await client.post(
        f"/api/tasks/{task_id}/complete",
        headers={"Authorization": f"Bearer {staff_token}"},
        data={"comment": "done"}
    )
    
    # 2. Manager Return (Reject Review)
    return_res = await client.post(
        f"/api/tasks/{task_id}/return?reason=重做",
        headers={"Authorization": f"Bearer {manager_token}"}
    )
    assert return_res.status_code == 200
    assert return_res.json()["status"] == "in_progress"


@pytest.mark.asyncio
async def test_return_forbidden(client: AsyncClient, staff_token):
    """测试普通员工无法退回任务"""
    # Staff cannot call return endpoint (it requires manager/admin)
    # We need a task first, but any ID checks auth first
    import uuid
    random_id = str(uuid.uuid4())
    
    return_res = await client.post(
        f"/api/tasks/{random_id}/return?reason=test",
        headers={"Authorization": f"Bearer {staff_token}"}
    )
    assert return_res.status_code == 403
