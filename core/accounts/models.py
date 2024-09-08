from decimal import Decimal

from sqlalchemy import String, DECIMAL, ForeignKey, CHAR
from sqlalchemy.orm import Mapped, mapped_column, validates, relationship

from core import exceptions
from core.database import Base
from core.domain_rules import domain_rules
from core import validators

ACC_RULES = domain_rules.account_rules
ACC_TYPE_RULES = domain_rules.account_type_rules


class AccountType(Base):
    """The entity model that represents the account type"""

    __tablename__ = "account_type"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    type: Mapped[str] = mapped_column(
        String(ACC_TYPE_RULES.MAX_TYPE_NAME_SIZE), nullable=False, unique=True
    )

    account: Mapped['Account'] = relationship(back_populates='account_type')

    @validates("type")
    def validate_type(self, _, type):
        valid = validators.regex_validator(
            ACC_TYPE_RULES.TYPE_REGEX_PATTERN, type
        )
        if not valid:
            raise exceptions.AccountTypeInvalidException(
                detail="O tipo da conta deve conter apenas letras."
            )

        return type


class Account(Base):
    """the model entity that represents the user account"""

    __tablename__ = "account"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    number: Mapped[str] = mapped_column(
        CHAR(ACC_RULES.NUMBER_SIZE),
        nullable=False,
        unique=True,
    )
    amount: Mapped[Decimal] = mapped_column(
        DECIMAL(10, 2),
        nullable=False,
        default=Decimal("0"),
    )
    user_id: Mapped[int] = mapped_column(ForeignKey("account.id"))
    account_type_id: Mapped[int] = mapped_column(ForeignKey("account_type.id"))

    user: Mapped['User'] = relationship(back_populates='accounts')  # noqa: F821 # pyright: ignore
    account_type: Mapped['AccountType'] = relationship(back_populates='accounts')

    @validates("number")
    def validate_number(self, _, number):
        """validates if the number field matches with the regex pattern and
        the size configured in the domain rules config
        """
        valid_pattern = validators.regex_validator(
            ACC_RULES.NUMBER_REGEX_PATTERN, number
        )
        valid_length = validators.min_max_validator(
            ACC_RULES.NUMBER_SIZE, ACC_RULES.NUMBER_SIZE, len(number)
        )
        if not valid_pattern:
            raise exceptions.AccountInvalidNumberException(
                "O número da conta deve conter apenas números."
            )

        elif not valid_length:
            raise exceptions.AccountInvalidNumberException(
                f"O número da conta deve conter {ACC_RULES.NUMBER_SIZE} números."
            )

        return number

    @validates("amount")
    def validate_amount(self, _, amount):
        """validates if the amount is not negative"""
        if amount < Decimal("0"):
            raise exceptions.AccountInvalidAmountException(
                "O valor não pode ser menor que 0."
            )

        return amount
