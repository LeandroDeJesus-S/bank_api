from datetime import datetime
from typing import Optional, List

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
    iss: str = 'bank'
    sub: str 
    aud: str | List[str]
    iat: Optional[datetime] = None
    typ: Optional[str] = 'Bearer'
    exp: Optional[datetime] = None


class AuthSchema(BaseModel):
    """schema with the necessary data to auth the user"""
    username: str
    password: str


class RoleInSchema(BaseModel):
    """input role schema"""
    name: str


class RoleOutSchema(RoleInSchema):
    """output role schema"""
    id: int


class AddRoleSchema(BaseModel):
    user_id: int
    role_id: int


class TokenSchema(BaseModel):
    """The jwt token response schema

    Args:
        access_token (str): the generated access token
        token_type (str, Optional): the type of the token. Defaults to 'bearer'.
    """
    access_token: str
    token_type: str = 'bearer'
