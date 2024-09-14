from core.database.controller import DatabaseController
from .models import Account, AccountType


class AccountController(DatabaseController):
    """controller to manage the account database model"""

    def __init__(self) -> None:
        super().__init__(model=Account)


class AccountTypeController(DatabaseController):
    """controller to manage the account type database model"""

    def __init__(self) -> None:
        super().__init__(model=AccountType)
