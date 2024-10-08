from datetime import date
from decimal import Decimal

from httpx import AsyncClient, ASGITransport
import pytest_asyncio as pyt
from sqlalchemy import and_, insert, select

from core.domain_rules import domain_rules
from core.settings import settings

settings.DATABASE_URI = "sqlite+aiosqlite:///test.db"

from core.database.conf import DB, Base, engine  # noqa: F401 , E402
from core.users.models import User  # noqa: F401 , E402
from core.accounts.models import AccountType, Account  # noqa: F401 , E402
from core.transactions.models import Transaction, TransactionType  # noqa: F401 , E402
from core.auth.models import Role, UserRole  # noqa: E402, F401

DUMB_USER_RAW_PW = "Dumbuser$123"


# general fixtures
@pyt.fixture(scope="session", autouse=True)
async def db_create():
    """create all tables, pass the time to tests execution and drop
    all tables when they finalize"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    await DB.connect()
    yield
    await DB.disconnect()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pyt.fixture(autouse=True)
async def db_clean(db_create):
    """clean all tables data after each test function execution"""
    for table in Base.metadata.sorted_tables:
        try:
            await DB.execute(f"DELETE FROM '{table.name}';")

        except Exception as e:
            print(f"Erro ao limpar a tabela {table.name}: {e}")


@pyt.fixture
async def client():
    """returns a non authenticated client"""
    from main import api

    transport = ASGITransport(api)
    headers = {
        "Accept": "application/json", "Content-Type": "application/json"
    }
    async with AsyncClient(
        base_url="http://test", transport=transport, headers=headers
    ) as c:
        yield c


# CONTROLLERS
@pyt.fixture
def db_ctrl():
    from core.database.controller import DatabaseController

    ctrl = DatabaseController
    return ctrl


@pyt.fixture
def user_ctrl():
    """return an instance of the user controller"""
    from core.users.controllers import UserController

    ctrl = UserController()
    return ctrl


@pyt.fixture
def jwt_controller():
    """return the instance of JWT controller"""
    from core.auth.controllers import JWTController

    ctrl = JWTController()
    return ctrl


@pyt.fixture
def password_controller():
    """return the instance of the password controller"""
    from core.auth.controllers import PasswordController

    ctrl = PasswordController()
    return ctrl


@pyt.fixture
def role_controller():
    from core.auth.controllers import RoleController

    ctrl = RoleController()
    return ctrl


@pyt.fixture
def user_role_controller():
    from core.auth.controllers import UserRoleController

    ctrl = UserRoleController()
    return ctrl


@pyt.fixture
def accounts_ctrl():
    """return the instance of the accounts controller"""
    from core.accounts.controllers import AccountController

    ctrl = AccountController()
    return ctrl


@pyt.fixture
def account_type_ctrl():
    """return the instance of the accounts controller"""
    from core.accounts.controllers import AccountTypeController

    ctrl = AccountTypeController()
    return ctrl


@pyt.fixture
def transaction_ctrl():
    """return the transaction controller"""
    from core.transactions.controllers import TransactionController

    ctrl = TransactionController()
    return ctrl


# SAMPLES
@pyt.fixture
async def dumb_user(user_ctrl):
    """creates a user in database"""
    await user_ctrl.create(
        username="dumb_username",
        password=DUMB_USER_RAW_PW,
        first_name="dumb",
        last_name="name",
        cpf="422.961.160-94",
        birthdate=date(2005, 3, 11),
    )
    return await user_ctrl.get("cpf", "422.961.160-94")


@pyt.fixture
async def admin_user(dumb_user, admin_role, user_role_controller, user_ctrl):
    """set the dumb user the admin role in database and return him"""
    await user_role_controller.create(
        user_id=dumb_user.id, role_id=admin_role.id
    )
    return await user_ctrl.get('id', dumb_user.id)


@pyt.fixture
async def dumb_account_type(account_type_ctrl):
    """creates and return an account type"""
    await account_type_ctrl.create(
        id=1,
        type="corrente",
    )
    acc_typ = await account_type_ctrl.get("id", 1)
    return acc_typ


@pyt.fixture
async def dumb_account(dumb_user, dumb_account_type, accounts_ctrl):
    """create and return an account"""
    await accounts_ctrl.create(
        number="0123456789",
        amount=Decimal("0"),
        user_id=dumb_user.id,
        account_type_id=dumb_account_type.id,
    )
    acc = await accounts_ctrl.get("number", "0123456789")
    return acc


@pyt.fixture
async def dumb_account_10amount(dumb_user, dumb_account_type, accounts_ctrl):
    """create and return an account for the dumb_user with 10 of amount"""
    await accounts_ctrl.create(
        number="0123456759",
        amount=Decimal("10"),
        user_id=dumb_user.id,
        account_type_id=dumb_account_type.id,
    )
    acc = await accounts_ctrl.get("number", "0123456759")
    return acc


@pyt.fixture
async def admin_token(client, admin_user):
    """returns a client with admin role."""
    response = await client.post(
        "/auth/login",
        json={
            "username": admin_user.username,
            "password": DUMB_USER_RAW_PW,
        },
    )
    access_token = response.json()["access_token"]
    return {'Authorization': f'Bearer {access_token}'}


@pyt.fixture
async def dumb_token(client, dumb_user):
    response = await client.post(
        "/auth/login",
        json={
            "username": dumb_user.username,
            "password": DUMB_USER_RAW_PW,
        },
    )
    access_token = response.json()["access_token"]
    return {'Authorization': f'Bearer {access_token}'}


@pyt.fixture
async def five_dumb_users(user_ctrl, faker):
    """create five random users in database"""
    cpfs = [
        "910.833.160-01",
        "660.135.320-52",
        "27988259032",
        "26901293020",
        "370.671.640-28",
    ]
    for i in range(5):
        await user_ctrl.create(
            username=faker.user_name()[: domain_rules.user_rules.MAX_USERNAME_SIZE],
            password=faker.password(),
            first_name=faker.first_name(),
            last_name=faker.last_name(),
            cpf=cpfs[i],
            birthdate=faker.date_of_birth(
                maximum_age=domain_rules.user_rules.MAX_USER_AGE - 1,
                minimum_age=domain_rules.user_rules.MIN_USER_AGE,
            ),
        )


@pyt.fixture
async def five_dumb_roles(role_controller, faker):
    """create five dumb roles"""
    roles = [{"name": faker.word()} for _ in range(5)]
    stmt = insert(role_controller.model).values(roles)
    await role_controller.query(stmt)


@pyt.fixture
async def five_dumb_accounts(
    five_dumb_users, dumb_account_type, accounts_ctrl, user_ctrl, faker
):
    """create five dumb accounts"""
    all_users = await user_ctrl.all()
    values = [
        {
            "number": f"{faker.random_number(10, fix_len=True)}",
            "amount": Decimal("0"),
            "user_id": user.id,
            "account_type_id": dumb_account_type.id,
        }
        for user in all_users
    ]

    stmt = insert(accounts_ctrl.model).values(values)
    await accounts_ctrl.query(stmt)


@pyt.fixture
async def five_dumb_account_types(account_type_ctrl, faker):
    """creates five dumb account types"""
    stmt = insert(account_type_ctrl.model).values(
        [{"type": faker.word()} for i in range(5)]
    )
    await account_type_ctrl.query(stmt)


@pyt.fixture
async def five_dumb_transactions(transaction_ctrl, dumb_account):
    """create five dumb transactions"""
    transactions = [
        {
            "from_account_id": dumb_account.id,
            "to_account_id": dumb_account.id,
            "type": TransactionType.deposit,
            "value": Decimal("10"),
        }
        for _ in range(5)
    ]
    stmt = insert(transaction_ctrl.model).values(transactions)
    await transaction_ctrl.query(stmt)


@pyt.fixture
async def two_dumb_accounts_10amount(
    five_dumb_users, dumb_account_type, accounts_ctrl, user_ctrl, faker
):
    """create two dumb accounts for two dumb users with 10 of amount"""
    all_users = await user_ctrl.all(limit=2)
    stmt = insert(accounts_ctrl.model).values(
        [
            {
                "number": f"{faker.random_number(10, fix_len=True)}",
                "amount": Decimal("10"),
                "user_id": user.id,
                "account_type_id": dumb_account_type.id,
            }
            for user in all_users
        ]
    )
    await accounts_ctrl.query(stmt)


@pyt.fixture
async def dumb_role(role_controller):
    """create and return a role"""
    await role_controller.create(
        name="dumb",
    )
    role = await role_controller.get("name", "dumb")
    return role


@pyt.fixture
async def dumb_user_role(user_role_controller, dumb_role, dumb_user):
    """create and return a user role"""
    await user_role_controller.create(user_id=dumb_user.id, role_id=dumb_role.id)
    stmt = select(user_role_controller.model).where(
        and_(
            user_role_controller.model.user_id == dumb_user.id,
            user_role_controller.model.role_id == dumb_role.id,
        )
    )
    role = await user_role_controller.query(stmt)
    return role[0]


@pyt.fixture
async def admin_role(role_controller):
    await role_controller.create(name="admin")
    role = await role_controller.get("name", "admin")
    return role


@pyt.fixture
async def client_role(role_controller):
    await role_controller.create(name="client")
    role = await role_controller.get("id", 1)
    return role


@pyt.fixture
def ini_user():
    """returns a initialized user model instance with valid data"""
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
def ini_account(dumb_account_type, dumb_user):
    """returns a initialized user model instance with valid data"""
    usr = Account(
        id=1,
        number="0123456789",
        amount=Decimal("0"),
        user_id=dumb_user.id,
        account_type_id=dumb_account_type.id,
    )
    return usr


@pyt.fixture
def ini_account_type():
    """returns a initialized user model instance with valid data"""
    usr = AccountType(id=1, type="corrente")
    return usr
