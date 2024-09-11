from decimal import Decimal

from pydantic import BaseModel
from pydantic_settings import BaseSettings


class UserRules(BaseModel):
    """stores all the business rules related to the users part"""

    MIN_PASSWORD_SIZE: int = 8
    MAX_PASSWORD_SIZE: int = 20

    MIN_USER_AGE: int = 18
    MAX_USER_AGE: int = 120

    MIN_USERNAME_SIZE: int = 2
    MAX_USERNAME_SIZE: int = 20
    
    MIN_FIRSTNAME_SIZE: int = 2
    MAX_FIRSTNAME_SIZE: int = 45
    
    MIN_LASTNAME_SIZE: int = 2
    MAX_LASTNAME_SIZE: int = 100

    MIN_CPF_SIZE: int = 11
    MAX_CPF_SIZE: int = 14

    USERNAME_REGEX_PATTERN: str = (
        r"^([\w ]{2,20})$"  # alphanumeric and spaces, min 2 max 30 chars
    )
    FIRSTNAME_REGEX_PATTERN: str = r"^[A-Za-z]{2,45}$"
    LASTNAME_REGEX_PATTERN: str = r"^[A-Za-z ]{2,100}$"


class TransactionRules(BaseModel):
    """stores all the business rules related to the transactions part"""

    MIN_DEPOSIT_VALUE: Decimal = Decimal("0.01")
    MAX_DEPOSIT_VALUE: Decimal | None = None

    MIN_CASHOUT_VALUE: Decimal = Decimal("0.01")
    MAX_CASHOUT_VALUE: Decimal = Decimal("5_000")

    MIN_TRANSFER_VALUE: Decimal = Decimal("0.01")
    MAX_TRANSFER_VALUE: Decimal = Decimal("10_000")


class AccountRules(BaseModel):
    """stores all the business rules related to the accounts part"""

    NUMBER_SIZE: int = 10
    NUMBER_REGEX_PATTERN: str = r"\d+"


class AccountTypeRules(BaseModel):
    """stores all the business rules related to the accounts type"""

    MAX_TYPE_NAME_SIZE: int = 25
    TYPE_REGEX_PATTERN: str = r"^[A-Za-z]+$"


class DomainRules(BaseSettings):
    """stores all the business rules of the application"""

    user_rules: UserRules = UserRules()
    transaction_rules: TransactionRules = TransactionRules()
    account_rules: AccountRules = AccountRules()
    account_type_rules: AccountTypeRules = AccountTypeRules()


domain_rules = DomainRules()
