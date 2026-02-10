
import asyncio
import os
import sys

# Add project root to sys.path
sys.path.append("/Users/yangjie/code/antigravity/PMS/backend")

from sqlalchemy import select, or_
from app.core.database import async_session_maker
from app.models.task import Task
from app.models.user import User, UserRole

async def debug_tasks():
    async with async_session_maker() as session:
        # User ID for staff
        user_id_str = "869e63c4-59d4-49e1-8753-0482398c4ba6"
        stmt = select(User).where(User.id == user_id_str)
        result = await session.execute(stmt)
        user = result._unique_strategy().scalar_one() # Using _unique_strategy for older sa or just unique()
        
        print(f"DEBUG: User {user.username}, Roles: {user.roles}")
        
        # Build query exactly like in tasks.py
        query = select(Task).where(Task.is_deleted == False)
        
        is_staff = UserRole.STAFF in user.roles
        is_admin = UserRole.ADMIN in user.roles
        is_manager = UserRole.MANAGER in user.roles
        
        print(f"is_staff: {is_staff}, is_admin: {is_admin}, is_manager: {is_manager}")
        
        if is_staff and not is_admin and not is_manager:
            print("Applying visibility filter")
            query = query.where(
                or_(
                    Task.creator_id == user.id,
                    Task.owner_id == user.id,
                    Task.executor_id == user.id,
                )
            )
        
        res = await session.execute(query)
        tasks = res.scalars().all()
        print(f"Found {len(tasks)} tasks")

if __name__ == "__main__":
    asyncio.run(debug_tasks())
