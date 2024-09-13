from http import HTTPStatus
from typing import Mapping, Sequence, Literal
from databases.interfaces import Record
from sqlalchemy import select, insert
from sqlalchemy.exc import SQLAlchemyError

from core.database import DB
from core.exceptions import AccountDatabaseException
from .models import Account, AccountType


class AccountsController:
    """controller to manage the account and account type database models"""

    def __init__(self) -> None:
        self._account_model = Account
        self._account_type_model = AccountType
        self._db = DB

    async def get_account(
        self, by: Literal["id", "number"], value: int | str
    ) -> Record | None:
        """fetch one account from database number or id

        Args:
            by (Literal[&#39;id&#39;, &#39;number&#39;]): the field name to fetch the account
            value (int | str): the value to match on `where` clause

        Raises:
            AttributeError: if by argument is defferent of 'id' or 'number'
            TypeError: if value is not instance of int or str
            AccountDatabaseException: if some error with sqlalchemy occur

        Returns:
            Record: the account found
            None: if no one account found
        """
        if by not in ["id", "number"]:
            raise AttributeError("the `by` argument value must be `id` or `number`.")
        if not isinstance(value, int | str):
            raise TypeError("the `value` argument must be int or str.")

        try:
            field = getattr(self._account_model, by)
            stmt = select(self._account_model).where(field == value)
            account = await self._db.fetch_one(stmt)
            return account

        except SQLAlchemyError:
            raise AccountDatabaseException("Something went wrong getting the account.")

    async def create_account(self, **mapping: Mapping) -> bool:
        """creates a new account

        Raises:
            AccountDatabaseException: if some sqlalchemy error occur

        Returns:
            bool: True if the account was created
        """
        self.__check_fields(list(mapping.keys()), self._account_model)

        try:
            stmt = insert(self._account_model).values(**mapping)
            created = await self._db.execute(stmt)
            return bool(created)

        except SQLAlchemyError:
            raise AccountDatabaseException("Something went wrong creating the account.")

    async def get_account_type(
        self, by: Literal["id", "type"], value: int | str
    ) -> Record | None:
        """fetch one account  type from database number or id

        Args:
            by (Literal['id', 'type']): the field to user in the where clause.
            value (int | str): the value expected to match for the by field

        Raises:
            AttributeError: if by is not `id` or `type`
            TypeError: if `value` is not instance of int or str
            AccountDatabaseException: if some sqlalchemy error occur

        Returns:
            Record: the account type
            None: if no one account type with the given id is found
        """
        if by not in ["id", "type"]:
            raise AttributeError("`by`must be `id` or `type`.")

        if not isinstance(value, int | str):
            raise TypeError("`value` must be instance of int or str")

        try:
            field = getattr(self._account_type_model, by)
            stmt = select(self._account_type_model).where(field == value)
            account_type = await self._db.fetch_one(stmt)
            return account_type

        except SQLAlchemyError:
            raise AccountDatabaseException(
                "Something went wrong getting the account type."
            )

    async def create_account_type(self, **mapping: Mapping) -> bool:
        """creates a new account type

        Raises:
            AccountDatabaseException: if some sqlalchemy error occur

        Returns:
            bool: True if the account type was created
        """
        self.__check_fields(list(mapping.keys()), self._account_type_model)
        self._account_type_model(**mapping).validate()

        try:
            stmt = insert(self._account_type_model).values(**mapping)
            created = await self._db.execute(stmt)
            return bool(created)

        except SQLAlchemyError:
            raise AccountDatabaseException(
                "Something went wrong creating the account type."
            )

    def __check_fields(
        self, fields: Sequence[str], model: type[Account] | type[AccountType]
    ):
        for field in fields:
            if not hasattr(model, field):
                raise AccountDatabaseException(
                    f"`{model.__tablename__}` has no attr `{field}`",
                    code=HTTPStatus.UNPROCESSABLE_ENTITY,
                )
