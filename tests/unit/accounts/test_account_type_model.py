from http import HTTPStatus
import pytest

from core.exceptions import AccountTypeInvalidException


async def test_validate_type_success(ini_account_type):
    """test validate_type with valid type name"""
    try:
        ini_account_type.validate_type()
    except AccountTypeInvalidException as e:
        pytest.fail(e.detail)


invalid_types = ['inv4lid', 'in_valid', 'not-valid', 'not valid']
@pytest.mark.parametrize('type', invalid_types)
async def test_validate_type_fail(ini_account_type, type):
    """test validate_type with valid type name"""
    ini_account_type.type = type

    with pytest.raises(AccountTypeInvalidException) as e:
        ini_account_type.validate_type()

    assert e.value.detail == "O tipo da conta deve conter apenas letras."
    assert e.value.code == HTTPStatus.UNPROCESSABLE_ENTITY
