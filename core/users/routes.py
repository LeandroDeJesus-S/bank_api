from http import HTTPStatus
from typing import Annotated, List

from databases.interfaces import Record
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import or_, select

from core.auth.controllers import JWTController, PasswordController

from .controllers import UserController
from .schemas import UserInSchema, UserOutSchema, UserUpSchema

router = APIRouter(prefix="/users", tags=["users"])
bearer = HTTPBearer()
jwt_ctrl = JWTController()


@router.get(
    "/",
    response_model=List[UserOutSchema],
    summary="Retorna todos os usuários existentes.",
)
async def list_users(
    limit: int = UserController.DEFAULT_LIMIT,
    offset: int = UserController.DEFAULT_OFFSET,
    ctrl: UserController = Depends(UserController),
) -> List[Record]:
    all_users = await ctrl.all(limit, offset)
    return all_users


@router.get(
    "/{id}",
    response_model=UserOutSchema,
    summary="Retorna o usuário com respectivo id na base dados.",
)
async def get_user(id: int, ctrl: UserController = Depends(UserController)):
    user = await ctrl.get(where_field="id", equals_to=id)
    if user is None:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="Usuário não encontrado."
        )

    return UserOutSchema.model_validate(user)


@router.post(
    "/",
    summary="Adiciona um novo usuário no banco de dados.",
    status_code=HTTPStatus.CREATED,
    response_model=UserOutSchema,
)
async def create_user(
    user_data: UserInSchema,
    ctrl: UserController = Depends(UserController),
    pw_ctrl: PasswordController = Depends(PasswordController),
):
    q = select(ctrl._model).where(
        or_(
            ctrl._model.cpf == user_data.cpf,
            ctrl._model.username == user_data.username,
        )
    )
    duplicated = await ctrl.query(q)
    if duplicated:
        raise HTTPException(
            HTTPStatus.UNPROCESSABLE_ENTITY,
            detail="Nome de usuário ou cpf não disponível.",
        )

    await ctrl.create(**user_data.model_dump())
    created_user = await ctrl.get(where_field="cpf", equals_to=user_data.cpf)
    output = UserOutSchema.model_validate(created_user)
    return output


@router.patch(
    "/{id}",
    response_model=UserOutSchema,
    summary="Atualiza dados do usuário.",
)
async def update_user(
    id: int,
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer)],
    user_data: UserUpSchema,
    ctrl: UserController = Depends(UserController),
):
    data = user_data.model_dump(exclude_unset=True)

    if not data:
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail="Invalid data.")

    user = await ctrl.get("id", id)
    username = jwt_ctrl.validate_token(credentials)

    if user is None or username != user._mapping["username"]:
        raise HTTPException(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
            detail="Invalid user id.",
        )

    updated = await ctrl.update_(id, **data)
    if updated:
        updated_user = await ctrl.get(where_field="id", equals_to=id)
        output = UserOutSchema.model_validate(updated_user)
        return output

    raise HTTPException(
        status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
        detail="Fail on update, please verify and try again.",
    )


@router.delete(
    "/{id}",
    status_code=HTTPStatus.NO_CONTENT,
    summary="Deleta um usuário do banco de dados.",
)
async def delete_user(
    id: int,
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer)],
    ctrl: UserController = Depends(UserController),
):
    user = await ctrl.get("id", id)
    username = jwt_ctrl.validate_token(credentials)

    if user is None or username != user._mapping["username"]:
        raise HTTPException(
            status_code=HTTPStatus.NO_CONTENT,
        )

    await ctrl.delete_(id)
