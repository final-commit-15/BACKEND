"""
Supabase Client Module

Provides singleton async Supabase clients for both anon and service role operations.
"""
import asyncio
import logging
from typing import Optional
from functools import lru_cache

from supabase import create_client, Client, AsyncClient
from supabase.lib.client_options import ClientOptions

from ..config.settings import settings

logger = logging.getLogger(__name__)

# Singleton instances
_supabase_anon: Optional[AsyncClient] = None
_supabase_admin: Optional[AsyncClient] = None
_init_lock = asyncio.Lock()


def _get_client_options() -> ClientOptions:
    """Create client options with timeouts and retries."""
    return ClientOptions(
        postgrest_client_timeout=30,
        storage_client_timeout=30,
        schema="public",
    )


async def get_supabase() -> AsyncClient:
    """
    Get or create the anon Supabase client.
    
    This client uses the anon key and is suitable for operations
    that respect Row Level Security policies.
    
    Returns:
        AsyncClient: Configured Supabase client with anon key
    """
    global _supabase_anon
    
    if _supabase_anon is not None:
        return _supabase_anon
    
    async with _init_lock:
        if _supabase_anon is not None:
            return _supabase_anon
        
        if not settings.SUPABASE_URL or not settings.SUPABASE_ANON_KEY:
            raise RuntimeError(
                "SUPABASE_URL and SUPABASE_ANON_KEY must be configured"
            )
        
        logger.info("Initializing Supabase anon client")
        
        _supabase_anon = create_client(
            supabase_url=settings.SUPABASE_URL,
            supabase_key=settings.SUPABASE_ANON_KEY,
            options=_get_client_options(),
        )
        
        # Test connection
        try:
            await _supabase_anon.auth.get_user()
        except Exception as e:
            logger.warning(f"Supabase anon client health check failed: {e}")
        
        logger.info("Supabase anon client initialized successfully")
        return _supabase_anon


async def get_supabase_admin() -> AsyncClient:
    """
    Get or create the service role Supabase client.
    
    This client uses the service role key and bypasses Row Level Security.
    Use only for administrative operations that require elevated privileges.
    
    Returns:
        AsyncClient: Configured Supabase client with service role key
    """
    global _supabase_admin
    
    if _supabase_admin is not None:
        return _supabase_admin
    
    async with _init_lock:
        if _supabase_admin is not None:
            return _supabase_admin
        
        if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_ROLE_KEY:
            raise RuntimeError(
                "SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be configured"
            )
        
        logger.info("Initializing Supabase admin (service role) client")
        
        _supabase_admin = create_client(
            supabase_url=settings.SUPABASE_URL,
            supabase_key=settings.SUPABASE_SERVICE_ROLE_KEY,
            options=_get_client_options(),
        )
        
        # Test connection
        try:
            await _supabase_admin.auth.admin.list_users()
        except Exception as e:
            logger.warning(f"Supabase admin client health check failed: {e}")
        
        logger.info("Supabase admin client initialized successfully")
        return _supabase_admin


async def supabase_health_check() -> dict:
    """
    Perform health check on Supabase connections.
    
    Returns:
        dict: Health status of both anon and admin clients
    """
    results = {
        "anon": {"status": "unknown", "error": None},
        "admin": {"status": "unknown", "error": None},
    }
    
    # Check anon client
    try:
        client = await get_supabase()
        # Simple query to test connection
        await client.table("users").select("id").limit(1).execute()
        results["anon"]["status"] = "healthy"
    except Exception as e:
        results["anon"]["status"] = "unhealthy"
        results["anon"]["error"] = str(e)
        logger.error(f"Supabase anon health check failed: {e}")
    
    # Check admin client
    try:
        client = await get_supabase_admin()
        # Simple query to test connection
        await client.auth.admin.list_users()
        results["admin"]["status"] = "healthy"
    except Exception as e:
        results["admin"]["status"] = "unhealthy"
        results["admin"]["error"] = str(e)
        logger.error(f"Supabase admin health check failed: {e}")
    
    return results


async def close_supabase_clients() -> None:
    """Close Supabase client connections."""
    global _supabase_anon, _supabase_admin
    
    # Supabase Python client doesn't have explicit close for async
    # Just clear references
    _supabase_anon = None
    _supabase_admin = None
    logger.info("Supabase clients cleared")


# Synchronous versions for compatibility
@lru_cache(maxsize=1)
def get_supabase_sync() -> Client:
    """Get synchronous Supabase client with anon key."""
    if not settings.SUPABASE_URL or not settings.SUPABASE_ANON_KEY:
        raise RuntimeError("SUPABASE_URL and SUPABASE_ANON_KEY must be configured")
    
    return create_client(
        supabase_url=settings.SUPABASE_URL,
        supabase_key=settings.SUPABASE_ANON_KEY,
        options=_get_client_options(),
    )


@lru_cache(maxsize=1)
def get_supabase_admin_sync() -> Client:
    """Get synchronous Supabase client with service role key."""
    if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_ROLE_KEY:
        raise RuntimeError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be configured")
    
    return create_client(
        supabase_url=settings.SUPABASE_URL,
        supabase_key=settings.SUPABASE_SERVICE_ROLE_KEY,
        options=_get_client_options(),
    )