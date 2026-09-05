import asyncio
import asyncpg

async def drop_all():
    conn = await asyncpg.connect(
        host='localhost', port=5432, user='backend', password='backendpass', database='postgres'
    )
    # Terminate all connections to agentforge database
    await conn.execute("SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = 'agentforge' AND pid <> pg_backend_pid();")
    # Drop the database
    await conn.execute('DROP DATABASE IF EXISTS agentforge;')
    # Create new database
    await conn.execute('CREATE DATABASE agentforge;')
    await conn.close()
    print('Database dropped and recreated')

asyncio.run(drop_all())