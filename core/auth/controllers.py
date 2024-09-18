from datetime import datetime, timedelta, timezone
from http import HTTPStatus
from typing import Any, List, Optional, Union

import jwt
from fastapi.security import HTTPAuthorizationCredentials
from passlib.hash import pbkdf2_sha256
from sqlalchemy import select

from core.database.controller import DatabaseController
from core.exceptions import JWTException
from core.settings import settings

from .models import Role, UserRole


class JWTController:
    """Controller class to manage JWT token functionalities"""

    def __init__(self) -> None:
        """
        Args:
            algorithm (str): the algorithm name
            expiration_minutes (int, optional): the token expiration time in minutes. Defaults to 5, minimum 1.
        """
        self.__secret_key = settings.JWT_SECRET
        self.algorithm = "HS256"
        self.expiration_delta_minutes = timedelta(minutes=5)

    def generate_token(self, payload: dict[str, Any]) -> str:
        """generates the JWT token with the given payload

        Args:
            payload (dict[str, Any]): the JWT payload

        Raises:
            JWTException: raised if some error occur when decoding token

        Returns:
            str: the generated token

        """
        try:
            now = datetime.now(timezone.utc)
            payload["iat"] = now
            payload["exp"] = now + self.expiration_delta_minutes
            
            print("encoded payload:", payload)

            encoded = jwt.encode(payload, self.__secret_key, self.algorithm)
        except Exception as exc:
            raise JWTException(f"Was not possible generate the token: {exc}") from exc

        return encoded

    def validate_token(
        self,
        credentials: HTTPAuthorizationCredentials,
        required_roles: Union[str, List[str]] = 'none',
    ) -> Any:
        """validates the JWT token.

        Args:
            credentials (HTTPAuthorizationCredentials): return the schema and the value of the token
            aud (str): the audience claim value
            iss (str): the issuer claim value
            require_role (Optional[Union[List[str]]]): the role names to get in the `aud` claim

        Raises:
            JWTException: raised if some error occur when decoding token or if the `sub`
            value is 'none' or the required role not found

        Returns:
            Any: the `sub` claim value
        """
        token = credentials.credentials
        try:
            payload = jwt.decode(
                token,
                self.__secret_key,
                [self.algorithm],
                audience=required_roles,
                issuer="bank",
            )
            sub = payload.get("sub")
            if sub is None:
                raise JWTException(
                    "Subject not provided.", code=HTTPStatus.UNAUTHORIZED
                )

            return sub

        except jwt.exceptions.DecodeError as exc:
            raise JWTException("Invalid token", code=HTTPStatus.UNAUTHORIZED) from exc

        except jwt.exceptions.ExpiredSignatureError as exc:
            raise JWTException("Token expired", code=HTTPStatus.UNAUTHORIZED) from exc

        except jwt.exceptions.InvalidTokenError as exc:
            raise JWTException(
                f"Cannot decode the token: {str(exc)}", code=HTTPStatus.UNAUTHORIZED
            ) from exc


class PasswordController:
    """Controller class that manage password functionalities"""

    def __init__(self) -> None:
        """
        Args:
            hasher (Any): a hasher class that supports .hash(password) and
            .verify(raw_pw, hash_pw) operation methods
        """
        self._hasher = pbkdf2_sha256
        self._hash_prefix = "hash::"

    def hash_password(self, password: str) -> str:
        """hash the given password

        Args:
            password (str): the password to hash

        Returns:
            str: the password hash result
        """
        hashed = self._hasher.hash(password)
        return self._hash_prefix + hashed

    def check_password(self, password_raw: str, password_hash: str) -> bool:
        """validates if password matches with the hashed password.

        Args:
            password_raw (str): user input password
            password_hash (str): hashed password

        Returns:
            bool: True if password matches
        """
        pw_hash = password_hash.removeprefix(self._hash_prefix)
        return self._hasher.verify(password_raw, pw_hash)


class RoleController(DatabaseController):
    def __init__(self) -> None:
        super().__init__(model=Role)


class UserRoleController(DatabaseController):
    def __init__(self) -> None:
        super().__init__(model=UserRole)

    async def check_role(self, user, role) -> bool:
        """check if the given user has the given role.

        Args:
            user (User): the user entity instance.
            role (Role): the role entity instance.

        Returns:
            bool: True the the user has the role.
        """
        stmt = select(self.model.user_id == user.id, self.model.role_id == role.id)
        has = await self.query(stmt)
        return bool(has)
