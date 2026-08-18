from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from ...db.session import get_db
from ...services.integration_service import IntegrationService
from ...middleware.auth import get_current_user_id
from ...schemas.integration import IntegrationCreate, IntegrationOut

router = APIRouter(prefix="/integrations", tags=["integrations"])

@router.post("/", response_model=IntegrationOut, status_code=status.HTTP_201_CREATED)
async def connect_integration(
    data: IntegrationCreate,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    return await IntegrationService.connect(db, data, current_user_id)

@router.get("/", response_model=List[IntegrationOut])
async def list_integrations(
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    return await IntegrationService.list_by_user(db, current_user_id)

@router.delete("/{integration_id}", status_code=status.HTTP_204_NO_CONTENT)
async def disconnect_integration(
    integration_id: str,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    await IntegrationService.disconnect(db, integration_id, current_user_id)