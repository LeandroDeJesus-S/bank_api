from http import HTTPStatus

import pytest
from sqlalchemy import select

from core.exceptions import AccountDatabaseException


async def test_create_account_type_success(client):
    """test create account route with valid data"""
    data = {"type": "poupanca"}

    response = await client.post("/accounts/types", json=data)
    resp_data = response.json()

    assert response.status_code == HTTPStatus.CREATED
    assert resp_data["type"] == data["type"]


@pytest.mark.parametrize(
    "param,value",
    [
        ("type", "conta poupanca"),
        ("type", "poupança"),
        ("type", ""),
        ("invalid", "conta"),
        ("type", 1),
    ],
)
async def test_create_account_type_fail(client, param, value):
    """test create account route with invalid data"""
    data = {param: value}

    response = await client.post("/accounts/types", json=data)

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


async def test_create_account_type_duplicated(client, dumb_account_type):
    """test create account route with invalid data"""
    data = {"type": dumb_account_type.type}

    response = await client.post("/accounts/types", json=data)
    resp_data = response.json()

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    assert resp_data["detail"] == "account type already exists."


@pytest.mark.parametrize("limit,offset", [(100, 0), (2, 0), (1, 1), (2, 5)])
async def test_list_account_types_success(
    client, five_dumb_account_types, accounts_ctrl, limit, offset
):
    """test list account types params"""
    stmt = select(accounts_ctrl._account_type_model).limit(limit).offset(offset)
    all_acc_types = await accounts_ctrl.query(stmt)
    expected_data = [dict(acc_t) for acc_t in all_acc_types]

    response = await client.get(
        "/accounts/types", params={"limit": limit, "offset": offset}
    )
    resp_data = response.json()

    assert response.status_code == HTTPStatus.OK
    assert resp_data == expected_data


async def test_list_account_types_fail(
    client, five_dumb_account_types, accounts_ctrl, mocker
):
    """test list account types when validation exception raises"""
    mocker.patch(
        "core.accounts.routes.AccountsController.query",
        side_effect=AccountDatabaseException('fail'),
    )

    response = await client.get("/accounts/types")
    resp_data = response.json()

    assert response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
    assert resp_data['detail'] == 'fail'
