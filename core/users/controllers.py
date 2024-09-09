from http import HTTPStatus
from typing import List, Any, Mapping

from databases.interfaces import Record
from sqlalchemy import select, insert, update

from core.database import DB
from core.exceptions import UserDatabaseException
from .models import User


class UserController:
    """controller to manager the user database operations"""

    DEFAULT_LIMIT = 1000
    DEFAULT_OFFSET = 0

    def __init__(self) -> None:
        self._model = User
        self._db = DB

    async def get(self, where_field: str, equals_to: Any) -> Record | None:
        """return a user where the where field value matches with equals_to value

        Args:
            where_field (str): the of the field to use on the where clause
            equals_to (Any): the expected matching value to the where field

        Returns:
            Record: the user register found
        """
        try:
            field = getattr(self._model, where_field)
            stmt = select(self._model).where(field == equals_to)
            user = await self._db.fetch_one(stmt)
            return user

        except (AttributeError, TypeError):
            raise UserDatabaseException(
                "Invalid where_field name or type",
            )
        except Exception as exc:
            raise UserDatabaseException(
                f"Unexpected fail: {str(exc)}", code=HTTPStatus.INTERNAL_SERVER_ERROR
            )

    async def all(
        self, limit: int = DEFAULT_LIMIT, offset: int = DEFAULT_OFFSET
    ) -> List[Record]:
        """return all users from database

        Args:
            limit (int, optional): the limit of users. Defaults to 1000.
            offset (int, optional): the offset to apply on the result. Defaults to 0.

        Returns:
            List[Record]: a list with all users found.
        """
        if not isinstance(limit, int):
            limit = self.DEFAULT_LIMIT
        if not isinstance(offset, int):
            offset = self.DEFAULT_OFFSET

        try:
            stmt = select(self._model).offset(offset).limit(limit)
            users = await self._db.fetch_all(stmt)
            return users
        except Exception as exc:
            raise UserDatabaseException(
                f"Error fetching users: {str(exc)}",
            )

    async def create(self, **user_mapping: Mapping) -> int | None:
        """creates a new user in database

        Returns:
            bool: 1 if created with success
        """
        try:
            self._model(**user_mapping).validate()

            stmt = insert(self._model)
            return await self._db.execute(stmt, values=user_mapping)

        except Exception as exc:
            raise UserDatabaseException(f"User creation fail: {str(exc)}") from exc

    async def update_user(self, user_id: int, **mapping: Mapping) -> bool:
        """updates an user from database

        Args:
            user_id (int): the user id
            mapping (Mapping): the user fields mapping to be updated
        """
        if not isinstance(user_id, int):
            return False
        
        stmt = update(self._model).where(self._model.id == user_id).values(**mapping)
        return await self._db.execute(stmt)
