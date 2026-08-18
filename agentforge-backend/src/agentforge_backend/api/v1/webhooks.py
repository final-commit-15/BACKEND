from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from ...db.session import get_db
from ...services.webhook_service import WebhookService
from ...middleware.auth import get_current_user_id
from ...schemas.webhook import WebhookCreate, WebhookOut

router = APIRouter(prefix="/webhooks", tags=["webhooks"])

@router.post("/", response_model=WebhookOut, status_code=status.HTTP_201_CREATED)
async def create_webhook(
    data: WebhookCreate,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    return await WebhookService.create(db, data, current_user_id)

@router.get("/", response_model=List[WebhookOut])
async def list_webhooks(
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    return await WebhookService.list_by_user(db, current_user_id)

@router.delete("/{webhook_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_webhook(
    webhook_id: str,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    await WebhookService.delete(db, webhook_id, current_user_id)