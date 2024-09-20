from decimal import Decimal
from typing import List

from sqlalchemy import String, DECIMAL, ForeignKey, CHAR
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core import exceptions
from core.database.conf import Base
from core.domain_rules import domain_rules
from core import validators

ACC_RULES = domain_rules.account_rules
ACC_TYPE_RULES = domain_rules.account_type_rules


class AccountType(Base):
    """The entity model that represents the account type
    
    Args:
        id (int, optional): the account type id, is the primary key with autoincrement.
        type (str): the type name. Must be unique and not null.
        account (List[Account]): the relationship reference to account model
    """

    __tablename__ = "account_type"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    type: Mapped[str] = mapped_column(
        String(ACC_TYPE_RULES.MAX_TYPE_NAME_SIZE), nullable=False, unique=True
    )

    account: Mapped[List["Account"]] = relationship(back_populates="account_type")
    
    def validate(self):
        self.validate_type()

    def validate_type(self):
        """validate if the account type name matches with the regex pattern"""
        valid = validators.regex_validator(
            ACC_TYPE_RULES.TYPE_REGEX_PATTERN, self.type, strict=True
        )
        if not valid:
            raise exceptions.AccountTypeInvalidException(
                detail="O tipo da conta deve conter apenas letras (exceto caracteres especiais)."
            )


class Account(Base):
    """the model entity that represents the user account
    
    Args:
        id (int, optional): the id of the account. Is the primary key with autoincrement.
        number (str): the number of the account. Must be unique, not null and exactly 10 chars.
        amount (Decimal): the amount of the account. Can't be null and the default is 0.
        user_id (int): the Foreign Key that references the user id own of the account.
        account_type_id (int): the account type id. Foreign key that references the account type.
        user (User): the User relationship reference.
        account_type (AccountType): the account type relationship reference.
        sent_transactions (List[Transaction]): the relationship reference to all transactions that the user made.
        received_transactions (List[Transaction]): the relationship reference to all transaction received by the user.
    """

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
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"))
    account_type_id: Mapped[int] = mapped_column(ForeignKey("account_type.id"))

    user: Mapped["User"] = relationship(back_populates="accounts")  # type: ignore # noqa: F821
    account_type: Mapped["AccountType"] = relationship(back_populates="account")
    
    sent_transactions: Mapped[List["Transaction"]] = relationship(  # type: ignore # noqa: F821
        back_populates="from_account", foreign_keys="[Transaction.from_account_id]"
    )
    received_transactions: Mapped[List["Transaction"]] = relationship(  # type: ignore # noqa: F821
        back_populates="to_account", foreign_keys="[Transaction.to_account_id]"
    )
    
    def validate(self):
        """method that call the validation field methods"""
        self.validate_number()
        self.validate_amount()

    def validate_number(self):
        """validates if the number field matches with the regex pattern and
        the size configured in the domain rules config
        """
        valid_pattern = validators.regex_validator(
            ACC_RULES.NUMBER_REGEX_PATTERN, self.number, strict=True
        )
        valid_length = validators.min_max_validator(
            ACC_RULES.NUMBER_SIZE, ACC_RULES.NUMBER_SIZE, len(self.number)
        )
        if not valid_pattern:
            raise exceptions.AccountInvalidNumberException(
                "O número da conta deve conter apenas números."
            )

        if not valid_length:
            raise exceptions.AccountInvalidNumberException(
                f"O número da conta deve conter {ACC_RULES.NUMBER_SIZE} números."
            )

    def validate_amount(self):
        """validates if the amount is not negative"""
        if self.amount < Decimal("0"):
            raise exceptions.AccountInvalidAmountException(
                "O valor não pode ser menor que 0."
            )
