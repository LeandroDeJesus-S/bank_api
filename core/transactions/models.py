import enum
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DECIMAL, TIMESTAMP, Enum, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship


from core.database.conf import Base



class TransactionType(enum.Enum):
    deposit = 0
    withdraw = 1
    transference = 2


class Transaction(Base):
    """the model entity that represents the transactions"""

    __tablename__ = "transaction"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    from_account_id: Mapped[int] = mapped_column(
        ForeignKey("account.id", name="transaction_account_from")
    )
    to_account_id: Mapped[int] = mapped_column(
        ForeignKey("account.id", name="transaction_account_to")
    )
    value: Mapped[Decimal] = mapped_column(DECIMAL(10, 2), nullable=False)
    time: Mapped[datetime] = mapped_column(
        TIMESTAMP, nullable=False, server_default=func.current_timestamp()
    )
    type: Mapped[enum.Enum] = mapped_column(Enum(TransactionType), nullable=False)

    from_account: Mapped["Account"] = relationship(  # type: ignore # noqa
        back_populates="sent_transactions", foreign_keys=[from_account_id]
    )
    to_account: Mapped["Account"] = relationship(  # type: ignore # noqa
        back_populates="received_transactions", foreign_keys=[to_account_id]
    )

    def validate(self): ...