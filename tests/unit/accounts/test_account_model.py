from decimal import Decimal
from http import HTTPStatus

import pytest

from core import exceptions


async def test_validate_number_success(ini_account):
    """test validate_number with valid number"""
    try:
        ini_account.validate_number()
    except exceptions.AccountInvalidNumberException as e:
        pytest.fail(e.detail)


invalid_numbers = ['123456789', '012345678a', '1234-67890', '1234 67890', '12345678910']
@pytest.mark.parametrize('number', invalid_numbers)
async def test_validate_number_fail(ini_account, number):
    """test validate_number with invalid numbers"""
    ini_account.number = number

    with pytest.raises(exceptions.AccountInvalidNumberException) as e:
        ini_account.validate_number()

    assert e.match(r'O número da conta deve conter apenas|\d{2} números\.$')
    assert e.value.code == HTTPStatus.UNPROCESSABLE_ENTITY


async def test_validate_amount_success(ini_account):
    """test validate amount with valid data"""
    try:
        ini_account.validate_amount()
    except exceptions.AccountInvalidAmountException as e:
        pytest.fail(e.detail)


async def test_validate_amount_fail(ini_account):
    """test validate amount with negative value"""
    ini_account.amount = Decimal('-0.01')
    with pytest.raises(exceptions.AccountInvalidAmountException) as e:
        ini_account.validate_amount()
    
    assert e.value.detail == "O valor não pode ser menor que 0."
    assert e.value.code == HTTPStatus.UNPROCESSABLE_ENTITY


async def test_validate_success(ini_account):
    """test validate with valid data"""
    try:
        ini_account.validate()
    except (exceptions.AccountInvalidAmountException, exceptions.AccountInvalidNumberException) as e:
        pytest.fail(e.detail)


invalid_data = [('0123a56789', Decimal('0')), ('0123456789', Decimal('-1'))]
@pytest.mark.parametrize('number,amount', invalid_data)
async def test_validate_fail(ini_account, number, amount):
    """test validate with valid data"""
    ini_account.number = number
    ini_account.amount = amount

    with pytest.raises((exceptions.AccountInvalidAmountException, exceptions.AccountInvalidNumberException)) as e:
        ini_account.validate()
    
    assert e.value.code == HTTPStatus.UNPROCESSABLE_ENTITY
    assert e.match(r'^(O número da conta deve conter)|(O valor não pode ser menor que 0.)')
