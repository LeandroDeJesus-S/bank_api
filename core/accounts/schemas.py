from decimal import Decimal
from typing import Annotated

from annotated_types import Ge, Len
from pydantic import BaseModel

from core.domain_rules import domain_rules


class AccountTypeInSchema(BaseModel):
    """account type input schema"""
    type: str


class AccountTypeOutSchema(AccountTypeInSchema):
    """account type output schema"""
    id: int


class AccountInSchema(BaseModel):
    """account input schema"""
    number: Annotated[str, Len(domain_rules.account_rules.NUMBER_SIZE)]
    amount: Annotated[Decimal, Ge(Decimal('0'))]
    user_id: int
    account_type_id: int


class AccountOutSchema(AccountInSchema):
    """account output schema"""
    id: int
