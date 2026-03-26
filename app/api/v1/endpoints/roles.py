from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.db.session import get_db
from app.models.user import User, Role, Permission
from app.schemas.schemas import RoleCreate, RoleOut, AssignRole, PermissionOut
from app.core.security import get_current_user, require_permission

router = APIRouter(tags=["Roles & Users"])


@router.post("/roles/create", response_model=RoleOut, status_code=201)
def create_role(
    payload: RoleCreate,
    db: Session = Depends(get_db),
    _=Depends(require_permission("full_access")),
):
    if db.query(Role).filter(Role.name == payload.name).first():
        raise HTTPException(status_code=400, detail="Role already exists")

    role = Role(name=payload.name, description=payload.description)
    db.add(role)
    db.flush()

    for perm_name in payload.permissions or []:
        perm = db.query(Permission).filter(Permission.name == perm_name).first()
        if not perm:
            perm = Permission(name=perm_name, description=perm_name.replace("_", " ").title())
            db.add(perm)
            db.flush()
        if perm not in role.permissions:
            role.permissions.append(perm)

    db.commit()
    db.refresh(role)
    return role


@router.post("/users/assign-role")
def assign_role(
    payload: AssignRole,
    db: Session = Depends(get_db),
    _=Depends(require_permission("full_access")),
):
    user = db.query(User).filter(User.id == payload.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    role = db.query(Role).filter(Role.name == payload.role_name).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    if role not in user.roles:
        user.roles.append(role)
        db.commit()
    return {"message": f"Role '{role.name}' assigned to '{user.username}'"}


@router.get("/users/{user_id}/roles", response_model=List[RoleOut])
def get_user_roles(
    user_id: int,
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user.roles


@router.get("/users/{user_id}/permissions", response_model=List[PermissionOut])
def get_user_permissions(
    user_id: int,
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    perms = {p for role in user.roles for p in role.permissions}
    return list(perms)
