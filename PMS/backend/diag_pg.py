
import asyncio
import os
import sys

# Add project root to sys.path
sys.path.append("/Users/yangjie/code/antigravity/PMS/backend")

from sqlalchemy import select, func, or_
from app.core.database import async_session_maker
from app.models.task import Task
from app.models.user import User

async def diag():
    async with async_session_maker() as session:
        # 1. Total status
        total = await session.scalar(select(func.count(Task.id)))
        active = await session.scalar(select(func.count(Task.id)).where(Task.is_deleted == False))
        print(f"Total tasks: {total}, Active tasks: {active}")

        # 2. Get Users
        users_result = await session.execute(select(User))
        users = users_result.unique().scalars().all()
        user_map = {u.id: u.username for u in users}
        print("\nUsers and Roles:")
        for u in users:
            print(f"- {u.username} (ID: {u.id}): {u.roles}")

        # 3. List active tasks
        tasks_result = await session.execute(
            select(Task)
            .where(Task.is_deleted == False)
        )
        tasks = tasks_result.scalars().all()
        print("\nActive Tasks Detail:")
        for t in tasks:
            creator_id = t.creator_id
            owner_id = t.owner_id
            executor_id = t.executor_id
            
            creator = user_map.get(creator_id, "Unknown")
            owner = user_map.get(owner_id, owner_id) if owner_id else "None"
            executor = user_map.get(executor_id, executor_id) if executor_id else "None"
            
            print(f"- [{t.status}] {t.title}")
            print(f"  IDs: Creator={creator_id}, Owner={owner_id}, Executor={executor_id}")
            print(f"  Names: Creator={creator}, Owner={owner}, Executor={executor}")

if __name__ == "__main__":
    asyncio.run(diag())
