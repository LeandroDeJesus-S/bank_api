from http import HTTPStatus
from typing import List

from databases.interfaces import Record
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy import select, or_

from .schemas import UserInSchema, UserOutSchema, UserUpSchema
from .controllers import UserController
from core.exceptions import ValidationException

router = APIRouter(prefix="/users", tags=["users"])


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
    try:
        all_users = await ctrl.all(limit, offset)
        return all_users

    except ValidationException as e:
        raise HTTPException(status_code=e.code, detail=e.detail)


@router.get(
    "/{id}",
    response_model=UserOutSchema,
    summary="Retorna o usuário com respectivo id na base dados.",
)
async def get_user(id: int, ctrl: UserController = Depends(UserController)):
    try:
        user = await ctrl.get(where_field="id", equals_to=id)
        if user is None:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND, detail="Usuário não encontrado."
            )

        return UserOutSchema.model_validate(user)

    except ValidationException as e:
        raise HTTPException(e.code, e.detail)


@router.post(
    "/",
    summary="Adiciona um novo usuário no banco de dados.",
    status_code=HTTPStatus.CREATED,
)
async def create_user(
    user_data: UserInSchema, ctrl: UserController = Depends(UserController)
) -> UserOutSchema:
    try:
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

    except ValidationException as e:
        raise HTTPException(e.code, e.detail)


@router.patch(
    "/{id}",
    response_model=UserOutSchema,
    summary="Atualiza dados do usuário.",
)
async def update_user(
    id: int, user_data: UserUpSchema, ctrl: UserController = Depends(UserController)
):
    try:
        data = user_data.model_dump(exclude_unset=True)
        if not data:
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST, detail="Invalid data."
            )

        updated = await ctrl.update_(id, **data)
        if updated:
            updated_user = await ctrl.get(where_field="id", equals_to=id)
            output = UserOutSchema.model_validate(updated_user)
            return output

        raise HTTPException(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
            detail="Não foi possivél atualizar, verifique e tente novamente.",
        )

    except ValidationException as e:
        raise HTTPException(e.code, e.detail)


@router.delete(
    "/{id}",
    status_code=HTTPStatus.NO_CONTENT,
    summary="Deleta um usuário do banco de dados.",
)
async def delete_user(id: int, ctrl: UserController = Depends(UserController)):
    try:
        await ctrl.delete_(id)

    except ValidationException as e:
        raise HTTPException(status_code=e.code, detail=e.detail)
