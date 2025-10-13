"""
Run Onboarding Links Migration Script
"""
import asyncio
import asyncpg

async def run_migration():
    """Run the onboarding links migration"""
    conn = await asyncpg.connect(
        host="localhost",
        port=5432,
        user="postgres",
        password="12345",
        database="salesbrain_tenant"
    )

    try:
        # Read migration SQL
        with open("sql/migration_phase3_onboarding_links.sql", "r") as f:
            sql = f.read()

        # Execute migration
        await conn.execute(sql)

        print("✅ Onboarding Links migration completed successfully!")

    except Exception as e:
        print(f"❌ Migration failed: {e}")
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(run_migration())
