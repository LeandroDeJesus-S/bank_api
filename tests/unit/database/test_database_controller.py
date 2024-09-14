from http import HTTPStatus
from datetime import date

import pytest
from sqlalchemy import select, insert, update, delete
from sqlalchemy.exc import SQLAlchemyError

from core.users.models import User
from core.exceptions import DatabaseException


async def test_get_success(db_ctrl, dumb_user):
    """test get with valid user"""
    ctrl = db_ctrl(User)
    user = await ctrl.get(where_field='id', equals_to=dumb_user.id)
    
    assert dict(user) == dict(dumb_user)


async def test_get_with_invalid_field(db_ctrl, dumb_user):
    """test if raises DatabaseException if a invalid field is sent"""
    where_field = "invalid"
    equals_to = 1

    with pytest.raises(DatabaseException) as exc:
        await db_ctrl(User).get(where_field, equals_to)

    assert exc.value.detail == f"`{User.__tablename__}` has no field `{where_field}`."
    assert exc.value.code == HTTPStatus.UNPROCESSABLE_ENTITY


async def test_get_return_none_if_not_found(db_ctrl, dumb_user):
    """test if get return None when equals_to value not found"""
    where_field = "id"
    equals_to = 2

    result = await db_ctrl(User).get(where_field, equals_to)

    assert result is None


async def test_get_raises_database_exception_when_database_fail_occur(
    db_ctrl, dumb_user, mocker
):
    """test if get_user raises DatabaseException when database exception
    occur"""
    mocker.patch("core.database.controller.select", side_effect=SQLAlchemyError)

    where_field = "id"  # noqa
    equals_to = 1

    with pytest.raises(DatabaseException) as exc:
        await db_ctrl(User).get(where_field, equals_to)

    assert exc.value.detail == f"Unexpected fail fetching `{User.__tablename__}`"
    assert exc.value.code == HTTPStatus.INTERNAL_SERVER_ERROR


async def test_all_return_all_data_from_db(five_dumb_users, db_ctrl):
    """test if .all returns all data correctly"""
    result = await db_ctrl(User).all()
    assert len(result) == 5
    assert list(range(1, 6)) == [r.id for r in result]


async def test_all_return_all_data_with_correct_limit(five_dumb_users, db_ctrl):
    """test if .all returns all data limited correctly"""
    result = await db_ctrl(User).all(limit=2)
    assert len(result) == 2
    assert list(range(1, 3)) == [r.id for r in result]


async def test_all_return_all_data_with_correct_offset(five_dumb_users, db_ctrl):
    """test if .all returns all data with correct offset"""
    result = await db_ctrl(User).all(offset=2)
    assert len(result) == 3
    assert list(range(3, 6)) == [r.id for r in result]


async def test_all_return_all_data_with_correct_limit_and_offset(
    five_dumb_users, db_ctrl
):
    """test if .all returns all data with correct limit and also offset"""
    result = await db_ctrl(User).all(offset=2, limit=1)
    assert len(result) == 1
    assert [3] == [r.id for r in result]


async def test_all_raises_database_exception_database_exception_occur(
    five_dumb_users, db_ctrl, mocker
):
    """test if .all raises DatabaseException if database exception occur"""
    mocker.patch("core.database.controller.select", side_effect=SQLAlchemyError)

    with pytest.raises(DatabaseException) as exc:
        await db_ctrl(User).all(offset=2, limit=1)

    assert exc.match("Error fetching data.")
    assert exc.value.code == HTTPStatus.INTERNAL_SERVER_ERROR


@pytest.mark.parametrize(
    "limit,offset,res_cnt,lst_id", [("a", 0, 5, 5), (3, "b", 3, 3)]
)
async def test_all_when_limit_or_offset_is_not_instance_of_int(
    five_dumb_users, db_ctrl, limit, offset, res_cnt, lst_id
):
    """test if is set the default values from limit or offset if
    some of they are not instance of int"""
    result = await db_ctrl(User).all(limit, offset)
    last_id = result[-1].id  # pyright: ignore

    assert len(result) == res_cnt
    assert last_id == lst_id


async def test_create_success(db_ctrl):
    """test if create save the data in database with success"""
    created = await db_ctrl(User).create(
        id=1,
        username="test",
        password="Test@123",
        first_name="test",
        last_name="test",
        cpf="422.961.160-94",
        birthdate=date(2005, 3, 11),
    )

    user = await db_ctrl(User).get(where_field="id", equals_to=1)

    assert created == 1
    assert user.id == 1
    assert user.username == "test"
    assert user.cpf == "422.961.160-94"


async def test_create_raises_database_exception_when_field_does_not_exists(db_ctrl):
    with pytest.raises(DatabaseException) as e:
        await db_ctrl(User).create(
            id=1,
            user_name="test",
            password="Test@123",
            first_name="test",
            last_name="test",
            cpf="422.961.160-94",
            birthdate=date(2005, 3, 11),
        )
    
    assert e.value.detail == "`user` has no field `user_name`."
    assert e.value.code == HTTPStatus.UNPROCESSABLE_ENTITY


async def test_create_raises_user_database_exception_if_an_exception_occur(
    db_ctrl, mocker
):
    """test if raises DatabaseException when database exception raises"""
    mocker.patch("core.database.controller.insert", side_effect=SQLAlchemyError)

    with pytest.raises(DatabaseException) as exc:
        await db_ctrl(User).create(
            id=1,
            username="test",
            password="Test@123",
            first_name="test",
            last_name="test",
            cpf="422.961.160-94",
            birthdate=date(2005, 3, 11),
        )

    assert exc.match("Creation fail.")
    assert exc.value.code == HTTPStatus.INTERNAL_SERVER_ERROR


async def test_update_return_true_if_successfully_updated(db_ctrl, dumb_user):
    """test if update_user return true when the user data is updated"""
    updated_username = 'updated_username'
    updated_fname = 'new_fname'
    updated = await db_ctrl(User).update_(
        id=dumb_user.id,
        username=updated_username,
        first_name=updated_fname,
    )
    updated_user = await db_ctrl(User).get('id', dumb_user.id)

    assert updated
    assert updated_user.username == updated_username
    assert updated_user.first_name == updated_fname


async def test_update_return_false_with_invalid_id(db_ctrl, dumb_user):
    """test if update_ return False when the id does not exist"""
    updated_username = 'updated_username'
    updated = await db_ctrl(User).update_(id=5, username=updated_username)

    assert not updated


async def test_update_return_false_with_invalid_id_type(db_ctrl, dumb_user):
    """test if update_ return False when the id is not int"""
    updated_username = 'updated_username'
    updated = await db_ctrl(User).update_(id='1', username=updated_username)

    assert not updated


async def test_update_user_raises_database_exception_when_field_does_not_exists(db_ctrl, dumb_user):
    with pytest.raises(DatabaseException) as e:
        await db_ctrl(User).update_(1, no_exists='x')

    assert e.value.code == HTTPStatus.UNPROCESSABLE_ENTITY
    assert e.value.detail == f"`{User.__tablename__}` has no field `no_exists`."


async def test_update_raises_database_exception_when_sqlalchemy_error_occur(db_ctrl, dumb_user, mocker):
    mocker.patch('core.database.controller.DB.execute', side_effect=SQLAlchemyError)

    with pytest.raises(DatabaseException) as e:
        await db_ctrl(User).update_(1, username='anything')
    
    assert e.value.detail == 'Update fail.'
    assert e.value.code == HTTPStatus.INTERNAL_SERVER_ERROR


async def test_query_select(db_ctrl, five_dumb_users):
    query = select(User).where(User.id == 3)
    result = await db_ctrl(User).query(query)
    expected = await db_ctrl(User).get('id', 3)
    assert dict(result[0]) == dict(expected)  # type: ignore


async def test_query_insert(db_ctrl, ini_user):
    data = ini_user.__dict__.copy()
    data.pop('_sa_instance_state')

    query = insert(User).values(**data)
    result = await db_ctrl(User).query(query)
    ins_usr = await db_ctrl(User).get('id', ini_user.id)
    
    assert result
    assert dict(ins_usr) == data


async def test_query_update(db_ctrl, dumb_user):
    data = {'username': 'updated'}
    query = update(User).values(**data)
    result = await db_ctrl(User).query(query)
    up_usr = await db_ctrl(User).get('id', dumb_user.id)
    
    assert result
    assert up_usr.username == data["username"]


async def test_query_delete(db_ctrl, dumb_user):
    query = delete(User).where(User.id == dumb_user.id)
    result = await db_ctrl(User).query(query)
    up_usr = await db_ctrl(User).get('id', dumb_user.id)
    
    assert result
    assert up_usr is None


async def test_delete_user(db_ctrl, dumb_user):
    user_id = dumb_user.id
    await db_ctrl(User).delete_(user_id)
    user = await db_ctrl(User).get('id', user_id)

    assert user is None


async def test_delete_when_sqlalchemy_error_raises(db_ctrl, dumb_user, mocker):
    mocker.patch('core.database.controller.DB.execute', side_effect=SQLAlchemyError)
    user_id = dumb_user.id

    with pytest.raises(DatabaseException) as e:
        await db_ctrl(User).delete_(user_id)

    assert e.value.detail == 'Delete operation fail.'
    assert e.value.code == HTTPStatus.INTERNAL_SERVER_ERROR


def test_raise_attr_error_if_model_is_no_sent(db_ctrl):
    with pytest.raises(AttributeError) as e:
        db_ctrl()
    
    assert e.value.args[0] == "the `model` argument must be expecified."


def test_model_property_return_the_model_attr(db_ctrl):
    ctrl = db_ctrl(User)
    assert ctrl.model is ctrl._model