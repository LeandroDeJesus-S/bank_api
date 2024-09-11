from http import HTTPStatus
from datetime import date

import pytest
from sqlalchemy import select, insert, update, delete
from sqlalchemy.exc import SQLAlchemyError

from core.exceptions import UserDatabaseException


async def test_get_user_success(user_ctrl, dumb_user):
    """test if get_user returns the correct user"""

    where_field = "id"
    equals_to = 1

    result = await user_ctrl.get(where_field, equals_to)
    assert result.id == equals_to
    assert dict(result) == dict(dumb_user)


async def test_get_user_with_invalid_field(user_ctrl, dumb_user):
    """test if raises UserDatabaseException if a invalid field is sent"""
    where_field = "invalid"
    equals_to = 1

    with pytest.raises(UserDatabaseException) as exc:
        await user_ctrl.get(where_field, equals_to)

    assert exc.value.detail == "Invalid where_field name or type"
    assert exc.value.code == HTTPStatus.INTERNAL_SERVER_ERROR


async def test_get_user_return_none_if_not_found(user_ctrl, dumb_user):
    """test if get user return None when equals_to value not found"""
    where_field = "id"
    equals_to = 2

    result = await user_ctrl.get(where_field, equals_to)

    assert result is None


async def test_get_user_raises_user_database_exception_with_invalid_field_type(
    user_ctrl, dumb_user
):
    """test if get_user raises UserDatabaseException with an invalid type to where_field"""
    where_field = lambda: "invalid"  # noqa
    equals_to = 2

    with pytest.raises(UserDatabaseException) as exc:
        await user_ctrl.get(where_field, equals_to)

    assert exc.value.detail == "Invalid where_field name or type"
    assert exc.value.code == HTTPStatus.INTERNAL_SERVER_ERROR


async def test_get_user_raises_user_database_exception_when_database_fail_occur(
    user_ctrl, dumb_user, mocker
):
    """test if get_user raises UserDatabaseException when database exception
    occur"""
    mocker.patch("core.users.controllers.select", side_effect=SQLAlchemyError)

    where_field = "id"  # noqa
    equals_to = 1

    with pytest.raises(UserDatabaseException) as exc:
        await user_ctrl.get(where_field, equals_to)

    assert exc.match("Unexpected fail")
    assert exc.value.code == HTTPStatus.INTERNAL_SERVER_ERROR


async def test_all_return_all_users_from_db(five_dumb_users, user_ctrl):
    """test if .all returns all users correctly"""
    result = await user_ctrl.all()
    assert len(result) == 5
    assert list(range(1, 6)) == [r.id for r in result]


async def test_all_return_all_users_with_correct_limit(five_dumb_users, user_ctrl):
    """test if .all returns all users limited correctly"""
    result = await user_ctrl.all(limit=2)
    assert len(result) == 2
    assert list(range(1, 3)) == [r.id for r in result]


async def test_all_return_all_users_with_correct_offset(five_dumb_users, user_ctrl):
    """test if .all returns all users with correct offset"""
    result = await user_ctrl.all(offset=2)
    assert len(result) == 3
    assert list(range(3, 6)) == [r.id for r in result]


async def test_all_return_all_users_with_correct_limit_and_offset(
    five_dumb_users, user_ctrl
):
    """test if .all returns all users with correct limit and also offset"""
    result = await user_ctrl.all(offset=2, limit=1)
    assert len(result) == 1
    assert [3] == [r.id for r in result]


async def test_all_raises_user_database_exception_database_exception_occur(
    five_dumb_users, user_ctrl, mocker
):
    """test if .all raises UserDatabaseException if database exception occur"""
    mocker.patch("core.users.controllers.select", side_effect=SQLAlchemyError)

    with pytest.raises(UserDatabaseException) as exc:
        await user_ctrl.all(offset=2, limit=1)

    assert exc.match("Error fetching users.")
    assert exc.value.code == HTTPStatus.INTERNAL_SERVER_ERROR


@pytest.mark.parametrize(
    "limit,offset,res_cnt,lst_id", [("a", 0, 5, 5), (3, "b", 3, 3)]
)
async def test_all_when_limit_or_offset_is_not_instance_of_int(
    five_dumb_users, user_ctrl, limit, offset, res_cnt, lst_id
):
    """test if is set the default values from limit or offset if
    some of they are not instance of int"""
    result = await user_ctrl.all(limit, offset)
    last_id = result[-1].id  # pyright: ignore

    assert len(result) == res_cnt
    assert last_id == lst_id


async def test_create_success(user_ctrl):
    """test if create save the data in database with success"""
    created = await user_ctrl.create(
        id=1,
        username="test",
        password="Test@123",
        first_name="test",
        last_name="test",
        cpf="422.961.160-94",
        birthdate=date(2005, 3, 11),
    )

    user = await user_ctrl.get(where_field="id", equals_to=1)

    assert created == 1
    assert user.id == 1
    assert user.username == "test"
    assert user.cpf == "422.961.160-94"


async def test_create_raises_user_database_exception_when_field_does_not_exists(user_ctrl):
    with pytest.raises(UserDatabaseException) as e:
        await user_ctrl.create(
            id=1,
            user_name="test",
            password="Test@123",
            first_name="test",
            last_name="test",
            cpf="422.961.160-94",
            birthdate=date(2005, 3, 11),
        )
    
    assert e.value.detail == 'user_name does not exists.'
    assert e.value.code == HTTPStatus.UNPROCESSABLE_ENTITY


async def test_create_raises_user_database_exception_if_an_exception_occur(
    user_ctrl, mocker
):
    """test if raises UserDatabaseException when database exception raises"""
    mocker.patch("core.users.controllers.insert", side_effect=SQLAlchemyError)

    with pytest.raises(UserDatabaseException) as exc:
        await user_ctrl.create(
            id=1,
            username="test",
            password="Test@123",
            first_name="test",
            last_name="test",
            cpf="422.961.160-94",
            birthdate=date(2005, 3, 11),
        )

    assert exc.match("User creation fail.")
    assert exc.value.code == HTTPStatus.INTERNAL_SERVER_ERROR


async def test_update_user_return_true_if_successfully_updated(user_ctrl, dumb_user):
    """test if update_user return true when the user data is updated"""
    updated_username = 'updated_username'
    updated_fname = 'new_fname'
    updated = await user_ctrl.update_user(
        user_id=dumb_user.id,
        username=updated_username,
        first_name=updated_fname,
    )
    updated_user = await user_ctrl.get('id', dumb_user.id)

    assert updated
    assert updated_user.username == updated_username
    assert updated_user.first_name == updated_fname


async def test_update_user_return_false_with_invalid_id(user_ctrl, dumb_user):
    """test if update_user return False when the user_id does not exist"""
    updated_username = 'updated_username'
    updated = await user_ctrl.update_user(user_id=5, username=updated_username)

    assert not updated


async def test_update_user_return_false_with_invalid_id_type(user_ctrl, dumb_user):
    """test if update_user return False when the user_id is not int"""
    updated_username = 'updated_username'
    updated = await user_ctrl.update_user(user_id='1', username=updated_username)

    assert not updated


async def test_update_user_raises_user_database_exception_when_field_does_not_exists(user_ctrl, dumb_user):
    with pytest.raises(UserDatabaseException) as e:
        await user_ctrl.update_user(1, no_exists='x')

    assert e.value.code == HTTPStatus.UNPROCESSABLE_ENTITY
    assert e.value.detail == 'no_exists does not exists.'


async def test_update_user_raises_user_database_exception_when_sqlalchemy_error_occur(user_ctrl, dumb_user, mocker):
    mocker.patch('core.users.controllers.DB.execute', side_effect=SQLAlchemyError)

    with pytest.raises(UserDatabaseException) as e:
        await user_ctrl.update_user(1, username='anything')
    
    assert e.value.detail == 'User update fail.'
    assert e.value.code == HTTPStatus.INTERNAL_SERVER_ERROR


async def test_query_select(user_ctrl, five_dumb_users):
    query = select(user_ctrl._model).where(user_ctrl._model.id == 3)
    result = await user_ctrl.query(query)
    expected = await user_ctrl.get('id', 3)
    assert dict(result[0]) == dict(expected)  # type: ignore


async def test_query_insert(user_ctrl, ini_user):
    data = ini_user.__dict__.copy()
    data.pop('_sa_instance_state')

    query = insert(user_ctrl._model).values(**data)
    result = await user_ctrl.query(query)
    ins_usr = await user_ctrl.get('id', ini_user.id)
    
    assert result
    assert dict(ins_usr) == data


async def test_query_update(user_ctrl, dumb_user):
    data = {'username': 'updated'}
    query = update(user_ctrl._model).values(**data)
    result = await user_ctrl.query(query)
    up_usr = await user_ctrl.get('id', dumb_user.id)
    
    assert result
    assert up_usr.username == data["username"]


async def test_query_delete(user_ctrl, dumb_user):
    query = delete(user_ctrl._model).where(user_ctrl._model.id == dumb_user.id)
    result = await user_ctrl.query(query)
    up_usr = await user_ctrl.get('id', dumb_user.id)
    
    assert result
    assert up_usr is None


async def test_delete_user(user_ctrl, dumb_user):
    user_id = dumb_user.id
    await user_ctrl.delete_user(user_id)
    user = await user_ctrl.get('id', user_id)

    assert user is None


async def test_delete_user_when_sqlalchemy_error_raises(user_ctrl, dumb_user, mocker):
    mocker.patch('core.users.controllers.DB.execute', side_effect=SQLAlchemyError)
    user_id = dumb_user.id

    with pytest.raises(UserDatabaseException) as e:
        await user_ctrl.delete_user(user_id)

    assert e.value.detail == 'Não foi possivel concluir a operação.'
    assert e.value.code == HTTPStatus.INTERNAL_SERVER_ERROR
