"""
Run User Assignment Migration
"""
import asyncio
import asyncpg
from app.core.config import settings

async def run_migration():
    """Execute user assignment migration"""
    conn = await asyncpg.connect(settings.database_tenant_url)
    try:
        with open('sql/migration_phase3_user_assignments.sql', 'r', encoding='utf-8') as f:
            sql = f.read()

        await conn.execute(sql)
        print('User Assignment Migration executed successfully!')

    except Exception as e:
        print(f'Migration failed: {e}')
        raise
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(run_migration())
