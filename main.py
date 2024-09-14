from contextlib import asynccontextmanager

from fastapi import FastAPI

from core.users import routes as user_routes
from core.accounts import routes as account_routes
from core.database.conf import Base, DB, engine


@asynccontextmanager
async def lifespan(app):
    import core.users.models as user_models
    import core.accounts.models as acct_models

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    await DB.connect()
    yield
    await DB.disconnect()


api = FastAPI(lifespan=lifespan)
api.include_router(user_routes.router)
api.include_router(account_routes.router)
