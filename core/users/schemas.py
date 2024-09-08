from typing import Annotated
from pydantic import BaseModel, ConfigDict, PastDate
from annotated_types import Len
from core.domain_rules import domain_rules


class UserOutSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    first_name: str
    last_name: str


class UserInSchema(UserOutSchema):
    password: str
    cpf: Annotated[str, Len(domain_rules.user_rules.MAX_CPF_SIZE)]
    birthdate: PastDate
