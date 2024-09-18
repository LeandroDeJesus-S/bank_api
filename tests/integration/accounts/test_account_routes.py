from http import HTTPStatus

import pytest

from core.exceptions import DatabaseException


async def test_create_account_success(client, dumb_user, dumb_account_type, dumb_token):
    """test create account with valid data"""
    data = {
        'number': '0123456789',
        'amount': '0.0',
        'user_id': dumb_user.id,
        'account_type_id': dumb_account_type.id,
    }
    
    response = await client.post('/accounts/', json=data, headers=dumb_token)
    resp_data = response.json()
    print(resp_data)
    assert response.status_code == HTTPStatus.CREATED
    assert resp_data['number'] == data['number']
    assert resp_data['user_id'] == data['user_id']
    assert resp_data['account_type_id'] == data['account_type_id']


async def test_create_account_non_existent_user_id(client, dumb_user, dumb_account_type, dumb_token):
    """test create account with invalid user id"""
    data = {
        'number': '0123456789',
        'amount': '0.0',
        'user_id': 333,
        'account_type_id': dumb_account_type.id,
    }

    response = await client.post('/accounts/', json=data, headers=dumb_token)
    resp_data = response.json()

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    assert resp_data['detail'] == 'invalid user id'


async def test_create_account_non_existent_type_id(client, dumb_user, dumb_account_type, dumb_token):
    """test create account with invalid account type id"""
    data = {
        'number': '0123456789',
        'amount': '0.0',
        'user_id': dumb_user.id,
        'account_type_id': 555,
    }
    
    response = await client.post('/accounts/', json=data, headers=dumb_token)
    resp_data = response.json()

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    assert resp_data['detail'] == 'invalid account type id'


async def test_create_account_duplicated_number(client, dumb_user, dumb_account, dumb_account_type, dumb_token):
    """test create account with a duplicated number"""
    data = {
        'number': dumb_account.number,
        'amount': '0.0',
        'user_id': dumb_user.id,
        'account_type_id': dumb_account_type.id,
    }
    
    response = await client.post('/accounts/', json=data, headers=dumb_token)
    resp_data = response.json()

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    assert resp_data['detail'] == 'account number already exists.'


async def test_create_account_to_diff_user(client, dumb_user, five_dumb_users, dumb_account_type, dumb_token):
    """test create account to a user different of the user authenticated"""
    data = {
        'number': '0123456789',
        'amount': '0.0',
        'user_id': 5,
        'account_type_id': dumb_account_type.id,
    }
    
    response = await client.post('/accounts/', json=data, headers=dumb_token)
    resp_data = response.json()

    assert response.status_code == HTTPStatus.FORBIDDEN
    assert resp_data['detail'] == "You can only to create an account to yourself."


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
async def test_create_account_fail(client, dumb_user, dumb_account_type, data, dumb_token):
    """test create account with invalid data"""
    response = await client.post('/accounts/', json=data, headers=dumb_token)
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


async def test_get_account_success(client, dumb_account, dumb_token):
    """test get a account with a valid id"""
    account_id = dumb_account.id

    response = await client.get(f'/accounts/{account_id}', headers=dumb_token)
    resp_data = response.json()
    assert response.status_code == HTTPStatus.OK
    assert resp_data['number'] == dumb_account.number


async def test_get_account_with_of_a_diff_user(client, dumb_account, five_dumb_accounts, dumb_token):
    """test create account to a user different of the user authenticated"""
    account_id = 4

    response = await client.get(f'/accounts/{account_id}', headers=dumb_token)
    resp_data = response.json()
    assert response.status_code == HTTPStatus.FORBIDDEN
    assert resp_data['detail'] == "This is not your account."


async def test_get_account_non_existent_id(client, dumb_account, dumb_token):
    """test get a account with an invalid id"""
    account_id = 999

    response = await client.get(f'/accounts/{account_id}', headers=dumb_token)
    resp_data = response.json()

    assert response.status_code == HTTPStatus.NOT_FOUND
    assert resp_data['detail'] == "account not found"


async def test_get_account_when_some_validation_exception_raises(client, dumb_account, mocker, dumb_token):
    """test get a account with an invalid id"""
    mocker.patch('core.accounts.routes.AccountController.get', side_effect=DatabaseException('validation exception', code=HTTPStatus.UNPROCESSABLE_ENTITY))
    account_id = dumb_account.id

    response = await client.get(f'/accounts/{account_id}', headers=dumb_token)
    resp_data = response.json()

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    assert resp_data['detail'] == 'validation exception'


@pytest.mark.parametrize("limit,offset", [(100, 0), (2, 0), (1, 1), (2, 5)])
async def test_list_accounts_success(
    client, admin_token, five_dumb_accounts, accounts_ctrl, limit, offset, dumb_token
):
    """test list account types params"""
    all_accounts = await accounts_ctrl.all(limit, offset)
    expected_ids = [acc.id for acc in all_accounts]

    response = await client.get(
        "/accounts/", params={"limit": limit, "offset": offset}, headers=admin_token
    )
    resp_data = response.json()
    resp_ids = [d['id'] for d in resp_data]

    assert response.status_code == HTTPStatus.OK
    assert resp_ids == expected_ids


async def test_list_accounts_fail(
    client, five_dumb_accounts, mocker, admin_token
):
    """test list account types when validation exception raises"""
    mocker.patch(
        "core.accounts.routes.AccountController.query",
        side_effect=DatabaseException('fail'),
    )

    response = await client.get("/accounts/", headers=admin_token)
    resp_data = response.json()

    assert response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
    assert resp_data['detail'] == 'fail'
