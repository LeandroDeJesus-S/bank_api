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


async def test_create_role(client, role_controller):
    data = {"name": "admin"}
    response = await client.post("/auth/roles", json=data)

    role = await role_controller.get("name", "admin")
    assert response.status_code == HTTPStatus.CREATED
    assert role.name == data["name"]


async def test_create_role_duplicated(client, role_controller, dumb_role):
    data = {"name": dumb_role.name}
    response = await client.post("/auth/roles", json=data)
    resp_detail = response.json()["detail"]

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    assert resp_detail == "Role already exists."


async def test_add_user_role(client, dumb_user, dumb_role):
    data = {"user_id": dumb_user.id, "role_id": dumb_role.id}
    response = await client.post("/auth/user-roles", json=data)
    print(response.json())
    assert response.status_code == HTTPStatus.CREATED


async def test_add_user_role_duplicated(client, dumb_user, dumb_role, dumb_user_role):
    data = {
        "user_id": dumb_user_role.user_id,
        "role_id": dumb_user_role.role_id,
    }
    response = await client.post("/auth/user-roles", json=data)
    resp_detail = response.json()["detail"]

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    assert resp_detail == "The user already have this role."
