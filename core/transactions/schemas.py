from datetime import datetime
from decimal import Decimal
from typing import Annotated
from pydantic import BaseModel, ConfigDict
from annotated_types import Gt


class TransactionSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    from_id: int
    to_id: int
    value: Annotated[Decimal, Gt(Decimal('0'))]
    time: datetime
    type: str
