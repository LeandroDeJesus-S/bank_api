from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class JWTPayload(BaseModel):
    """represents a sent JWT payload

    Args:
        iss: str
        sub: str
        aud: Optional[str]
        iat: Optional[datetime]
        typ: Optional[str]
        exp: Optional[datetime]
    """
    iss: str = 'the-bank'
    sub: str
    aud: Optional[str] = None
    iat: Optional[datetime] = None
    typ: Optional[str] = None
    exp: Optional[datetime] = None


class AuthSchema(BaseModel):
    """schema with the necessary data to auth the user"""
    username: str
    password: str
