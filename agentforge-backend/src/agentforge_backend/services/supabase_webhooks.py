"""
Supabase Webhooks Handler

Handles incoming webhooks from Supabase for:
- user.created
- user.deleted
- user.updated
- storage.object.created
- storage.object.deleted
- storage.object.updated
"""
import logging
import hmac
import hashlib
import json
from typing import Dict, Any, Optional, Callable
from fastapi import Request, HTTPException, Header

from ..config.settings import settings
from ..services.supabase_auth import get_supabase_auth_service
from ..services.supabase_storage import get_storage_service
from ..db.session import async_session
from ..models.user import User
from sqlalchemy import select
from uuid import UUID

logger = logging.getLogger(__name__)


class SupabaseWebhookHandler:
    """Handles Supabase webhook events."""
    
    def __init__(self):
        self._handlers: Dict[str, Callable] = {}
        self._register_default_handlers()
    
    def _register_default_handlers(self):
        """Register default event handlers."""
        self.register("user.created", self._handle_user_created)
        self.register("user.deleted", self._handle_user_deleted)
        self.register("user.updated", self._handle_user_updated)
        self.register("storage.object.created", self._handle_storage_created)
        self.register("storage.object.deleted", self._handle_storage_deleted)
        self.register("storage.object.updated", self._handle_storage_updated)
    
    def register(self, event_type: str, handler: Callable):
        """Register a handler for an event type."""
        self._handlers[event_type] = handler
        logger.info(f"Registered webhook handler for: {event_type}")
    
    async def handle(self, event_type: str, payload: Dict[str, Any]) -> bool:
        """
        Handle a webhook event.
        
        Args:
            event_type: The event type (e.g., "user.created")
            payload: The webhook payload
            
        Returns:
            True if handled successfully
        """
        handler = self._handlers.get(event_type)
        if not handler:
            logger.warning(f"No handler for event type: {event_type}")
            return False
        
        try:
            await handler(payload)
            return True
        except Exception as e:
            logger.error(f"Error handling {event_type}: {e}")
            return False
    
    # ==================== User Event Handlers ====================
    
    async def _handle_user_created(self, payload: Dict[str, Any]):
        """Handle user.created event - sync user to local DB."""
        user_data = payload.get("user", {})
        user_id = user_data.get("id")
        email = user_data.get("email")
        
        if not user_id or not email:
            logger.warning("User created event missing required fields")
            return
        
        async with async_session() as db:
            # Check if user already exists locally
            result = await db.execute(select(User).where(User.id == UUID(user_id)))
            existing = result.scalar_one_or_none()
            
            if existing:
                logger.info(f"User {user_id} already exists locally, updating")
                existing.email = email
                existing.is_verified = user_data.get("email_confirmed_at") is not None
                await db.commit()
            else:
                # Create local user record
                user = User(
                    id=UUID(user_id),
                    email=email,
                    username=user_data.get("user_metadata", {}).get("username", email.split("@")[0]),
                    hashed_password="",  # Managed by Supabase
                    full_name=user_data.get("user_metadata", {}).get("full_name", email),
                    is_verified=user_data.get("email_confirmed_at") is not None,
                )
                db.add(user)
                await db.commit()
                logger.info(f"Created local user record for {user_id}")
    
    async def _handle_user_deleted(self, payload: Dict[str, Any]):
        """Handle user.deleted event - soft delete local user."""
        user_id = payload.get("user", {}).get("id")
        
        if not user_id:
            logger.warning("User deleted event missing user ID")
            return
        
        async with async_session() as db:
            result = await db.execute(select(User).where(User.id == UUID(user_id)))
            user = result.scalar_one_or_none()
            
            if user:
                user.is_active = False
                user.deleted_at = datetime.utcnow()
                await db.commit()
                logger.info(f"Soft deleted local user {user_id}")
            else:
                logger.warning(f"Local user {user_id} not found for deletion")
    
    async def _handle_user_updated(self, payload: Dict[str, Any]):
        """Handle user.updated event - sync user data."""
        user_data = payload.get("user", {})
        user_id = user_data.get("id")
        
        if not user_id:
            return
        
        async with async_session() as db:
            result = await db.execute(select(User).where(User.id == UUID(user_id)))
            user = result.scalar_one_or_none()
            
            if user:
                user.email = user_data.get("email", user.email)
                user.is_verified = user_data.get("email_confirmed_at") is not None
                
                # Update metadata fields
                metadata = user_data.get("user_metadata", {})
                if "full_name" in metadata:
                    user.full_name = metadata["full_name"]
                if "username" in metadata:
                    user.username = metadata["username"]
                
                await db.commit()
                logger.info(f"Updated local user {user_id}")
    
    # ==================== Storage Event Handlers ====================
    
    async def _handle_storage_created(self, payload: Dict[str, Any]):
        """Handle storage.object.created event."""
        record = payload.get("record", {})
        bucket_id = record.get("bucket_id")
        object_id = record.get("id")
        name = record.get("name")
        
        logger.info(f"Storage object created: {bucket_id}/{object_id} ({name})")
        # Could update local file records, trigger processing, etc.
    
    async def _handle_storage_deleted(self, payload: Dict[str, Any]):
        """Handle storage.object.deleted event."""
        record = payload.get("record", {})
        object_id = record.get("id")
        
        logger.info(f"Storage object deleted: {object_id}")
        # Could clean up local references
    
    async def _handle_storage_updated(self, payload: Dict[str, Any]):
        """Handle storage.object.updated event."""
        record = payload.get("record", {})
        object_id = record.get("id")
        
        logger.info(f"Storage object updated: {object_id}")
        # Could update local metadata


# Global handler instance
_webhook_handler: Optional[SupabaseWebhookHandler] = None


def get_webhook_handler() -> SupabaseWebhookHandler:
    """Get the webhook handler instance."""
    global _webhook_handler
    if _webhook_handler is None:
        _webhook_handler = SupabaseWebhookHandler()
    return _webhook_handler


async def verify_webhook_signature(
    request: Request,
    signature: str = Header(None, alias="x-supabase-signature"),
) -> bool:
    """
    Verify Supabase webhook signature.
    
    Supabase signs webhooks with HMAC-SHA256 using the webhook secret.
    """
    if not settings.SUPABASE_WEBHOOK_SECRET:
        logger.warning("SUPABASE_WEBHOOK_SECRET not configured, skipping verification")
        return True
    
    if not signature:
        raise HTTPException(status_code=401, detail="Missing signature header")
    
    body = await request.body()
    
    expected_signature = hmac.new(
        settings.SUPABASE_WEBHOOK_SECRET.encode(),
        body,
        hashlib.sha256,
    ).hexdigest()
    
    if not hmac.compare_digest(signature, expected_signature):
        logger.warning("Invalid webhook signature")
        raise HTTPException(status_code=401, detail="Invalid signature")
    
    return True


async def handle_supabase_webhook(
    request: Request,
    event_type: str,
    payload: Dict[str, Any],
    signature: str = Header(None, alias="x-supabase-signature"),
) -> Dict[str, Any]:
    """
    Main webhook endpoint handler.
    
    Args:
        request: FastAPI request
        event_type: Event type from path or header
        payload: Webhook payload
        signature: Webhook signature for verification
        
    Returns:
        Response dict
    """
    # Verify signature
    await verify_webhook_signature(request, signature)
    
    # Get event type from header if not in path
    if not event_type:
        event_type = request.headers.get("x-supabase-event", "unknown")
    
    logger.info(f"Received webhook: {event_type}")
    
    # Handle event
    handler = get_webhook_handler()
    success = await handler.handle(event_type, payload)
    
    if success:
        return {"status": "ok", "event": event_type}
    else:
        return {"status": "unhandled", "event": event_type}


# Import datetime for user deleted handler
from datetime import datetime