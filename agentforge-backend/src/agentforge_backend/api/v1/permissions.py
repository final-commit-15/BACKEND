from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import List, Optional
from uuid import UUID

from ..deps import get_current_user, get_db, require_permission
from ...models.user import User
from ...services.permissions import PermissionsService

router = APIRouter()

class PermissionOut(BaseModel):
    id: UUID
    name: str
    description: Optional[str]

class RoleBase(BaseModel):
    name: str
    description: Optional[str] = None

class RoleCreate(RoleBase):
    permissions: List[UUID] = []

class RoleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    permissions: Optional[List[UUID]] = None

class RoleOut(RoleBase):
    id: UUID
    permissions: List[PermissionOut]

@router.get("/", response_model=List[PermissionOut])
async def list_permissions(
    current_user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    service = PermissionsService(db)
    perms = await service.get_all_permissions()
    return [PermissionOut(**p) for p in perms]

@router.get("/roles", response_model=List[RoleOut])
async def list_roles(
    current_user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    service = PermissionsService(db)
    roles = await service.get_all_roles()
    return [RoleOut(**r) for r in roles]

@router.post("/roles", response_model=RoleOut, status_code=201)
async def create_role(
    role_in: RoleCreate,
    current_user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    # Add permission check: only admin/owner
    await require_permission(current_user, "roles:write")
    service = PermissionsService(db)
    role = await service.create_role(role_in.dict())
    return RoleOut(**role)

@router.put("/roles/{role_id}", response_model=RoleOut)
async def update_role(
    role_id: UUID,
    role_in: RoleUpdate,
    current_user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    await require_permission(current_user, "roles:write")
    service = PermissionsService(db)
    updated = await service.update_role(role_id, role_in.dict(exclude_unset=True))
    if not updated:
        raise HTTPException(status_code=404, detail="Role not found")
    return RoleOut(**updated)