from http import HTTPStatus
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, and_

from .schemas import AuthSchema, RoleInSchema, RoleOutSchema, AddRoleSchema
from .controllers import RoleController, UserRoleController

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/token")
def authenticate(auth_data: AuthSchema): ...


@router.get(
    "/roles",
    response_model=List[RoleOutSchema],
    summary="Lista todas as permissões disponíveis.",
)
async def list_roles(
    limit: int = RoleController.DEFAULT_LIMIT,
    offset: int = RoleController.DEFAULT_OFFSET,
    ctrl: RoleController = Depends(RoleController),
):
    roles = await ctrl.all(limit, offset)
    return roles


@router.post(
    "/roles",
    response_model_exclude_unset=True,
    status_code=HTTPStatus.CREATED,
    summary="Cria uma nova permissão.",
)
async def create_role(
    role_data: RoleInSchema, ctrl: RoleController = Depends(RoleController)
):
    if await ctrl.get("name", role_data.name):
        raise HTTPException(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY, detail="Role already exists."
        )
    await ctrl.create(**role_data.model_dump())


@router.post(
    "/user-roles",
    response_model_exclude_unset=True,
    summary="Adiciona um role para um usuário.",
    status_code=HTTPStatus.CREATED,
)
async def add_user_role(
    role_data: AddRoleSchema,
    ctrl: UserRoleController = Depends(UserRoleController)
):
    stmt = select(ctrl.model).where(
        and_(
            ctrl.model.user_id == role_data.user_id,
            ctrl.model.role_id == role_data.role_id,
        )
    )
    if await ctrl.query(stmt):
        raise HTTPException(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
            detail="The user already have this role.",
        )

    await ctrl.create(**role_data.model_dump())
