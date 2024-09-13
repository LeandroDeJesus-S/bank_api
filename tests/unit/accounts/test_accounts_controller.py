from decimal import Decimal
from http import HTTPStatus

import pytest
from sqlalchemy.exc import SQLAlchemyError

from core.exceptions import AccountDatabaseException, AccountTypeInvalidException


async def test_create_account_type(accounts_ctrl):
    """test the creation of the account type with valid data"""
    acc_type = 'corrente'
    created = await accounts_ctrl.create_account_type(id=1, type=acc_type)
    acc_type_db = await accounts_ctrl.get_account_type(by='id', value=1)
    assert created
    assert acc_type_db.id == 1
    assert acc_type_db.type == acc_type


async def test_create_account_type_with_invalid_field(accounts_ctrl):
    """test the creation of the account type with non existent field"""
    with pytest.raises(AccountDatabaseException) as e:
        await accounts_ctrl.create_account_type(id=1, invalid_field='something')
    
    assert e.value.detail == '`account_type` has no attr `invalid_field`'
    assert e.value.code == HTTPStatus.UNPROCESSABLE_ENTITY


@pytest.mark.parametrize('type_', ['inv4lid', 'in_valid', 'in valid', 'in-valid'])
async def test_create_account_type_with_invalid_type_field_pattern(accounts_ctrl, type_):
    """test the creation of the account type with not only letters"""
    with pytest.raises(AccountTypeInvalidException) as e:
        await accounts_ctrl.create_account_type(type=type_)
    
    assert e.value.detail == 'O tipo da conta deve conter apenas letras.'
    assert e.value.code == HTTPStatus.UNPROCESSABLE_ENTITY


async def test_create_account_type_when_raises_sqlalchemy_error(accounts_ctrl, mocker):
    """test the creation of the account type when an sqlalchemy error occur"""
    mocker.patch('core.accounts.controllers.DB.execute', side_effect=SQLAlchemyError)

    with pytest.raises(AccountDatabaseException) as e:
        await accounts_ctrl.create_account_type(type='any')
    
    assert e.value.detail == 'Something went wrong creating the account type.'
    assert e.value.code == HTTPStatus.INTERNAL_SERVER_ERROR


async def test_get_account_type_success(accounts_ctrl, dumb_account_type):
    """test get_account_type with valid data"""
    id = dumb_account_type.id
    type = dumb_account_type.type

    by_id = await accounts_ctrl.get_account_type(by='id', value=id)
    by_type = await accounts_ctrl.get_account_type(by='type', value=type)
    
    assert by_id.id == id and by_id.type == type
    assert by_type.id == id and by_type.type == type


async def test_get_account_type_with_non_existent_id(accounts_ctrl, dumb_account_type):
    """test get_account_type with an id that does not exists"""
    id = 999
    acc_typ = await accounts_ctrl.get_account_type(by='id', value=id)
    
    assert acc_typ is None


async def test_get_account_type_with_invalid_id_type(accounts_ctrl, dumb_account_type):
    """test get_account_type with an id that does not exists"""
    id = 1.5
    with pytest.raises(TypeError) as e:
        await accounts_ctrl.get_account_type(by='id', value=id)
    
    assert e.value.args[0] == "`value` must be instance of int or str"

async def test_get_account_type_with_invalid_by_value(accounts_ctrl, dumb_account_type):
    """test if raises attribute error when given an unavailable field to `by` arg"""
    with pytest.raises(AttributeError) as e:
        await accounts_ctrl.get_account_type(by='not_available', value=1)
    
    assert e.value.args[0] == "`by`must be `id` or `type`."

async def test_get_account_type_when_sqlalchemy_error_raises(accounts_ctrl, dumb_account_type, mocker):
    """test get_account_type when a sqlalchemy error occur"""
    mocker.patch('core.accounts.controllers.DB.fetch_one', side_effect=SQLAlchemyError)

    with pytest.raises(AccountDatabaseException) as e:
        await accounts_ctrl.get_account_type(by='id', value=1)
    
    assert e.value.detail == 'Something went wrong getting the account type.'
    assert e.value.code == HTTPStatus.INTERNAL_SERVER_ERROR


async def test_create_account_success(accounts_ctrl, dumb_account_type, dumb_user):
    """test create_account with valid data"""
    data = {
        'id': 1,
        'number': '0123456789',
        'amount': Decimal('100'),
        'user_id': dumb_user.id,
        'account_type_id': dumb_account_type.id
    }
    created = await accounts_ctrl.create_account(
        **data
    )
    account_db = await accounts_ctrl.get_account(by='id', value=1)
    assert created
    assert dict(account_db) == data


async def test_create_account_with_non_existent_field(accounts_ctrl, dumb_account_type, dumb_user):
    """test create_account with valid data"""
    data = {
        'id': 1,
        'non_exists': '0123456789',
        'amount': Decimal('100'),
        'user_id': dumb_user.id,
        'account_type_id': dumb_account_type.id
    }
    with pytest.raises(AccountDatabaseException) as e:
        await accounts_ctrl.create_account(**data)
    
    assert e.value.detail == '`account` has no attr `non_exists`'
    assert e.value.code == HTTPStatus.UNPROCESSABLE_ENTITY


async def test_create_account_when_sqlalchemy_error_raises(accounts_ctrl, dumb_account_type, dumb_user, mocker):
    """test create_account when a sqlalchemy error raises"""
    mocker.patch('core.accounts.controllers.DB.execute', side_effect=SQLAlchemyError)

    data = {
        'id': 1,
        'number': '0123456789',
        'amount': Decimal('100'),
        'user_id': dumb_user.id,
        'account_type_id': dumb_account_type.id
    }
    with pytest.raises(AccountDatabaseException) as e:
        await accounts_ctrl.create_account(**data)
    
    assert e.value.detail == 'Something went wrong creating the account.'
    assert e.value.code == HTTPStatus.INTERNAL_SERVER_ERROR


async def test_get_account_success(accounts_ctrl, dumb_account):
    """test to get account by id and number"""
    id = dumb_account.id
    number = dumb_account.number

    account_by_id = await accounts_ctrl.get_account(by='id', value=id)
    account_by_num = await accounts_ctrl.get_account(by='number', value=number)

    assert account_by_id.id == id and account_by_id.user_id == dumb_account.user_id
    assert account_by_num.number == number and account_by_num.user_id == dumb_account.user_id


async def test_get_account_by_unavaliable_field(accounts_ctrl, dumb_account):
    """test to get account by field defferent of id or number raises attribute error"""
    field = 'user_id'
    value = dumb_account.user_id

    with pytest.raises(AttributeError) as e:
        await accounts_ctrl.get_account(by=field, value=value)

    assert e.value.args[0] == 'the `by` argument value must be `id` or `number`.'


@pytest.mark.parametrize('value', [[1], (1,), 1.5])
async def test_get_account_with_invalid_value_type(accounts_ctrl, dumb_account, value):
    """test to get account with value arg type defferent of int or str raises 
    type error"""
    field = 'id'

    with pytest.raises(TypeError) as e:
        await accounts_ctrl.get_account(by=field, value=value)

    assert e.value.args[0] == 'the `value` argument must be int or str.'


async def test_get_account_when_sqlalchemy_error_raises(accounts_ctrl, dumb_account, mocker):
    """test to get account when a sqlalchemy error raises"""
    field = 'id'
    value = dumb_account.id
    mocker.patch('core.accounts.controllers.DB.fetch_one', side_effect=SQLAlchemyError)

    with pytest.raises(AccountDatabaseException) as e:
        await accounts_ctrl.get_account(by=field, value=value)

    assert e.value.detail == 'Something went wrong getting the account.'
    assert e.value.code == HTTPStatus.INTERNAL_SERVER_ERROR
