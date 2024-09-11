from http import HTTPStatus
from typing import List, Any, Mapping, Sequence
from databases.interfaces import Record
from sqlalchemy import select, insert, update, delete
from sqlalchemy.exc import SQLAlchemyError

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

        except (AttributeError, TypeError) as exc:
            raise UserDatabaseException(
                "Invalid where_field name or type",
            ) from exc

        except SQLAlchemyError as exc:
            raise UserDatabaseException("Unexpected fail on fetching user") from exc

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
        except SQLAlchemyError as exc:
            raise UserDatabaseException(
                "Error fetching users.",
            ) from exc

    async def create(self, **user_mapping: Mapping) -> int | None:
        """creates a new user in database

        Returns:
            bool: 1 if created with success
        """
        self.__check_fields(list(user_mapping.keys()))

        try:
            self._model(**user_mapping).validate()

            stmt = insert(self._model)
            return await self._db.execute(stmt, values=user_mapping)

        except SQLAlchemyError as exc:
            raise UserDatabaseException("User creation fail.") from exc

    async def update_user(self, user_id: int, **mapping: Mapping) -> bool:
        """updates an user from database

        Args:
            user_id (int): the user id
            mapping (Mapping): the user fields mapping to be updated
        """
        if not isinstance(user_id, int):
            return False
        
        self.__check_fields(list(mapping.keys()))

        try:
            stmt = (
                update(self._model).where(self._model.id == user_id).values(**mapping)
            )
            return await self._db.execute(stmt)

        except SQLAlchemyError as e:  # TODO: testar
            raise UserDatabaseException("User update fail.") from e

    async def query(self, q, **values):
        """executes the given query"""
        if q._is_select_statement:
            return await self._db.fetch_all(q, values=values)
        return await self._db.execute(q, values=values)

    async def delete_user(self, id: int):
        """deletes a user from database

        Args:
            id (int): the user id to delete

        Raises:
            UserDatabaseException: if some exception related to the sqlalchemy occur
        """
        try:
            stmt = delete(self._model).where(self._model.id == id)
            await self._db.execute(stmt)
        except SQLAlchemyError:
            raise UserDatabaseException(
                'Não foi possivel concluir a operação.'
            )

    def __check_fields(self, fields: Sequence[str]):
        """raises UserDatabaseException if any of the given fields dos not exists."""
        for field in fields:
            if not hasattr(self._model, field):
                raise UserDatabaseException(
                    f"{field} does not exists.", code=HTTPStatus.UNPROCESSABLE_ENTITY
                )
