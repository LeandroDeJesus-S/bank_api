from http import HTTPStatus
from typing import Annotated, List

from databases.interfaces import Record
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from .controllers import TransactionController
from core.accounts.controllers import AccountController
from core.auth.controllers import JWTController
from core.users.controllers import UserController
from .schemas import TransactionInSchema, TransactionOutSchema

router = APIRouter(prefix="/transactions", tags=["transactions"])
jwt_ctrl = JWTController()
bearer = HTTPBearer()


@router.get("/", response_model=List[TransactionOutSchema])
async def list_transactions(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer)],
    limit: int = TransactionController.DEFAULT_LIMIT,
    offset: int = TransactionController.DEFAULT_OFFSET,
    transaction_ctrl: TransactionController = Depends(TransactionController),
) -> List[Record]:
    jwt_ctrl.validate_token(credentials, required_roles="admin")

    transactions = await transaction_ctrl.all(limit, offset)
    return transactions


@router.post(
    "/",
    status_code=HTTPStatus.CREATED,
    summary="Registra uma nova transação.",
    response_model_exclude_unset=True,
)
async def create_transaction(
    data: TransactionInSchema,
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer)],
    transaction_ctrl: TransactionController = Depends(TransactionController),
    user_ctrl: UserController = Depends(UserController),
    account_ctrl: AccountController = Depends(AccountController),
):
    from_account = await account_ctrl.get("id", data.from_account_id)
    to_account = await account_ctrl.get("id", data.to_account_id)

    username = jwt_ctrl.validate_token(credentials)
    print('decoded username:', username)
    
    if from_account is None or to_account is None:
        raise HTTPException(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
            detail="the sender or receiver account id does not exists.",
        )

    user = await user_ctrl.get('id', from_account._mapping['user_id'])
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
