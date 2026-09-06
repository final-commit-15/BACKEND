# Alembic migration environment configuration
import os
import sys
from logging.config import fileConfig
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# Add the parent directory to sys.path so we can import our models
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# Import our models
from src.agentforge_backend.models import Base
from src.agentforge_backend.config.settings import settings

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Determine the database URL for migrations
migration_db_url = settings.DATABASE_URL

# Check if we're running inside Docker
running_in_docker = os.environ.get("ALEMBIC_DOCKER", "0") == "1"

if running_in_docker:
    # Inside Docker, use the service name as-is
    print(f"Running inside Docker, using service name: {migration_db_url}")
else:
    # Outside Docker (host), only replace Docker service names in the host part
    # URL format: scheme://[user:pass@]host:port/database
    # We only replace if host is a Docker service name (postgres, db)
    # and NOT a real hostname like db.xxx.supabase.co
    
    def replace_docker_service(url: str) -> str:
        # Check if URL already has a real hostname (contains a dot in host part)
        # Real hostnames like db.xxx.supabase.co have dots, Docker services don't
        
        # Find the authority part: //[user:pass@]host[:port]
        # Split by // to get authority part
        if '://' not in url:
            return url
        
        scheme, rest = url.split('://', 1)
        
        # Find the end of authority (start of path)
        # Authority ends at / or end of string
        auth_end = len(rest)
        for sep in ['/', '?', '#']:
            idx = rest.find(sep)
            if idx != -1 and idx < auth_end:
                auth_end = idx
        
        authority = rest[:auth_end]
        path = rest[auth_end:]
        
        # Split authority into [user:pass@]host[:port]
        # Find the last @ to separate user:pass from host
        at_idx = authority.rfind('@')
        if at_idx != -1:
            userinfo = authority[:at_idx+1]
            hostport = authority[at_idx+1:]
        else:
            userinfo = ''
            hostport = authority
        
        # Split host:port
        if ':' in hostport:
            host, port = hostport.split(':', 1)
        else:
            host = hostport
            port = ''
        
        # Only replace if host is a Docker service name (no dots)
        # Real hostnames have dots like db.xxx.supabase.co
        if host in ('postgres', 'db') and '.' not in host:
            new_host = 'localhost'
            new_hostport = f'{new_host}:{port}' if port else new_host
            new_authority = f'{userinfo}{new_hostport}'
            return f'{scheme}://{new_authority}{path}'
        
        return url
    
    migration_db_url = replace_docker_service(migration_db_url)
    print(f"Running on host, using: {migration_db_url}")

config.set_main_option("sqlalchemy.url", migration_db_url)

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    from sqlalchemy.ext.asyncio import create_async_engine
    from sqlalchemy import pool

    # Use the migration database URL directly (already set in config)
    migration_db_url = config.get_main_option("sqlalchemy.url")
    print(f"Migration DB URL (async): {migration_db_url}")  # Debug output

    connectable = create_async_engine(
        migration_db_url,
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    import asyncio
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()