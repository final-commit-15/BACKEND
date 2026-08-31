from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from ...db.session import get_db
from ...services.execution_service import ExecutionService
from ...middleware.auth import get_current_user_id
from ...schemas.execution import ExecutionStart, ExecutionOut
from ...websocket.manager import ws_manager
from ...utils.exceptions import NotFoundError, PermissionDeniedError

router = APIRouter(tags=["executions"])

@router.post("/", response_model=ExecutionOut)
async def start_execution(
    data: ExecutionStart,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    try:
        return await ExecutionService.start(
            db,
            str(data.agent_id),
            str(data.task_id) if data.task_id else None,
            data.input,
            current_user_id
        )
    except NotFoundError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e)
        )
    except PermissionDeniedError as e:
        raise HTTPException(
            status_code=403,
            detail=str(e)
        )

from typing import Optional

@router.get("/", response_model=list[ExecutionOut])
async def list_executions(
    limit: int = 10,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    return await ExecutionService.list_by_user(
        db=db,
        user_id=current_user_id,
        limit=limit,
    )

@router.get("/{execution_id}", response_model=ExecutionOut)
async def get_execution(execution_id: str, db: AsyncSession = Depends(get_db)):
    exec = await ExecutionService.get_by_id(db, execution_id)
    if not exec:
        raise HTTPException(status_code=404, detail="Execution not found")
    return exec

@router.websocket("/ws/{execution_id}")
async def websocket_endpoint(websocket: WebSocket, execution_id: str):
    # Authenticate the WebSocket connection
    user_info = await ws_manager.authenticate_websocket(websocket)
    if not user_info:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    
    # Authorize access to this execution
    authorized = await ws_manager.authorize_execution_access(user_info["user_id"], execution_id)
    if not authorized:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    
    await ws_manager.connect(execution_id, websocket, user_info)
    try:
        while True:
            await websocket.receive_text()  # keep alive
    except WebSocketDisconnect:
        ws_manager.disconnect(execution_id, websocket)