import asyncio
import asyncpg
import os

# From environment or hardcoded fallback
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://pms:pms_secret_2026@localhost:5432/plan_management")
# Strip +asyncpg for asyncpg.connect
if "+asyncpg" in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.replace("+asyncpg", "")

async def migrate():
    print(f"Connecting to PostgreSQL at {DATABASE_URL.split('@')[-1]}...")
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        try:
            print("Adding columns to tasks table...")
            # We use a safer approach: add if not exists (Postgres 9.6+)
            # But simple ALTER TABLE with try/except is also fine in a script.
            
            queries = [
                "ALTER TABLE tasks ADD COLUMN IF NOT EXISTS extension_status VARCHAR(20)",
                "ALTER TABLE tasks ADD COLUMN IF NOT EXISTS extension_reason TEXT",
                "ALTER TABLE tasks ADD COLUMN IF NOT EXISTS extension_date TIMESTAMPTZ",
                "ALTER TABLE tasks ADD COLUMN IF NOT EXISTS reviewer_id UUID"
            ]
            
            for query in queries:
                try:
                    await conn.execute(query)
                    print(f"Executed: {query}")
                except Exception as e:
                    print(f"Error executing {query}: {e}")
            
            print("Successfully updated PostgreSQL schema.")
        finally:
            await conn.close()
    except Exception as e:
        print(f"Failed to connect or migrate: {e}")

if __name__ == "__main__":
    asyncio.run(migrate())
