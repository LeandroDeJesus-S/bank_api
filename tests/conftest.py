from datetime import date

from faker import Faker
from httpx import AsyncClient, ASGITransport
import pytest_asyncio as pyt

from core.domain_rules import domain_rules
from core.settings import settings

settings.DATABASE_URI = 'sqlite:///test.db'

# general fixtures
@pyt.fixture(scope='session', autouse=True)
async def db_create():
    """create all tables, pass the time to tests execution and drop
    all tables when they finalize"""
    from core.database import DB, Base, engine
    from core.users.models import User  # noqa: F401
    from core.accounts.models import AccountType, Account  # noqa: F401

    Base.metadata.create_all(engine)
    await DB.connect()
    yield
    await DB.disconnect()
    Base.metadata.drop_all(engine)


@pyt.fixture(autouse=True)
async def db_clean(db_create):
    """clean all tables data after each test function execution"""
    from core.database import DB, Base

    for table in Base.metadata.sorted_tables:
        try:
            await DB.execute(f"DELETE FROM {table.name};")

        except Exception as e:
            print(f"Erro ao limpar a tabela {table.name}: {e}")


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


# user fixtures
@pyt.fixture
def user_ctrl():
    """return an instance of the user controller"""
    from core.users.controllers import UserController
    ctrl = UserController()
    return ctrl


@pyt.fixture
async def dumb_user(user_ctrl):
    """creates a user in database"""
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
def ini_user():
    """returns a initialized user model instance"""
    from core.users.models import User

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
async def five_dumb_users(user_ctrl):
    """create five random users in database"""    
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


# auth fixtures
@pyt.fixture
def jwt_controller():
    """return the instance of JWT controller"""
    from core.auth.controllers import JWTController
    ctrl = JWTController(secret_key="secret", algorithm="HS256", expiration_minutes=1)
    return ctrl


@pyt.fixture
def password_controller():
    """return the instance of the password controller"""
    from core.auth.controllers import PasswordController
    ctrl = PasswordController()
    return ctrl
