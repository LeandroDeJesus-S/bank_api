from typing import Mapping, Any
from sqlalchemy import insert
from sqlalchemy.exc import SQLAlchemyError
from core.database.controller import DatabaseController
from core.exceptions import DatabaseException
from .models import User
from core.auth.controllers import PasswordController


class UserController(DatabaseController):
    """controller to manager the user database operations"""
    def __init__(self) -> None:
        super().__init__(model=User)
        self._pw_controller = PasswordController()
    
    async def create(self, **mapping: Mapping[Any, Any]) -> int | None:
        self._check_fields(list(mapping.keys()))

        try:
            self._model(**mapping).validate()
            pw = mapping.get('password', '')
            hashed_pw = self._pw_controller.hash_password(pw)  # type: ignore
            mapping['password'] = hashed_pw  # type: ignore

            stmt = insert(self._model)
            return await self._db.execute(stmt, values=mapping)

        except SQLAlchemyError as exc:
            raise DatabaseException("Creation fail.") from exc

    async def update_(self, id: int, **mapping: Mapping) -> bool:
        if not isinstance(id, int):
            return False
        
        self._check_fields(list(mapping.keys()))
        
        if pw := mapping.get('password'):
            self.model(**mapping).validate_password()
            mapping['password'] = self._pw_controller.hash_password(pw)  # type: ignore

        return await super().update_(id, **mapping)
