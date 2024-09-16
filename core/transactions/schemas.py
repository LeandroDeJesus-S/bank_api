from decimal import Decimal
from typing import Annotated
from pydantic import BaseModel, ConfigDict, AwareDatetime, NaiveDatetime
from annotated_types import Gt
from .models import TransactionType


class TransactionInSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    from_account_id: int
    to_account_id: int
    value: Annotated[Decimal, Gt(Decimal('0'))]
    type: TransactionType


class TransactionOutSchema(TransactionInSchema):
    id: int
    time: AwareDatetime | NaiveDatetime
