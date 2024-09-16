from http import HTTPStatus
from typing import List

from databases.interfaces import Record
from fastapi import APIRouter, Depends, HTTPException

from .controllers import TransactionController
from core.accounts.controllers import AccountController
from core.users.controllers import UserController
from .schemas import TransactionInSchema, TransactionOutSchema

router = APIRouter(prefix="/transactions", tags=["transactions"])


@router.get("/", response_model=List[TransactionOutSchema])
async def list_transactions(
    limit: int = TransactionController.DEFAULT_LIMIT,
    offset: int = TransactionController.DEFAULT_OFFSET,
    transaction_ctrl: TransactionController = Depends(TransactionController),
) -> List[Record]:
    transactions = await transaction_ctrl.all(limit, offset)
    return transactions


@router.post(
    "/",
    status_code=HTTPStatus.CREATED,
    summary="Registra uma nova transação.",
    response_model_exclude_unset=True
)
async def create_transaction(
    data: TransactionInSchema,
    transaction_ctrl: TransactionController = Depends(TransactionController),
    user_ctrl: UserController = Depends(UserController),
    account_ctrl: AccountController = Depends(AccountController),
):
    from_account = await account_ctrl.get("id", data.from_account_id)
    to_account = await account_ctrl.get("id", data.to_account_id)

    if from_account is None or to_account is None:
        raise HTTPException(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
            detail="the sender or receiver account id does not exists.",
        )

    await transaction_ctrl.new(
        from_account=from_account,
        to_account=to_account,
        value=data.value,
        type=data.type,
        accounts_controller=account_ctrl,
    )
