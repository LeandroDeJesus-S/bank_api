from http import HTTPStatus

import pytest


@pytest.mark.parametrize("limit,offset,expected_len", [(5, 0, 5), (5, 2, 3), (2, 4, 1)])
async def test_list_roles(client, five_dumb_roles, limit, offset, expected_len):
    response = await client.get(
        "/auth/roles", params={"limit": limit, "offset": offset}
    )
    resp_data = response.json()

    assert response.status_code == HTTPStatus.OK
    assert len(resp_data) == expected_len


async def test_create_role(client, role_controller, admin_token):
    data = {"name": "role"}
    response = await client.post("/auth/roles", json=data, headers=admin_token)

    role = await role_controller.get("name", "role")
    assert response.status_code == HTTPStatus.CREATED
    assert role.name == data["name"]


async def test_create_role_duplicated(client, role_controller, dumb_role, admin_token):
    data = {"name": dumb_role.name}
    response = await client.post("/auth/roles", json=data, headers=admin_token)
    resp_detail = response.json()["detail"]

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    assert resp_detail == "Role already exists."


async def test_add_user_role(client, dumb_user, dumb_role, admin_token):
    data = {"user_id": dumb_user.id, "role_id": dumb_role.id}
    response = await client.post("/auth/user-roles", json=data, headers=admin_token)
    print(response.json())
    assert response.status_code == HTTPStatus.CREATED


async def test_add_user_role_duplicated(client, dumb_user, dumb_role, dumb_user_role, admin_token):
    data = {
        "user_id": dumb_user_role.user_id,
        "role_id": dumb_user_role.role_id,
    }
    response = await client.post("/auth/user-roles", json=data, headers=admin_token)
    resp_detail = response.json()["detail"]

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    assert resp_detail == "The user already have this role."


async def test_authenticate_success(client, dumb_user):
    data = {
        'username': dumb_user.username,
        'password': "Dumbuser$123"
    }

    response = await client.post('/auth/login', json=data)

    assert response.status_code == HTTPStatus.OK
    assert 'access_token' in response.json()



@pytest.mark.parametrize('username,password', [
    ('dumb_username', 'Wrong@123'),
    ('wrong_username', "Dumbuser$123")
])
async def test_authenticate_fail(client, dumb_user, username, password):
    data = {
        'username': username, 'password': password
    }

    response = await client.post('/auth/login', json=data)

    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert response.json()['detail'] == "Invalid credentials."
