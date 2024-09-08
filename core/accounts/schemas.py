from decimal import Decimal
from typing import Annotated

from annotated_types import Gt, Len
from pydantic import BaseModel

from core.domain_rules import domain_rules


class AccountTypeSchema(BaseModel):
    id: int
    type: str


class AccountSchema(BaseModel):
    id: int
    number: Annotated[str, Len(domain_rules.account_rules.NUMBER_SIZE)]
    amount: Annotated[Decimal, Gt(Decimal('0'))]
    user_id: int
    account_type: AccountTypeSchema
