from typing import Annotated
from pydantic import BaseModel, ConfigDict, PastDate, Field
from annotated_types import Len
from core.domain_rules import domain_rules


class UserInSchema(BaseModel):
    """user input schema"""
    model_config = ConfigDict(from_attributes=True)

    username: str
    first_name: str
    last_name: str
    password: str
    cpf: Annotated[
        str,
        Len(domain_rules.user_rules.MIN_CPF_SIZE, domain_rules.user_rules.MAX_CPF_SIZE),
    ]
    birthdate: PastDate

class UserUpSchema(BaseModel):
    """user update schema"""
    username: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    password: str | None = None
    cpf: Annotated[
        str,
        Len(domain_rules.user_rules.MIN_CPF_SIZE, domain_rules.user_rules.MAX_CPF_SIZE),
    ] | None = None
    birthdate: PastDate | None = None


class UserOutSchema(UserInSchema):
    """user output schema"""
    id: int
    password: str = Field(exclude=True)
    cpf: str = Field(exclude=True)
