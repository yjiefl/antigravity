
import asyncio
import os
import sys

# Add project root to sys.path
sys.path.append("/Users/yangjie/code/antigravity/PMS/backend")

from sqlalchemy import select, func, or_, and_
from app.core.database import async_session_maker
from app.models.task import Task
from app.models.user import User, UserRole

async def simulate_query():
    async with async_session_maker() as session:
        # Get the staff user
        stmt = select(User).where(User.username == "staff")
        result = await session.execute(stmt)
        staff = result.unique().scalar_one()
        
        print(f"User: {staff.username}, ID: {staff.id}, Roles: {staff.roles}")
        
        # Simulate list_tasks query
        query = select(Task).where(Task.is_deleted == False)
        
        if UserRole.STAFF in staff.roles and UserRole.ADMIN not in staff.roles and UserRole.MANAGER not in staff.roles:
            print("Applying filter for STAFF...")
            query = query.where(
                or_(
                    Task.creator_id == staff.id,
                    Task.owner_id == staff.id,
                    Task.executor_id == staff.id,
                )
            )
        else:
            print("Not applying visibility filter.")
            
        tasks_result = await session.execute(query)
        tasks = tasks_result.scalars().all()
        print(f"Query returned {len(tasks)} tasks.")
        for t in tasks:
            print(f"- {t.title}")

if __name__ == "__main__":
    asyncio.run(simulate_query())
