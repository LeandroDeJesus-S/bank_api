from datetime import timedelta, timezone, datetime
from http import HTTPStatus
import pytest
from core.domain_rules import domain_rules
from core import exceptions


@pytest.mark.parametrize(
    "username",
    ["valid user", "valid_user", "user123", "123user"]
)
def test_validate_username_success(ini_user, username):
    ini_user.username = username
    try:
        ini_user.validate_username()
    except exceptions.UserInvalidUsernameException as e:
        pytest.fail(f"username invalid: {e.detail}")


@pytest.mark.parametrize(
    "username",
    [
        "/inv4lid username",
        "invalid-username",
        "invalid@too",
        "u" * (domain_rules.user_rules.MIN_USERNAME_SIZE - 1),
        "u" * (domain_rules.user_rules.MAX_USERNAME_SIZE + 1),
    ],
)
def test_validate_username_fail(ini_user, username):
    ini_user.username = username
    with pytest.raises(exceptions.UserInvalidUsernameException) as exc:
        ini_user.validate_username()

    assert exc.value.detail == "Invalid username."
    assert exc.value.code == HTTPStatus.UNPROCESSABLE_ENTITY


def test_validate_password_success(ini_user):
    pw = 'Stron@123'
    ini_user.password = pw
    try:
        ini_user.validate_password()
    except exceptions.UserWeakPasswordException as e:
        pytest.fail(e.detail)


@pytest.mark.parametrize('pw', ['senha213', 'senha', '12345678'])
def test_validate_password_fail(ini_user, pw):
    ini_user.password = pw
    with pytest.raises(exceptions.UserWeakPasswordException) as exc:
        ini_user.validate_password()
    
    assert exc.value.detail == "Password too weak."
    assert exc.value.code == HTTPStatus.UNPROCESSABLE_ENTITY


def test_validate_first_name_success(ini_user):
    ini_user.first_name = 'Joares'
    try:
        ini_user.validate_first_name()
    except exceptions.UserInvalidNameException as exc:
        pytest.fail(exc.detail)    


@pytest.mark.parametrize(
    'fname',
    [
        '1nvalid',
        'inv@lid',
        'invalid ',
        ' invalid',
        'in_valid',
        'i' * (domain_rules.user_rules.MIN_FIRSTNAME_SIZE - 1),
        'i' * (domain_rules.user_rules.MAX_FIRSTNAME_SIZE + 1)
    ]
)
def test_validate_first_name_fail(ini_user, fname):
    ini_user.first_name = fname
    with pytest.raises(exceptions.UserInvalidNameException) as e:
        ini_user.validate_first_name()
    
    assert e.value.detail == "Invalid first name."
    assert e.value.code == HTTPStatus.UNPROCESSABLE_ENTITY


def test_validate_last_name_success(ini_user):
    ini_user.last_name = 'Santos Silva'
    try:
        ini_user.validate_last_name()
    except exceptions.UserInvalidNameException as exc:
        pytest.fail(exc.detail)  


@pytest.mark.parametrize('lname', ['invalid_lastname', 'l4stname', 'santos-silva'])
def test_validate_last_name_fail(ini_user, lname):
    ini_user.last_name = lname
    with pytest.raises(exceptions.UserInvalidNameException) as e:
        ini_user.validate_last_name()
    
    assert e.value.detail == "Invalid last name."
    assert e.value.code == HTTPStatus.UNPROCESSABLE_ENTITY


def test_validate_cpf_success(ini_user):
    ini_user.cpf = '911.550.730-02'
    try:
        ini_user.validate_cpf()
    except exceptions.UserInvalidCPFException as e:
        pytest.fail(e.detail)


def test_validate_cpf_fail(ini_user):
    ini_user.cpf = '911.550.730-03'
    with pytest.raises(exceptions.UserInvalidCPFException) as e:
        ini_user.validate_cpf()
    
    assert e.value.detail == "Invalid CPF"
    assert e.value.code == HTTPStatus.UNPROCESSABLE_ENTITY


valid_dates = [
    datetime.now(timezone.utc).date() - timedelta(days=domain_rules.user_rules.MIN_USER_AGE * 365),
    datetime.now(timezone.utc).date() - timedelta(days=domain_rules.user_rules.MAX_USER_AGE * 365),
]
@pytest.mark.parametrize('date', valid_dates)
def test_validate_birthdate_success(ini_user, date):
    ini_user.birthdate = date
    try:
        ini_user.validate_birthdate()
    except exceptions.UserInvalidAgeException as e:
        pytest.fail(e.detail)


invalid_dates = [
    datetime.now().date() - timedelta(days=(domain_rules.user_rules.MIN_USER_AGE - 1) * 365),
    datetime.now().date() - timedelta(days=(domain_rules.user_rules.MAX_USER_AGE + 1) * 365),
]
@pytest.mark.parametrize('date', invalid_dates)
def test_validate_birthdate_fail(ini_user, date):
    ini_user.birthdate = date
    min_age = domain_rules.user_rules.MIN_USER_AGE
    max_age = domain_rules.user_rules.MAX_USER_AGE

    with pytest.raises(exceptions.UserInvalidAgeException) as e:
        ini_user.validate_birthdate()

    assert e.value.detail == f"The age must be between {min_age} and {max_age} years."
