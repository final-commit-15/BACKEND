from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from ...db.session import get_db
from ...services.agent_service import AgentService
from ...middleware.auth import get_current_user_id
from ...schemas.agent import AgentCreate, AgentOut, AgentUpdate
from ...utils.exceptions import NotFoundError, PermissionDeniedError

router = APIRouter(prefix="/agents", tags=["agents"])

@router.post("/", response_model=AgentOut, status_code=status.HTTP_201_CREATED)
async def create_agent(
    data: AgentCreate,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    return await AgentService.create(db, data, current_user_id)

@router.get("/", response_model=List[AgentOut])
async def list_agents(
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    return await AgentService.list_by_owner(db, current_user_id)

@router.get("/{agent_id}", response_model=AgentOut)
async def get_agent(agent_id: str, db: AsyncSession = Depends(get_db)):
    agent = await AgentService.get_by_id(db, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent

@router.patch("/{agent_id}", response_model=AgentOut)
async def update_agent(agent_id: str, data: AgentUpdate, db: AsyncSession = Depends(get_db)):
    return await AgentService.update(db, agent_id, data)

@router.delete("/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_agent(agent_id: str, db: AsyncSession = Depends(get_db)):
    deleted = await AgentService.delete(db, agent_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Agent not found")

@router.post("/{agent_id}/clone", response_model=AgentOut)
async def clone_agent(
    agent_id: str,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    return await AgentService.clone(db, agent_id, current_user_id)

@router.post("/{agent_id}/enable", response_model=AgentOut)
async def enable_agent(agent_id: str, db: AsyncSession = Depends(get_db)):
    return await AgentService.set_active(db, agent_id, True)

@router.post("/{agent_id}/disable", response_model=AgentOut)
async def disable_agent(agent_id: str, db: AsyncSession = Depends(get_db)):
    return await AgentService.set_active(db, agent_id, False)