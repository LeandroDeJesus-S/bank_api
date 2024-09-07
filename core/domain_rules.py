from pydantic import BaseModel, types
from pydantic_settings import BaseSettings


class UserRules(BaseModel):
    """stores all the business rules related to the users part"""
    MIN_PASSWORD_SIZE: int = 8
    MAX_PASSWORD_SIZE: int = 20

    MIN_USER_AGE: int = 18
    MAX_USER_AGE: int = 120

    MAX_USERNAME_SIZE: int = 20
    MAX_FIRSTNAME_SIZE: int = 45
    MAX_LASTNAME_SIZE: int = 100
    MAX_CPF_SIZE: int = 11

    USERNAME_REGEX_PATTERN: str = R'^\w([\w ]{2,20})\w$'  # alphanumeric and spaces, min 2 max 30 chars
    FIRSTNAME_REGEX_PATTERN: str = '^[A-Za-z ]{2,45}$'
    LASTNAME_REGEX_PATTERN: str = '^[A-Za-z ]{2,100}$'


class TransactionRules(BaseModel):
    """stores all the business rules related to the transactions part"""
    MIN_DEPOSIT_VALUE: types.Decimal = types.Decimal('0.01')
    MAX_DEPOSIT_VALUE: types.Decimal | None = None
    
    MIN_CASHOUT_VALUE: types.Decimal = types.Decimal('0.01')
    MAX_CASHOUT_VALUE: types.Decimal = types.Decimal('10_000')


class AccountRules(BaseModel):
    """stores all the business rules related to the accounts part"""
    NUMBER_SIZE: int = 10


class AccountTypeRules(BaseModel):
    """stores all the business rules related to the accounts type"""
    MAX_TYPE_NAME_SIZE = 25


class DomainRules(BaseSettings):
    """stores all the business rules of the application"""
    user_rules: UserRules = UserRules()
    transaction_rules: TransactionRules = TransactionRules()
    account_type_rules: AccountTypeRules = AccountTypeRules()


domain_rules = DomainRules()
