from http import HTTPStatus

import pytest

from core.exceptions import UserDatabaseException


async def test_list_users_success(client, dumb_user):
    response = await client.get('/users/')
    
    result = response.json()
    expected =  [
        {
            'username': dumb_user.username,
            'first_name': dumb_user.first_name,
            'last_name': dumb_user.last_name,
            'birthdate': dumb_user.birthdate.strftime('%Y-%m-%d'),
            'id': dumb_user.id
        }
    ]
    
    assert response.status_code == HTTPStatus.OK
    assert result == expected


async def test_list_users_limit_offset(client, five_dumb_users):
    limit = 2
    offset = 1
    response = await client.get('/users/', params={'limit': limit, 'offset': offset})

    resp_user_ids = [u['id'] for u in response.json()]  # pyright: ignore[reportInvalidTypeForm]
    expected_user_ids = [2, 3]

    assert response.status_code == HTTPStatus.OK
    assert expected_user_ids == sorted(resp_user_ids)


async def test_list_users_when_validation_exception_raises(client, mocker):
    mocker.patch('core.users.routes.UserController.all', side_effect=UserDatabaseException('exception'))

    response = await client.get('/users/')
    resp_data = response.json()

    assert response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
    assert resp_data == {'detail': "exception"}


async def test_get_user(client, dumb_user):
    user_id = dumb_user.id
    response = await client.get(f'/users/{user_id}')
    
    assert response.status_code == HTTPStatus.OK
    assert response.json()['id'] == user_id  # pyright: ignore[reportInvalidTypeForm]


async def test_get_user_with_invalid_id(client):
    user_id = 'x'
    response = await client.get(f'/users/{user_id}')
    resp_msg = response.json()['detail'][0]['msg']  # type: ignore
    expected_msg = 'Input should be a valid integer, unable to parse string as an integer'

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    assert resp_msg == expected_msg


async def test_get_user_with_non_existent_id(client, dumb_user):
    user_id = 999
    response = await client.get(f'/users/{user_id}')
    resp_msg = response.json()['detail']  # type: ignore
    expected_msg = 'Usuário não encontrado.'

    assert response.status_code == HTTPStatus.NOT_FOUND
    assert resp_msg == expected_msg


async def test_get_user_when_validation_exception_raises(client, mocker):
    user_id = 1
    mocker.patch('core.users.routes.UserController.get', side_effect=UserDatabaseException('exception'))

    response = await client.get(f'/users/{user_id}')
    resp_data = response.json()

    assert response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
    assert resp_data == {'detail': "exception"}


async def test_create_user(client, ini_user):
    data = ini_user.__dict__
    data.pop('_sa_instance_state')
    data['birthdate'] = data['birthdate'].strftime('%Y-%m-%d')  # type: ignore

    response = await client.post('/users/', json=data)
    resp_data = response.json()

    data.pop('cpf')
    data.pop('password')

    assert response.status_code == HTTPStatus.CREATED
    assert resp_data == data


async def test_create_user_with_non_existent_field(client, ini_user):
    data = ini_user.__dict__.copy()
    data.pop('_sa_instance_state')

    data['invalid_field'] = 'something'  # type: ignore
    data['birthdate'] = data['birthdate'].strftime('%Y-%m-%d')  # type: ignore

    response = await client.post('/users/', json=data)
    resp_data = response.json()

    data.pop('cpf')
    data.pop('password')
    data.pop('invalid_field')

    assert response.status_code == HTTPStatus.CREATED
    assert resp_data == data


@pytest.mark.parametrize('username,cpf', [('dumb_username', '135.339.740-81'), ('username', "422.961.160-94")])
async def test_create_user_with_duplicated_cpf_and_username(client, dumb_user, cpf, username):
    data = {
        'username': username,
        'password': "Dumbuser$123",
        'first_name': "dumb",
        'last_name': "name",
        'cpf': cpf,
        'birthdate': '2005-03-11',
    }

    response = await client.post('/users/', json=data)
    resp_data = response.json()

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    assert resp_data == {'detail': "Nome de usuário ou cpf não disponível."}


async def test_create_user_when_validation_exception_raises(client, mocker):
    data = {
        'username': 'username',
        'password': "Dumbuser$123",
        'first_name': "dumb",
        'last_name': "name",
        'cpf': '135.339.740-81',
        'birthdate': '2005-03-11',
    }
    mocker.patch('core.users.routes.UserController.query', side_effect=UserDatabaseException('exception'))

    response = await client.post('/users/', json=data)
    resp_data = response.json()

    assert response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
    assert resp_data == {'detail': "exception"}


async def test_update_user(client, dumb_user):
    user_id = dumb_user.id
    data = {'username': 'updated_username'}
    response = await client.patch(f'/users/{user_id}', json=data)
    resp_data = response.json()

    assert response.status_code == HTTPStatus.OK
    assert resp_data['username'] == data['username']  # type: ignore


async def test_update_user_invalid_id(client, dumb_user):
    user_id = 'x'
    data = {'username': 'updated_username'}
    response = await client.patch(f'/users/{user_id}', json=data)
    resp_data = response.json()

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    assert resp_data['detail'][0]['msg'] == 'Input should be a valid integer, unable to parse string as an integer'  # type: ignore


async def test_update_user_non_existent_id(client):
    user_id = 1
    data = {'username': 'updated_username'}
    response = await client.patch(f'/users/{user_id}', json=data)
    resp_data = response.json()

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    assert resp_data['detail'] == 'Não foi possivél atualizar, verifique e tente novamente.'  # type: ignore


async def test_update_user_non_existent_field(client, dumb_user):
    user_id = dumb_user.id
    data = {'invalid_field': 'invalid_field'}

    response = await client.patch(f'/users/{user_id}', json=data)
    resp_data = response.json()

    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert resp_data['detail'] == 'Invalid data.'  # type: ignore


async def test_update_user_when_validation_exception_raises(client, mocker, dumb_user):
    user_id = 1
    data = {'username': 'username'}

    mocker.patch('core.users.routes.UserController.update_user', side_effect=UserDatabaseException('exception'))

    response = await client.patch(f'/users/{user_id}', json=data)
    resp_data = response.json()

    assert response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
    assert resp_data == {'detail': "exception"}


async def test_delete_user(client, dumb_user, user_ctrl):
    user_id = dumb_user.id

    response = await client.delete(f'/users/{user_id}')
    user = await user_ctrl.get('id', user_id)

    assert response.status_code == HTTPStatus.NO_CONTENT
    assert user is None


async def test_delete_user_non_existent_id(client, dumb_user, user_ctrl):
    user_id = 999

    response = await client.delete(f'/users/{user_id}')

    assert response.status_code == HTTPStatus.NO_CONTENT


async def test_delete_user_when_raises_validation_exception(client, dumb_user, user_ctrl, mocker):
    mocker.patch('core.users.routes.UserController.delete_user', side_effect=UserDatabaseException('exception', code=HTTPStatus.BAD_REQUEST))
    user_id = 1

    response = await client.delete(f'/users/{user_id}')
    resp_data = response.json()

    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert resp_data['detail'] == 'exception'  # type: ignore
