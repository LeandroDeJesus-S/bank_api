from http import HTTPStatus
from typing import Annotated, List

from databases.interfaces import Record
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select

from .controllers import TransactionController
from core.accounts.controllers import AccountController
from core.auth.controllers import JWTController
from core.users.controllers import UserController
from .schemas import TransactionInSchema, TransactionOutSchema

router = APIRouter(prefix="/transactions", tags=["transactions"])
jwt_ctrl = JWTController()
bearer = HTTPBearer()


@router.get(
    "/",
    response_model=List[TransactionOutSchema],
    summary="Lista todas as transações realizadas por todas as contas.",
    description="Apenas usuários autenticados que possuem a role `admin` podem ter acesso.",
)
async def list_transactions(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer)],
    limit: int = TransactionController.DEFAULT_LIMIT,
    offset: int = TransactionController.DEFAULT_OFFSET,
    transaction_ctrl: TransactionController = Depends(TransactionController),
) -> List[Record]:
    """list all transactions. Only admin users can access.

    Args:
        credentials (Annotated[HTTPAuthorizationCredentials, Depends): authorization header value.
        limit (int, optional): the limit of transactions to show. Defaults to TransactionController.DEFAULT_LIMIT.
        offset (int, optional): the offset to apply. Defaults to TransactionController.DEFAULT_OFFSET.
        transaction_ctrl (TransactionController, optional): the transactions controller. Defaults to Depends(TransactionController).

    Returns:
        List[Record]: all the transactions from database.
    """
    jwt_ctrl.validate_token(credentials, required_roles="admin")

    transactions = await transaction_ctrl.all(limit, offset)
    return transactions


@router.get(
    "/me",
    response_model=List[TransactionOutSchema],
    summary="Lista todas as transações da conta do usuário autenticado.",
    description="Retorna as transações do usuário atual autenticado."
)
async def list_account_transactions(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer)],
    limit: int = TransactionController.DEFAULT_LIMIT,
    offset: int = TransactionController.DEFAULT_OFFSET,
    transaction_ctrl: TransactionController = Depends(TransactionController),
    account_ctrl: AccountController = Depends(AccountController),
    user_ctrl: UserController = Depends(UserController),
) -> List[Record]:
    """list all transactions of the authenticated user.

    Args:
        credentials (Annotated[HTTPAuthorizationCredentials, Depends): the authorization header value.
        limit (int, optional): the limit of transactions to show. Defaults to TransactionController.DEFAULT_LIMIT.
        offset (int, optional): the offset to apply. Defaults to TransactionController.DEFAULT_OFFSET.
        transaction_ctrl (TransactionController, optional): the transaction controller instance. Defaults to Depends(TransactionController).
        account_ctrl (AccountController, optional): the accounts controller instance. Defaults to Depends(AccountController).
        user_ctrl (UserController, optional): the user controller instance. Defaults to Depends(UserController).

    Returns:
        List[Record]: the list of the account transactions found
    """
    username = jwt_ctrl.validate_token(credentials)
    user = await user_ctrl.get("username", username)
    account = await account_ctrl.get("user_id", user.id)  # type: ignore

    stmt = (
        select(transaction_ctrl.model)
        .where(
            transaction_ctrl.model.from_account_id == account.id  # type: ignore
        )
        .limit(limit)
        .offset(offset)
    )

    transactions = await transaction_ctrl.query(stmt)
    return transactions


@router.post(
    "/",
    status_code=HTTPStatus.CREATED,
    summary="Registra uma nova transação.",
    description="É preciso estar autenticado e o usuário autenticado só pode criar uma transação para sua própria conta.",
    response_model_exclude_unset=True,
)
async def create_transaction(
    data: TransactionInSchema,
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer)],
    transaction_ctrl: TransactionController = Depends(TransactionController),
    user_ctrl: UserController = Depends(UserController),
    account_ctrl: AccountController = Depends(AccountController),
):
    """creates a new transaction

    Args:
        data (TransactionInSchema): the data to create the transaction.
        credentials (Annotated[HTTPAuthorizationCredentials, Depends): authorization header value.
        transaction_ctrl (TransactionController, optional): the transaction controller instance. Defaults to Depends(TransactionController).
        user_ctrl (UserController, optional): the user controller instance. Defaults to Depends(UserController).
        account_ctrl (AccountController, optional): the account controller instance. Defaults to Depends(AccountController).

    Raises:
        HTTPException: the sender or account id does not exists
        HTTPException: the user is trying to make a transaction using an account of other user.
    """
    from_account = await account_ctrl.get("id", data.from_account_id)
    to_account = await account_ctrl.get("id", data.to_account_id)

    username = jwt_ctrl.validate_token(credentials)
    print("decoded username:", username)

    if from_account is None or to_account is None:
        raise HTTPException(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
            detail="the sender or receiver account id does not exists.",
        )

    user = await user_ctrl.get("id", from_account._mapping["user_id"])
    if username != user._mapping["username"]:  # type: ignore
        raise HTTPException(
            status_code=HTTPStatus.FORBIDDEN,
            detail="You can only make a transaction from your own account",
        )

    await transaction_ctrl.new(
        from_account=from_account,
        to_account=to_account,
        value=data.value,
        type=data.type,
        accounts_controller=account_ctrl,
    )
