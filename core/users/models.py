from typing import List
from datetime import date, datetime, timezone

from sqlalchemy import Date, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core import exceptions
from core.database.conf import Base
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
        String(256),  # different of the configured value in rules cause stores the hash
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

    accounts: Mapped[List["Account"]] = relationship(back_populates="user")  # type: ignore # noqa: F821
    roles: Mapped[List["Role"]] = relationship(  # type: ignore # noqa: F821
        secondary="user_role", back_populates="users"
    )

    def validate(self):
        """call all functions that validates the fields"""
        self.validate_username()
        self.validate_password()
        self.validate_first_name()
        self.validate_last_name()
        self.validate_cpf()
        self.validate_birthdate()

    def validate_username(self):
        """validates if the username contains alphanumeric cases, spaces and
        the valid size"""
        matches = validators.regex_validator(
            USER_RULES.USERNAME_REGEX_PATTERN,
            self.username,
        )
        if not matches:
            raise exceptions.UserInvalidUsernameException(
                detail="O nome de usuário é inválido."
            )

    def validate_password(self):
        """validates the password strength"""
        if not validators.strong_password_validator(self.password):
            raise exceptions.UserWeakPasswordException(
                "A senha é muito fraca.",
            )

    def validate_first_name(self):
        """validates if the first name contains only letters and has the
        valid size"""
        valid = validators.regex_validator(
            USER_RULES.FIRSTNAME_REGEX_PATTERN, self.first_name, strict=True
        )
        if not valid:
            raise exceptions.UserInvalidNameException(detail="Primeiro nome inválido.")

    def validate_last_name(self):
        """validates if the last name contains only letters and has the
        valid size"""
        valid = validators.regex_validator(
            USER_RULES.LASTNAME_REGEX_PATTERN, self.last_name, strict=True
        )
        if not valid:
            raise exceptions.UserInvalidNameException(detail="Sobrenome inválido.")

    def validate_cpf(self):
        """validates if the user's cpf is valid and return the cpf without punctuations"""
        validator = validators.CpfValidator(self.cpf)
        if not validator.is_valid():
            raise exceptions.UserInvalidCPFException("O CPF é inválido")

    def validate_birthdate(self):
        """validates the max and min user's age required"""
        now = datetime.now(timezone.utc)

        user_age = now.year - self.birthdate.year
        min_age = domain_rules.user_rules.MIN_USER_AGE
        max_age = domain_rules.user_rules.MAX_USER_AGE
        is_valid = validators.min_max_validator(min_age, max_age, user_age)

        if not is_valid:
            raise exceptions.UserInvalidAgeException(
                f"A idade minima deve ser entre {min_age} e {max_age} anos."
            )
