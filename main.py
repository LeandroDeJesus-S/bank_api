from contextlib import asynccontextmanager

from fastapi import FastAPI

from core.users import routes as user_routes
from core.database import Base, DB, engine


@asynccontextmanager
async def lifespan(app):
    import core.users.models as user_models
    import core.accounts.models as acct_models

    Base.metadata.create_all(engine)
    await DB.connect()
    yield
    await DB.disconnect()


api = FastAPI(lifespan=lifespan)
api.include_router(user_routes.router)
