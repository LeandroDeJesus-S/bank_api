from datetime import datetime, timezone, timedelta
from http import HTTPStatus
from typing import Any

import jwt

from core.exceptions import JWTException


class JWTController:
    def __init__(
        self, secret_key: str, algorithm: str, expiration_minutes: int = 5
    ) -> None:
        """
        Args:
            secret_key (str): the secret key used to generate the token
            algorithm (str): the algorithm name
            expiration_minutes (int, optional): the token expiration time in minutes. Defaults to 5, minimum 1.
        """
        self.__secret_key = secret_key
        self.algorithm = algorithm
        self.expiration_delta_minutes = timedelta(minutes=max(1, expiration_minutes))

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
            
            encoded = jwt.encode(payload, self.__secret_key, self.algorithm)
        except Exception as exc:
            raise JWTException(
                f"Was not possible generate the token: {exc}"
            ) from exc
        
        return encoded

    def validate_token(self, token: str, aud: str, iss: str) -> Any:
        """validates the JWT token.

        Args:
            token (str): the token to validate
            aud (str): the audience claim value
            iss (str): the issuer claim value

        Raises:
            JWTException: raised if some error occur when decoding token or if the `sub`
            value is None

        Returns:
            Any: the `sub` claim value
        """
        try:
            payload = jwt.decode(
                token,
                self.__secret_key,
                [self.algorithm],
                audience=aud,
                issuer=iss,
            )
            sub = payload.get("sub")
            if sub is None:
                raise JWTException(
                    "Subject not provided.", code=HTTPStatus.UNAUTHORIZED
                )
            return sub

        except jwt.exceptions.DecodeError as exc:
            raise JWTException(
                "Invalid token", code=HTTPStatus.UNAUTHORIZED
            ) from exc

        except jwt.exceptions.ExpiredSignatureError as exc:
            raise JWTException(
                "Expired token", code=HTTPStatus.UNAUTHORIZED
            ) from exc
        
        except jwt.exceptions.InvalidTokenError as exc:
            raise JWTException(
                f"Cannot decode the token: {str(exc)}", code=HTTPStatus.UNAUTHORIZED
            ) from exc
