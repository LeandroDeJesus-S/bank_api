from typing import List
from datetime import date, datetime, timezone

from sqlalchemy import Date, String
from sqlalchemy.orm import Mapped, mapped_column, validates, relationship

from core import exceptions
from core.database import Base
from core.domain_rules import domain_rules
from core import validators

USER_RULES = domain_rules.user_rules


class User(Base):
    """the user entity representation"""
    __tablename__ = "user"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )
    username: Mapped[str] = mapped_column(
        String(USER_RULES.MAX_USERNAME_SIZE),
        nullable=False,
        unique=True,
    )
    password: Mapped[str] = mapped_column(
        String(USER_RULES.MAX_PASSWORD_SIZE),
        nullable=False,
    )
    first_name: Mapped[str] = mapped_column(
        String(USER_RULES.MAX_FIRSTNAME_SIZE),
        nullable=False,
    )
    last_name: Mapped[str] = mapped_column(
        String(USER_RULES.MAX_LASTNAME_SIZE),
        nullable=False,
    )
    cpf: Mapped[str] = mapped_column(
        String(USER_RULES.MAX_CPF_SIZE),
        nullable=False,
        unique=True,
    )
    birthdate: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    accounts: Mapped[List['Account']] = relationship(back_populates='user')  # noqa: F821 # pyright: ignore

    @validates("username")
    def validate_username(self, _, username):
        """validates if the username contains alphanumeric cases, spaces and
        the valid size"""
        matches = validators.regex_validator(
            USER_RULES.USERNAME_REGEX_PATTERN,
            username,
        )
        if not matches:
            raise exceptions.UserInvalidNameException(
                detail="O nome de usuário é inválido."
            )
        return username

    @validates("first_name")
    def validate_first_name(self, _, first_name):
        """validates if the first name contains only letters and has the
        valid size"""
        valid = validators.regex_validator(
            USER_RULES.FIRSTNAME_REGEX_PATTERN, first_name
        )
        if not valid:
            raise exceptions.UserInvalidNameException(
                detail='Primeiro nome inválido.'
            )
        return first_name

    @validates("last_name")
    def validate_last_name(self, _, last_name):
        """validates if the last name contains only letters and has the
        valid size"""
        valid = validators.regex_validator(
            USER_RULES.LASTNAME_REGEX_PATTERN, last_name
        )
        if not valid:
            raise exceptions.UserInvalidNameException(
                detail='Sobrenome inválido.'
            )
        return last_name

    @validates("cpf")
    def validate_cpf(self, _, cpf):
        """validates if the user's cpf is valid and return the cpf without punctuations"""
        validator = validators.CpfValidator(cpf)
        if not validator.is_valid():
            raise exceptions.UserInvalidCPFException("O CPF é inválido")

        return validator.cpf

    @validates("birthdate")
    def validate_birthdate(self, _, birthdate):
        """validates the max and min user's age required"""
        now = datetime.now(timezone.utc)

        user_age = now.year - birthdate.year
        min_age = domain_rules.user_rules.MIN_USER_AGE
        max_age = domain_rules.user_rules.MAX_USER_AGE
        is_valid = validators.min_max_validator(min_age, max_age, user_age)

        if not is_valid:
            raise exceptions.UserInvalidAgeException(
                f"A idade minima deve ser entre {min_age} e {max_age} anos."
            )
        return birthdate
