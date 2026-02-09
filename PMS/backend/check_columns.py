import asyncio
import asyncpg
import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://pms:pms_secret_2026@localhost:5432/plan_management").replace("+asyncpg", "")

async def check():
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        rows = await conn.fetch("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'tasks'")
        for row in rows:
            print(f"{row['column_name']}: {row['data_type']}")
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(check())
