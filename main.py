from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from core.accounts import routes as account_routes
from core.database.conf import DB, Base, engine
from core.exceptions import ValidationException
from core.users import routes as user_routes
from core.transactions import routes as transaction_routes
from core.auth import routes as auth_routes


@asynccontextmanager
async def lifespan(app):
    import core.accounts.models as acct_models
    import core.users.models as user_models
    import core.transactions.models as transaction_models
    import core.auth.models as auth_models

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    await DB.connect()
    yield
    await DB.disconnect()


api = FastAPI(
    lifespan=lifespan,
    title="API de Banco",
    summary="API de banco assíncrona desenvolvida como desafio de projeto final na DIO para a formação `Python Backend Developer` .",
    description="""
Funcionalidades:
   - Gerenciamento de usuários como criação, listagem, atualização e exclusão.
   - Gerenciamento de contas e tipos de conta.
   - Uso `roles` para controle de permissões.
   - Cadastro de transações como depósitos, saques e transferências.
   - Exibição de extrato de uma ou todas as contas mostrando todas as transações realizadas.
   - Utilização de Json Web Tokens para realizar a autenticação e autorização.
"""
)


@api.exception_handler(ValidationException)
def validation_exception_handler(request: Request, exc: ValidationException):
    return JSONResponse(
        status_code=exc.code,
        content={"detail": exc.detail},
    )


api.include_router(user_routes.router)
api.include_router(account_routes.router)
api.include_router(transaction_routes.router)
api.include_router(auth_routes.router)
