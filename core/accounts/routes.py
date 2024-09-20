from http import HTTPStatus
from typing import Annotated, List

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select

from core.auth.controllers import JWTController
from core.exceptions import JWTException
from core.users.controllers import UserController

from . import schemas
from .controllers import AccountController, AccountTypeController

router = APIRouter(prefix="/accounts", tags=["accounts"])
jwt_ctrl = JWTController()
bearer = HTTPBearer()


@router.post(
    "/types",
    response_model=schemas.AccountTypeOutSchema,
    summary="Cria um novo tipo de conta.",
    description="Cria um novo tipo de conta. O usuário precisa estar autenticado e ter a role `admin`.",
    status_code=HTTPStatus.CREATED,
    response_model_exclude_unset=True,
)
async def create_account_type(
    acc_type_data: schemas.AccountTypeInSchema,
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer)],
    ctrl: AccountTypeController = Depends(AccountTypeController),
):
    """Creates a new account type.
    The user must be authenticated and to have `admin` role.

    Args:
        acc_type_data (schemas.AccountTypeInSchema): the necessary data to create the account type.
        credentials (Annotated[HTTPAuthorizationCredentials, Depends): the authorization header value.
        ctrl (AccountTypeController, optional): the controller that manages the account types. Defaults to Depends(AccountTypeController).

    Raises:
        HTTPException: if the account type already exists.

    Returns:
        AccountTypeOutSchema: the new account type created.
    """
    jwt_ctrl.validate_token(credentials, required_roles="admin")

    data = acc_type_data.model_dump()
    if await ctrl.get("type", acc_type_data.type):
        raise HTTPException(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
            detail="account type already exists.",
        )

    await ctrl.create(**data)
    created = await ctrl.get("type", acc_type_data.type)
    return created


@router.get(
    "/types",
    response_model=List[schemas.AccountTypeOutSchema],
    summary="Lista todos os tipos de conta disponíveis.",
    description="Lista todas os tipos de conta presentes no banco de dados.",
)
async def list_account_types(
    limit: int = 100,
    offset: int = 0,
    ctrl: AccountTypeController = Depends(AccountTypeController),
):
    """list all account types available. Is not necessary to be authenticated.

    Args:
        limit (int, optional): the limit of account types to show. Defaults to 100.
        offset (int, optional): the offset to apply. Defaults to 0.
        ctrl (AccountTypeController, optional): the instance of the account type controller. Defaults to Depends(AccountTypeController).

    Returns:
        List[AccountTypeOutSchema]: the list of account types.
    """
    stmt = select(ctrl.model).limit(limit).offset(offset)
    account_types = await ctrl.query(stmt)
    return account_types


@router.post(
    "/",
    response_model=schemas.AccountOutSchema,
    response_model_exclude_unset=True,
    status_code=HTTPStatus.CREATED,
    summary="Cria uma nova conta para o usuário.",
    description="O usuário precisa estar autenticado e só pode criar uma nova conta para sí mesmo",
)
async def create_account(
    account_data: schemas.AccountInSchema,
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer)],
    account_ctrl: AccountController = Depends(AccountController),
    account_type_ctrl: AccountTypeController = Depends(AccountTypeController),
    user_ctrl: UserController = Depends(UserController),
):
    """create a new user's account.

    Args:
        account_data (schemas.AccountInSchema): the necessary data to create the account
        credentials (Annotated[HTTPAuthorizationCredentials, Depends): the authorization header value.
        account_ctrl (AccountController, optional): the controller of the accounts. Defaults to Depends(AccountController).
        account_type_ctrl (AccountTypeController, optional): the controller of the account types. Defaults to Depends(AccountTypeController).
        user_ctrl (UserController, optional): the controller of the users. Defaults to Depends(UserController).

    Raises:
        HTTPException: if the sent user id doest not exists
        HTTPException: if the user id of the account does not match with the authenticated user
        HTTPException: if the account type id does not exists
        HTTPException: account number already exists

    Returns:
        AccountOutSchema: the account created.
    """
    data = account_data.model_dump()
    user = await user_ctrl.get("id", account_data.user_id)
    if not user:
        raise HTTPException(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY, detail="invalid user id"
        )

    username = jwt_ctrl.validate_token(credentials)
    if username != user._mapping["username"]:
        raise HTTPException(
            status_code=HTTPStatus.FORBIDDEN,
            detail="You can only to create an account to yourself.",
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


@router.get(
    "/{id}",
    response_model=schemas.AccountOutSchema,
    summary="Retorna a conta com o id passado.",
    description="Usuários que possuem a role `admin` podem solicitar qualquer conta, \
        caso não tenha o usuário autenticado só pode solicitar a própria conta.",
)
async def get_account(
    id: int,
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer)],
    ctrl: AccountController = Depends(AccountController),
    usr_ctrl: UserController = Depends(UserController),
):
    """return the account with the given id. Users that have the role `admin` can
    get any account, otherwise the authenticated user can only get the account of himself.

    Args:
        id (int): the account id
        credentials (Annotated[HTTPAuthorizationCredentials, Depends): authorization header value.
        ctrl (AccountController, optional): the accounts controller. Defaults to Depends(AccountController).
        usr_ctrl (UserController, optional): the users controller. Defaults to Depends(UserController).

    Raises:
        HTTPException: account with the given id not found
        HTTPException: the account is not of the user authenticated.

    Returns:
        AccountOutSchema: the account found.
    """
    account = await ctrl.get("id", id)
    if account is None:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="account not found"
        )

    user = await usr_ctrl.get("id", account._mapping["user_id"])
    username = jwt_ctrl.validate_token(credentials)
    if username != user._mapping["username"]:  # type: ignore
        try:
            jwt_ctrl.validate_token(credentials, required_roles="admin")
        except JWTException:
            raise HTTPException(
                status_code=HTTPStatus.FORBIDDEN, detail="This is not your account."
            )

    return account


@router.get(
    "/",
    response_model=List[schemas.AccountOutSchema],
    summary="Lista todos as contas existentes.",
    description="Lista as contas de todos os usuários. Somente usuário que possuem a role `admin` pode acessar.",
)
async def list_accounts(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer)],
    limit: int = 100,
    offset: int = 0,
    ctrl: AccountController = Depends(AccountController),
):
    """list all accounts. Only users with `admin` role can have access.

    Args:
        credentials (Annotated[HTTPAuthorizationCredentials, Depends): authorization header value
        limit (int, optional): the limit of account. Defaults to 100.
        offset (int, optional): the offset to apply on list. Defaults to 0.
        ctrl (AccountController, optional): the accounts controller. Defaults to Depends(AccountController).

    Returns:
        List[AccountOutSchema]: the list of accounts
    """
    jwt_ctrl.validate_token(credentials, required_roles="admin")

    stmt = select(ctrl.model).limit(limit).offset(offset)
    accounts = await ctrl.query(stmt)
    return accounts
