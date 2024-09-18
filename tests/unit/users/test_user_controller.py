from datetime import date
from http import HTTPStatus

from core.exceptions import DatabaseException

import pytest
from sqlalchemy.exc import SQLAlchemyError


async def test_create_success(user_ctrl):
    data = {
        'username': 'test',
        'first_name': 'test',
        'last_name': 'test',
        'password': 'Password@01',
        'cpf': '953.447.200-09',
        'birthdate': date(2002, 5, 3),

    }
    
    created = await user_ctrl.create(**data)
    user_created = await user_ctrl.get('username', data['username'])
    
    assert created
    assert user_created.cpf == data['cpf']


async def test_create_hashes_password(user_ctrl):
    data = {
        'username': 'test',
        'first_name': 'test',
        'last_name': 'test',
        'password': 'Password@01',
        'cpf': '953.447.200-09',
        'birthdate': date(2002, 5, 3),
    }
    
    await user_ctrl.create(**data)
    user_created = await user_ctrl.get('username', data['username'])
    
    assert user_created.password != data['password']
    assert user_created.password.startswith('hash::')


async def test_create_when_sqlalchemy_error(user_ctrl, mocker):
    mocker.patch('core.users.controllers.insert', side_effect=SQLAlchemyError)
    data = {
        'username': 'test',
        'first_name': 'test',
        'last_name': 'test',
        'password': 'Password@01',
        'cpf': '953.447.200-09',
        'birthdate': date(2002, 5, 3),
    }
    
    with pytest.raises(DatabaseException) as e:
        await user_ctrl.create(**data)
    
    assert e.value.code == HTTPStatus.INTERNAL_SERVER_ERROR
    assert e.value.detail == 'Creation fail.'


async def test_update_hashes_the_password(user_ctrl, dumb_user):
    await user_ctrl.update_(
        id=dumb_user.id,
        password='Changed@01'
    )

    updated_user = await user_ctrl.get('id', dumb_user.id)
    assert updated_user.password.startswith('hash::')


async def test_update_with_not_int_id(user_ctrl, dumb_user):
    updated = await user_ctrl.update_(
        id=str(dumb_user.id),
        password='Changed@01'
    )

    assert not updated
