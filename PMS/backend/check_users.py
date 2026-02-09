import asyncio
import asyncpg
import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://pms:pms_secret_2026@localhost:5432/plan_management").replace("+asyncpg", "")

async def check():
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        rows = await conn.fetch("SELECT id, username, real_name FROM users")
        for row in rows:
            print(f"{row['id']}: {row['username']} ({row['real_name']})")
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(check())
