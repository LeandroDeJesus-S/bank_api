from http import HTTPStatus


class ValidationException(Exception):
    """refers to error of validation"""
    def __init__(self, detail: str, *, code=HTTPStatus.UNPROCESSABLE_ENTITY) -> None:
        self.detail = detail
        self.code = code


# user exceptions
class UserWeakPasswordException(ValidationException):
    """the user password is too weak"""

class UserInvalidCPFException(ValidationException):
    """user's CPF is invalid"""


class UserInvalidAgeException(ValidationException):
    """user's age is invalid"""


class UserInvalidUsernameException(ValidationException):
    """the username of the user is invalid"""


class UserInvalidNameException(ValidationException):
    """the name of the user is invalid"""


class UserDatabaseException(ValidationException):
    """raises when a database operation related to users fail"""
    def __init__(self, detail: str, *, code=HTTPStatus.INTERNAL_SERVER_ERROR) -> None:
        super().__init__(detail, code=code)

# account exceptions


class AccountTypeInvalidException(ValidationException):
    """raise when the account type is invalid"""


class AccountInvalidNumberException(ValidationException):
    """raises when the account number is invalid"""


class AccountInvalidAmountException(ValidationException):
    """raises when the amount value of the account is invalid"""


# Transaction exceptions


class TransactionException(ValidationException):
    """raises when something is wrong in the transaction"""


# auth exceptions


class JWTException(ValidationException):
    """raises when something is wrong with the token"""
