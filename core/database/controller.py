from http import HTTPStatus
from typing import List, Any, Mapping, Sequence

from databases.interfaces import Record
from sqlalchemy import select, insert, update, delete

from sqlalchemy.exc import SQLAlchemyError

from core.exceptions import DatabaseException
from .conf import DB


class DatabaseController:
    """controller to manager the database operations"""

    DEFAULT_LIMIT = 1000
    DEFAULT_OFFSET = 0

    def __init__(self, model: Any = None, db=DB) -> None:  # type: ignore
        self._model = model
        self._db = db
        if self._model is None:
            raise AttributeError("the `model` argument must be expecified.")

    @property
    def model(self):
        return self._model

    async def get(self, where_field: str, equals_to: Any) -> Record | None:
        """return a registry where the `where_field` value matches with `equals_to` value

        Args:
            where_field (str): the of the field to use on the where clause
            equals_to (Any): the expected matching value to the where field

        Returns:
            Record: the model registry found
        """
        self.__check_fields([where_field])
        try:
            field = getattr(self._model, where_field)
            stmt = select(self._model).where(field == equals_to)
            user = await self._db.fetch_one(stmt)
            return user

        except SQLAlchemyError as exc:
            raise DatabaseException(
                f"Unexpected fail fetching `{self._model.__tablename__}`"  # type: ignore
            ) from exc

    async def all(
        self, limit: int = DEFAULT_LIMIT, offset: int = DEFAULT_OFFSET
    ) -> List[Record]:
        """return all model data from database

        Args:
            limit (int, optional): the limit of registries. Defaults to 1000.
            offset (int, optional): the offset to apply on the result. Defaults to 0.

        Returns:
            List[Record]: a list with all data found.
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
            print(str(exc))
            raise DatabaseException(
                "Error fetching data.",
            ) from exc

    async def create(self, **mapping: Mapping[Any,Any]) -> int | None:
        """creates a new registry in database

        Returns:
            int: 1 if created with success
        """
        self.__check_fields(list(mapping.keys()))

        try:
            self._model(**mapping).validate()

            stmt = insert(self._model)
            return await self._db.execute(stmt, values=mapping)

        except SQLAlchemyError as exc:
            print(str(exc))
            raise DatabaseException("Creation fail.") from exc

    async def update_(self, id: int, **mapping: Mapping) -> bool:
        """updates an registry from database

        Args:
            id (int): the registry id
            mapping (Mapping): the registry fields mapping to be updated
        """
        if not isinstance(id, int):
            return False

        self.__check_fields(list(mapping.keys()))

        try:
            stmt = (
                update(self._model).where(self._model.id == id).values(**mapping)  # type: ignore
            )
            return await self._db.execute(stmt)

        except SQLAlchemyError as e:
            raise DatabaseException("Update fail.") from e

    async def query(self, q, **values):
        """executes the given query"""
        if q._is_select_statement:
            return await self._db.fetch_all(q, values=values)
        return await self._db.execute(q, values=values)

    async def delete_(self, id: int):
        """deletes a registry from database

        Args:
            id (int): the registry id to delete

        Raises:
            DatabaseException: if some exception related to the sqlalchemy occur
        """
        try:
            stmt = delete(self._model).where(self._model.id == id)  # type: ignore
            await self._db.execute(stmt)
        except SQLAlchemyError:
            raise DatabaseException("Delete operation fail.")

    def __check_fields(self, fields: Sequence[str]):
        """raises DatabaseException if any of the given fields dos not exists."""
        for field in fields:
            if not hasattr(self._model, str(field)):
                raise DatabaseException(
                    f"`{self._model.__tablename__}` has no field `{field}`.",  # type: ignore
                    code=HTTPStatus.UNPROCESSABLE_ENTITY,
                )
