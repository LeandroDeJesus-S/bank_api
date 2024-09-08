import pytest
from core.exceptions import JWTException


def test_generate_token_success(jwt_controller):
    """test success case of the generate_token method"""
    token = jwt_controller.generate_token({"aud": "usr:r", "iss": "bank:su"})

    assert isinstance(token, str)
    assert len(token) == 168


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
        {"sub": "usr1", "aud": "usr:r", "iss": "bank:su"}
    )
    sub = jwt_controller.validate_token(token, aud='usr:r', iss='bank:su')

    assert sub == 'usr1'


def test_validate_token_with_invalid_token(jwt_controller):
    """test if the validate_token method raises JWTException with
    an invalid token.
    """
    token = jwt_controller.generate_token(
        {"sub": "usr1", "aud": "usr:r", "iss": "bank:su"}
    )
    token += 'x'

    with pytest.raises(JWTException) as exc:
        jwt_controller.validate_token(token, aud='usr:r', iss='bank:su')

    assert exc.match('Invalid token')
    assert exc.type == JWTException


def test_validate_token_without_sub_claim(jwt_controller):
    """test if the validate_token method raises JWTException if
    the sub claim is not sent.
    """
    token = jwt_controller.generate_token({"aud": "usr:r", "iss": "bank:su"})

    with pytest.raises(JWTException) as exc:
        jwt_controller.validate_token(token, aud='usr:r', iss='bank:su')

    assert exc.match('Subject not provided.')
    assert exc.type == JWTException


def test_validate_token_diff_issuer_claim(jwt_controller):
    """test if the validate_token method raises JWTException if
    the iss claim do not match.
    """
    token = jwt_controller.generate_token({'sub': 'usr', "aud": "usr:r", "iss": "bank:su"})

    with pytest.raises(JWTException) as exc:
        jwt_controller.validate_token(token, aud='usr:r', iss='bank:u')

    assert exc.match('Cannot decode the token: Invalid issuer')
    assert exc.type == JWTException
