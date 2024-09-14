from http import HTTPStatus
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select

from core.exceptions import ValidationException
from core.users.controllers import UserController

from . import schemas
from .controllers import AccountController, AccountTypeController

router = APIRouter(prefix="/accounts", tags=["accounts"])


@router.post(
    "/types",
    response_model=schemas.AccountTypeOutSchema,
    summary="Cria um novo tipo de conta.",
    status_code=HTTPStatus.CREATED,
    response_model_exclude_unset=True,
)
async def create_account_type(
    acc_type_data: schemas.AccountTypeInSchema,
    ctrl: AccountTypeController = Depends(AccountTypeController),
):
    data = acc_type_data.model_dump()
    try:
        if await ctrl.get("type", acc_type_data.type):
            raise HTTPException(
                status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
                detail="account type already exists.",
            )

        await ctrl.create(**data)
        created = await ctrl.get("type", acc_type_data.type)
        return created

    except ValidationException as e:
        raise HTTPException(status_code=e.code, detail=e.detail)


@router.get("/types", response_model=List[schemas.AccountTypeOutSchema], summary='Lista todos os tipos de conta disponiveis.')
async def list_account_types(
    limit: int = 100,
    offset: int = 0,
    ctrl: AccountTypeController = Depends(AccountTypeController),
):
    try:
        stmt = select(ctrl.model).limit(limit).offset(offset)
        account_types = await ctrl.query(stmt)
        return account_types

    except ValidationException as e:
        raise HTTPException(status_code=e.code, detail=e.detail)


@router.post(
    "/",
    response_model=schemas.AccountOutSchema,
    response_model_exclude_unset=True,
    status_code=HTTPStatus.CREATED,
    summary="Cria uma nova conta.",
)
async def create_account(
    account_data: schemas.AccountInSchema,
    account_ctrl: AccountController = Depends(AccountController),
    account_type_ctrl: AccountTypeController = Depends(AccountTypeController),
    user_ctrl: UserController = Depends(UserController),
):
    data = account_data.model_dump()
    try:
        user = await user_ctrl.get("id", account_data.user_id)
        if not user:
            raise HTTPException(
                status_code=HTTPStatus.UNPROCESSABLE_ENTITY, detail="invalid user id"
            )

        acc_type = await account_type_ctrl.get("id", account_data.account_type_id)
        if not acc_type:
            raise HTTPException(
                status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
                detail="invalid account type id",
            )

        number_exists = await account_ctrl.get("number", account_data.number)
        if number_exists:
            raise HTTPException(
                status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
                detail="account number already exists.",
            )

        await account_ctrl.create(**data)
        account = await account_ctrl.get("number", account_data.number)
        return account

    except ValidationException as e:
        raise HTTPException(status_code=e.code, detail=e.detail)


@router.get(
    "/{id}",
    response_model=schemas.AccountOutSchema,
    summary="Retorna a conta com o id passado.",
)
async def get_account(id: int, ctrl: AccountController = Depends(AccountController)):
    try:
        account = await ctrl.get("id", id)
        if account is None:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND, detail="account not found"
            )
        return account

    except ValidationException as e:
        raise HTTPException(status_code=e.code, detail=e.detail)


@router.get("/", response_model=List[schemas.AccountOutSchema], summary='Lista todos as contas existentes.')
async def list_accounts(
    limit: int = 100,
    offset: int = 0,
    ctrl: AccountController = Depends(AccountController),
):
    try:
        stmt = select(ctrl.model).limit(limit).offset(offset)
        accounts = await ctrl.query(stmt)
        return accounts

    except ValidationException as e:
        raise HTTPException(status_code=e.code, detail=e.detail)
