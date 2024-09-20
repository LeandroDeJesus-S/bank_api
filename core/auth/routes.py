from http import HTTPStatus
from typing import Annotated, List

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import and_, select

from core.users.controllers import UserController

from .controllers import (
    JWTController,
    PasswordController,
    RoleController,
    UserRoleController,
)
from .schemas import (
    AddRoleSchema,
    AuthSchema,
    JWTPayload,
    RoleInSchema,
    RoleOutSchema,
    TokenSchema,
)

router = APIRouter(prefix="/auth", tags=["auth"])
jwt_ctrl = JWTController()
bearer = HTTPBearer()


@router.post(
    "/login",
    summary="Realiza a autenticação do usuário.",
    description="Verifica as credenciais e retorna o token de autenticação caso sejam validas.",
    response_model=TokenSchema,
)
async def authenticate(
    auth_data: AuthSchema,
    pw_ctrl: PasswordController = Depends(PasswordController),
    usr_ctrl: UserController = Depends(UserController),
    jwt_ctrl: JWTController = Depends(JWTController),
    usr_role_ctrl: UserRoleController = Depends(UserRoleController),
    role_ctrl: RoleController = Depends(RoleController),
):
    """authenticate the user.

    Args:
        auth_data (AuthSchema): the user data necessary to authenticate.
        pw_ctrl (PasswordController, optional): the password controller. Defaults to Depends(PasswordController).
        usr_ctrl (UserController, optional): the user controller. Defaults to Depends(UserController).
        jwt_ctrl (JWTController, optional): the jwt controller. Defaults to Depends(JWTController).
        usr_role_ctrl (UserRoleController, optional): the user role controller. Defaults to Depends(UserRoleController).
        role_ctrl (RoleController, optional): the role controller. Defaults to Depends(RoleController).

    Raises:
        HTTPException: the sent credentials does not matches

    Returns:
        TokenSchema: the generated token schema.
    """
    base_exc = HTTPException(
        status_code=HTTPStatus.UNAUTHORIZED, detail="Invalid credentials."
    )

    user = await usr_ctrl.get("username", auth_data.username)
    if user is None:
        raise base_exc

    chk = pw_ctrl.check_password(auth_data.password, user.password)  # type: ignore
    if not chk:
        raise base_exc

    stmt = select(usr_role_ctrl.model.role_id).where(
        usr_role_ctrl.model.user_id == user._mapping["id"]
    )
    user_role_ids = [r.role_id for r in await usr_role_ctrl.query(stmt)]  # type: ignore

    stmt = select(role_ctrl.model.name).where(role_ctrl.model.id.in_(user_role_ids))
    role_names = [r.name for r in await role_ctrl.query(stmt)]  # type: ignore
    role_names.append('none')

    payload = JWTPayload(sub=user._mapping["username"], aud=role_names, iss='bank')
    token = jwt_ctrl.generate_token(payload.model_dump())
    return TokenSchema(access_token=token)


@router.get(
    "/roles",
    response_model=List[RoleOutSchema],
    summary="Lista todas as roles disponíveis.",
    description="Retorna todas as roles do banco de dados."
)
async def list_roles(
    limit: int = RoleController.DEFAULT_LIMIT,
    offset: int = RoleController.DEFAULT_OFFSET,
    ctrl: RoleController = Depends(RoleController),
):
    """list all roles.

    Args:
        limit (int, optional): the limit of roles. Defaults to RoleController.DEFAULT_LIMIT.
        offset (int, optional): the offset to apply. Defaults to RoleController.DEFAULT_OFFSET.
        ctrl (RoleController, optional): the role controller. Defaults to Depends(RoleController).

    Returns:
        List[RoleOutSchema]: the list of roles from database
    """
    roles = await ctrl.all(limit, offset)
    return roles


@router.post(
    "/roles",
    response_model_exclude_unset=True,
    status_code=HTTPStatus.CREATED,
    summary="Cria uma nova permissão.",
    description="somente usuários que possuem a role `admin` podem criar uma role.",
)
async def create_role(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer)],
    role_data: RoleInSchema,
    ctrl: RoleController = Depends(RoleController),
):
    """creates a new role in database.

    Args:
        credentials (Annotated[HTTPAuthorizationCredentials, Depends): the authorization header value
        role_data (RoleInSchema): the data to create the new role.
        ctrl (RoleController, optional): the role controller instance.. Defaults to Depends(RoleController).

    Raises:
        HTTPException: role already exists.
    """
    jwt_ctrl.validate_token(credentials, required_roles="admin")

    if await ctrl.get("name", role_data.name):
        raise HTTPException(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY, detail="Role already exists."
        )
    await ctrl.create(**role_data.model_dump())


@router.post(
    "/user-roles",
    response_model_exclude_unset=True,
    summary="Adiciona um role para um usuário.",
    description="Somente usuário com a role `admin` podem atribuir uma role para um usuário.",
    status_code=HTTPStatus.CREATED,
)
async def add_user_role(
    role_data: AddRoleSchema,
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer)],
    ctrl: UserRoleController = Depends(UserRoleController),
):
    """set a role to an user. Must have `admin` role to set.

    Args:
        role_data (AddRoleSchema): the user id and the role id to apply.
        credentials (Annotated[HTTPAuthorizationCredentials, Depends): the authorization header value.
        ctrl (UserRoleController, optional): the user role controller instance. Defaults to Depends(UserRoleController).

    Raises:
        HTTPException: the user already have the role.
    """
    jwt_ctrl.validate_token(credentials, required_roles="admin")
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
