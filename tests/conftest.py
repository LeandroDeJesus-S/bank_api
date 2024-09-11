from datetime import date

from faker import Faker
from httpx import AsyncClient, ASGITransport
import pytest_asyncio as pyt

from core.database import DB, Base, engine
from core.auth.controllers import JWTController, PasswordController
from core.users.controllers import UserController
from core.domain_rules import domain_rules
from core.users.models import User
from core.settings import settings


@pyt.fixture
def jwt_controller():
    """return the instance of JWT controller"""
    ctrl = JWTController(secret_key="secret", algorithm="HS256", expiration_minutes=1)
    return ctrl


@pyt.fixture
def password_controller():
    """return the instance of the password controller"""
    ctrl = PasswordController()
    return ctrl


@pyt.fixture
def user_ctrl():
    """return an instance of the user controller"""
    ctrl = UserController()
    return ctrl


@pyt.fixture(scope="session", autouse=True)
async def db_create():
    """create all tables, pass the time to tests execution and drop
    all tables when they finalize"""
    from core.users import models
    from core.accounts import models

    settings.DATABASE_URI = 'sqlite:///:memory:'
    Base.metadata.create_all(engine)
    await DB.connect()
    yield
    await DB.disconnect()
    Base.metadata.drop_all(engine)


@pyt.fixture(scope="function", autouse=True)
async def db_clean():
    """clean all tables data after each test function execution"""
    for table in Base.metadata.sorted_tables:
        await DB.execute(f"DELETE FROM {table.name};")


@pyt.fixture
async def dumb_user(user_ctrl):
    await user_ctrl.create(
        id=1,
        username="dumb_username",
        password="Dumbuser$123",
        first_name="dumb",
        last_name="name",
        cpf="422.961.160-94",
        birthdate=date(2005, 3, 11),
    )
    return await user_ctrl.get("id", 1)


@pyt.fixture
async def five_dumb_users(user_ctrl):
    f = Faker()
    cpfs = [
        "422.961.160-94",
        "660.135.320-52",
        "27988259032",
        "26901293020",
        "370.671.640-28",
    ]
    for i in range(5):
        await user_ctrl.create(
            id=i + 1,
            username=f.user_name(),
            password=f.password(),
            first_name=f.first_name(),
            last_name=f.last_name(),
            cpf=cpfs[i],
            birthdate=f.date_of_birth(
                maximum_age=domain_rules.user_rules.MAX_USER_AGE - 1,
                minimum_age=domain_rules.user_rules.MIN_USER_AGE,
            ),
        )


@pyt.fixture
def ini_user():
    usr = User(
        id=1,
        username="dumb_username",
        password="Strong@pass213",
        first_name="dumb",
        last_name="name",
        cpf="422.961.160-94",
        birthdate=date(2005, 3, 11),
    )
    return usr


@pyt.fixture
async def client():
    from main import api

    transport = ASGITransport(api)
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }
    async with AsyncClient(base_url='http://test', transport=transport, headers=headers) as c:
        yield c
