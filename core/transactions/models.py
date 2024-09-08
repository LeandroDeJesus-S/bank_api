import enum
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DECIMAL, TIMESTAMP, Enum, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from core import exceptions, validators
from core.database import Base
from core.domain_rules import domain_rules

TRANSACTION_RULES = domain_rules.transaction_rules


class TransactionType(enum.Enum):
    deposit = 0
    cashout = 1
    transference = 2


class Transaction(Base):
    """the model entity that represents the transactions"""

    __tablename__ = "transaction"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    from_id: Mapped[int] = mapped_column(
        ForeignKey("account.id", name="transaction_account_from")
    )
    to_id: Mapped[int] = mapped_column(
        ForeignKey("account.id", name="transaction_account_to")
    )
    value: Mapped[Decimal] = mapped_column(DECIMAL(10, 2), nullable=False)
    time: Mapped[datetime] = mapped_column(
        TIMESTAMP, nullable=False, server_default=func.current_timestamp()
    )
    type: Mapped[enum.Enum] = mapped_column(Enum(TransactionType), nullable=False)

    from_account: Mapped["Account"] = relationship()  # noqa: F821 #pyright: ignore
    to_account: Mapped["Account"] = relationship()  # noqa: F821  #pyright: ignore

    @validates("to_id")
    def validate_self_transference(self, _, receiver_id):
        """validates if the user doesn't make a transfer to him self"""
        if (
            receiver_id == self.from_id
            and self.type == self.TransactionTypes.transference
        ):
            raise exceptions.TransactionException(
                "Você não pode fazer uma transferência para você mesmo"
            )

        return receiver_id

    @validates("value")
    def validate_min_max_value(self, _, value):
        """validates the minimum and maximum value of the transaction"""
        transaction_type_validation_dict = {
            self.TransactionTypes.cashout: validators.min_max_validator(
                TRANSACTION_RULES.MIN_CASHOUT_VALUE,
                TRANSACTION_RULES.MAX_CASHOUT_VALUE,
                value,
            ),
            self.TransactionTypes.deposit: validators.min_max_validator(
                TRANSACTION_RULES.MIN_DEPOSIT_VALUE,
                TRANSACTION_RULES.MAX_DEPOSIT_VALUE,
                value,
            ),
            self.TransactionTypes.transference: validators.min_max_validator(
                TRANSACTION_RULES.MIN_TRANSFER_VALUE,
                TRANSACTION_RULES.MAX_TRANSFER_VALUE,
                value,
            ),
        }
        valid = transaction_type_validation_dict[self.type]

        if not valid:
            raise exceptions.TransactionException("Valor de transação inválido")

        return value

    @validates("value")
    def validate_transference_sufficient_value(self, _, value):
        """validates if the user has sufficient value to make the transaction"""
        if (
            self.type == self.TransactionTypes.transference
            and value < self.from_account.amount
        ):
            raise exceptions.TransactionException(
                "Valor insuficiente para realizar transferência."
            )

        return value

    @validates("value")
    def validate_cashout_sufficient_value(self, _, value):
        """validates if user has sufficient money to cash out"""
        if (
            self.type == self.TransactionTypes.cashout
            and value > self.from_account.amount
        ):
            raise exceptions.TransactionException(
                "Valor insuficiente para realizar retirada."
            )

        return value
