from ..models.user import UserRole

ROLE_PERMISSIONS = {
    UserRole.ADMIN: ["*"],
    UserRole.DEVELOPER: ["create:agent", "update:agent", "delete:agent", "execute:agent"],
    UserRole.OPERATOR: ["execute:agent", "view:agent"],
    UserRole.USER: ["view:agent", "view:project"],
    UserRole.VIEWER: ["view:agent"],
}

def user_has_permission(user_role: UserRole, required_permission: str) -> bool:
    perms = ROLE_PERMISSIONS.get(user_role, [])
    return "*" in perms or required_permission in perms