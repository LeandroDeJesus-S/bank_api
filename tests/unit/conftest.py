import pytest_asyncio as pyt

from core.auth.controllers import JWTController, PasswordController


@pyt.fixture
def jwt_controller():
    ctrl = JWTController(
        secret_key="secret", algorithm="HS256", expiration_minutes=1
    )
    return ctrl


@pyt.fixture
def password_controller():
    ctrl = PasswordController()
    return ctrl
