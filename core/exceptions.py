from http import HTTPStatus


class ValidationException(Exception):
    """refers to error of validation"""
    def __init__(self, detail: str, *, code=HTTPStatus.UNPROCESSABLE_ENTITY) -> None:
        self.detail = detail
        self.code = code


class UserInvalidCPFException(ValidationException):
    """user's CPF is invalid"""


class UserInvalidAgeException(ValidationException):
    """user's age is invalid"""


class UserInvalidUsernameException(ValidationException):
    """the username of the user is invalid"""


class UserInvalidNameException(ValidationException):
    """the name of the user is invalid"""
