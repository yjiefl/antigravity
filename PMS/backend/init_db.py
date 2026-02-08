"""
初始化脚本

创建默认管理员账户和示例数据
"""
import asyncio
import uuid
from datetime import datetime, timezone, timedelta

from app.core.database import async_session_maker, init_db
from app.core.security import get_password_hash
from app.models import (
    Organization, Department, Position, User, UserRole, UserRoleBinding,
    Task, TaskStatus, TaskType, TaskCategory
)


async def create_admin():
    """创建管理员账户"""
    async with async_session_maker() as session:
        # 检查是否已存在
        from sqlalchemy import select
        result = await session.execute(
            select(User).where(User.username == "admin")
        )
        if result.scalar_one_or_none():
            print("管理员账户已存在")
            return
        
        # 创建公司
        org = Organization(name="示例公司", code="DEMO")
        session.add(org)
        await session.flush()
        
        # 创建部门
        dept = Department(
            name="技术部", 
            code="TECH", 
            organization_id=org.id
        )
        session.add(dept)
        await session.flush()
        
        # 创建岗位
        manager_pos = Position(
            name="技术主管",
            code="TECH_MGR",
            department_id=dept.id,
            can_assign_task=True,
            can_transfer_task=True
        )
        staff_pos = Position(
            name="开发工程师",
            code="DEV",
            department_id=dept.id
        )
        session.add_all([manager_pos, staff_pos])
        await session.flush()
        
        # 创建管理员
        admin = User(
            username="admin",
            password_hash=get_password_hash("admin123"),
            real_name="管理员",
            roles_binding=[UserRoleBinding(role=UserRole.ADMIN)],
            department_id=dept.id,
            position_id=manager_pos.id,
        )
        session.add(admin)
        
        # 创建主管
        manager = User(
            username="manager",
            password_hash=get_password_hash("manager123"),
            real_name="张主管",
            roles_binding=[UserRoleBinding(role=UserRole.MANAGER)],
            department_id=dept.id,
            position_id=manager_pos.id,
        )
        session.add(manager)
        
        # 创建员工
        staff = User(
            username="staff",
            password_hash=get_password_hash("staff123"),
            real_name="李员工",
            roles_binding=[UserRoleBinding(role=UserRole.STAFF)],
            department_id=dept.id,
            position_id=staff_pos.id,
        )
        session.add(staff)
        await session.flush()
        
        # 创建示例任务
        now = datetime.now(timezone.utc)
        task1 = Task(
            title="完成系统需求分析",
            description="根据用户需求，完成系统功能需求分析文档",
            task_type=TaskType.PERFORMANCE,
            category=TaskCategory.PROJECT,
            status=TaskStatus.COMPLETED,
            importance_i=1.2,
            difficulty_d=1.0,
            quality_q=1.1,
            progress=100,
            plan_start=now - timedelta(days=10),
            plan_end=now - timedelta(days=3),
            actual_start=now - timedelta(days=10),
            actual_end=now - timedelta(days=4),
            final_score=132.0,
            creator_id=manager.id,
            owner_id=manager.id,
            executor_id=staff.id,
        )
        
        task2 = Task(
            title="开发用户登录模块",
            description="实现用户登录、登出、JWT 认证功能",
            task_type=TaskType.PERFORMANCE,
            category=TaskCategory.PROJECT,
            status=TaskStatus.IN_PROGRESS,
            importance_i=1.0,
            difficulty_d=1.2,
            progress=60,
            plan_start=now - timedelta(days=5),
            plan_end=now + timedelta(days=2),
            actual_start=now - timedelta(days=5),
            creator_id=manager.id,
            owner_id=manager.id,
            executor_id=staff.id,
        )
        
        task3 = Task(
            title="编写技术文档",
            description="编写系统技术架构和 API 文档",
            task_type=TaskType.PERFORMANCE,
            category=TaskCategory.ROUTINE,
            status=TaskStatus.DRAFT,
            progress=0,
            creator_id=staff.id,
        )
        
        session.add_all([task1, task2, task3])
        await session.commit()
        
        print("✅ 初始化完成！")
        print("\n账户信息：")
        print("  管理员: admin / admin123")
        print("  主管: manager / manager123")
        print("  员工: staff / staff123")


async def main():
    """主函数"""
    print("🚀 初始化数据库...")
    await init_db()
    print("✅ 数据库表创建完成")
    
    print("\n📝 创建初始数据...")
    await create_admin()


if __name__ == "__main__":
    asyncio.run(main())
