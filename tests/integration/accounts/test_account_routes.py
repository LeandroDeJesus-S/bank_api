from http import HTTPStatus

import pytest

from core.exceptions import DatabaseException

async def test_create_account_success(client, dumb_user, dumb_account_type):
    """test create account with valid data"""
    data = {
        'number': '0123456789',
        'amount': '0.0',
        'user_id': dumb_user.id,
        'account_type_id': dumb_account_type.id,
    }
    
    response = await client.post('/accounts/', json=data)
    resp_data = response.json()

    assert response.status_code == HTTPStatus.CREATED
    assert resp_data['number'] == data['number']
    assert resp_data['user_id'] == data['user_id']
    assert resp_data['account_type_id'] == data['account_type_id']


async def test_create_account_non_extistent_user_id(client, dumb_user, dumb_account_type):
    """test create account with invalid user id"""
    data = {
        'number': '0123456789',
        'amount': '0.0',
        'user_id': 333,
        'account_type_id': dumb_account_type.id,
    }
    
    response = await client.post('/accounts/', json=data)
    resp_data = response.json()

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    assert resp_data['detail'] == 'invalid user id'


async def test_create_account_non_extistent_type_id(client, dumb_user, dumb_account_type):
    """test create account with invalid account type id"""
    data = {
        'number': '0123456789',
        'amount': '0.0',
        'user_id': dumb_user.id,
        'account_type_id': 555,
    }
    
    response = await client.post('/accounts/', json=data)
    resp_data = response.json()

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    assert resp_data['detail'] == 'invalid account type id'


async def test_create_account_duplicated_number(client, dumb_user, dumb_account, dumb_account_type):
    """test create account with a duplicated number"""
    data = {
        'number': dumb_account.number,
        'amount': '0.0',
        'user_id': dumb_user.id,
        'account_type_id': dumb_account_type.id,
    }
    
    response = await client.post('/accounts/', json=data)
    resp_data = response.json()

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    assert resp_data['detail'] == 'account number already exists.'


invalid_account_cases = [
    {
        'number': '01234567890',
        'amount': '0.0',
        'user_id': 1,
        'account_type_id': 1,
    },
    {
        'number': '0123456789',
        'amount': -0.01,
        'user_id': 1,
        'account_type_id': 1,
    },
    {
        'number': '0123456789',
        'amount': -0.01,
        'user_id': 111,
        'account_type_id': 1,
    },
    {
        'number': '0123456789',
        'amount': -0.01,
        'user_id': 1,
        'account_type_id': 111,
    },
]
@pytest.mark.parametrize('data', invalid_account_cases)
async def test_create_account_fail(client, dumb_user, dumb_account_type, data):
    """test create account with invalid data"""
    response = await client.post('/accounts/', json=data)
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


async def test_get_account_success(client, dumb_account):
    """test get a account with a valid id"""
    account_id = dumb_account.id

    response = await client.get(f'/accounts/{account_id}')
    resp_data = response.json()

    assert response.status_code == HTTPStatus.OK
    assert resp_data['number'] == dumb_account.number


async def test_get_account_non_existent_id(client, dumb_account):
    """test get a account with an invalid id"""
    account_id = 999

    response = await client.get(f'/accounts/{account_id}')
    resp_data = response.json()

    assert response.status_code == HTTPStatus.NOT_FOUND
    assert resp_data['detail'] == "account not found"


async def test_get_account_when_some_validation_exception_raises(client, dumb_account, mocker):
    """test get a account with an invalid id"""
    mocker.patch('core.accounts.routes.AccountController.get', side_effect=DatabaseException('validation exception', code=HTTPStatus.UNPROCESSABLE_ENTITY))
    account_id = dumb_account.id

    response = await client.get(f'/accounts/{account_id}')
    resp_data = response.json()

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    assert resp_data['detail'] == 'validation exception'


@pytest.mark.parametrize("limit,offset", [(100, 0), (2, 0), (1, 1), (2, 5)])
async def test_list_accounts_success(
    client, five_dumb_accounts, accounts_ctrl, limit, offset
):
    """test list account types params"""
    all_accounts = await accounts_ctrl.all(limit, offset)
    expected_ids = [acc.id for acc in all_accounts]

    response = await client.get(
        "/accounts/", params={"limit": limit, "offset": offset}
    )
    resp_data = response.json()
    resp_ids = [d['id'] for d in resp_data]

    assert response.status_code == HTTPStatus.OK
    assert resp_ids == expected_ids


async def test_list_accounts_fail(
    client, five_dumb_accounts, mocker
):
    """test list account types when validation exception raises"""
    mocker.patch(
        "core.accounts.routes.AccountController.query",
        side_effect=DatabaseException('fail'),
    )

    response = await client.get("/accounts/")
    resp_data = response.json()

    assert response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
    assert resp_data['detail'] == 'fail'
