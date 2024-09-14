from core.database.controller import DatabaseController
from .models import User


class UserController(DatabaseController):
    """controller to manager the user database operations"""
    def __init__(self) -> None:
        super().__init__(model=User)
