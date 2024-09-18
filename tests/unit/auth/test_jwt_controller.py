from http import HTTPStatus
import pytest
from fastapi.security import HTTPAuthorizationCredentials
from core.exceptions import JWTException
from jwt import ExpiredSignatureError


def test_generate_token_success(jwt_controller):
    """test success case of the generate_token method"""
    token = jwt_controller.generate_token({"aud": "usr:r", "iss": "bank:su"})

    assert isinstance(token, str)
    assert token.startswith('ey')


def test_generate_token_fail(jwt_controller):
    """test the fail case of generate_token method"""
    with pytest.raises(JWTException) as exc:
        jwt_controller.generate_token("invalid payload")

    assert exc.match(
        "Was not possible generate the token: 'str'"
        " object does not support item assignment"
    )
    assert exc.type == JWTException


def test_validate_token_with_valid_token(jwt_controller):
    """test if the validate_token method return the sub correctly
    with a valid token.
    """
    token = jwt_controller.generate_token(
        {"sub": "usr1", "aud": "adm", "iss": "bank"}
    )
    sub = jwt_controller.validate_token(
        HTTPAuthorizationCredentials(scheme="Bearer", credentials=token),
        required_roles='adm'
    )

    assert sub == "usr1"


def test_validate_token_with_invalid_token(jwt_controller):
    """test if the validate_token method raises JWTException with
    an invalid token.
    """
    token = jwt_controller.generate_token(
        {"sub": "usr1", "aud": "r", "iss": "bank:su"}
    )
    token += "x"

    with pytest.raises(JWTException) as exc:
        jwt_controller.validate_token(
            HTTPAuthorizationCredentials(scheme="Bearer", credentials=token),
        )

    assert exc.match("Invalid token")
    assert exc.type == JWTException


def test_validate_token_without_sub_claim(jwt_controller):
    """test if the validate_token method raises JWTException if
    the sub claim is not sent.
    """
    token = jwt_controller.generate_token({"aud": "r", "iss": "bank"})

    with pytest.raises(JWTException) as exc:
        jwt_controller.validate_token(
            HTTPAuthorizationCredentials(scheme="Bearer", credentials=token),
            required_roles='r'
        )

    assert exc.match("Subject not provided.")
    assert exc.type == JWTException


def test_validate_token_diff_issuer_claim(jwt_controller):
    """test if the validate_token method raises JWTException if
    the iss claim do not match.
    """
    token = jwt_controller.generate_token(
        {"sub": "usr", "aud": "r", "iss": "bank2"}
    )

    with pytest.raises(JWTException) as exc:
        jwt_controller.validate_token(
            HTTPAuthorizationCredentials(scheme="Bearer", credentials=token),
           required_roles='r'
        )

    assert exc.match("Cannot decode the token: Invalid issuer")
    assert exc.type == JWTException


def test_validate_token_expired(jwt_controller, mocker):
    mocker.patch("core.auth.controllers.jwt.decode", side_effect=ExpiredSignatureError)
    token = jwt_controller.generate_token(
        {"sub": "usr1", "aud": "r", "iss": "bank"}
    )

    with pytest.raises(JWTException) as e:
        jwt_controller.validate_token(
            HTTPAuthorizationCredentials(scheme="Bearer", credentials=token),
        )

    assert e.value.detail == "Token expired"
    assert e.value.code == HTTPStatus.UNAUTHORIZED
