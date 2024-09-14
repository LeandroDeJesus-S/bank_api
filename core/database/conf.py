from databases import Database
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import declarative_base

from core.settings import settings

DB = Database(settings.DATABASE_URI)
Base = declarative_base()
engine = create_async_engine(
    settings.DATABASE_URI,
    connect_args={'check_same_thread': settings.ENVIRONMENT == 'production'}
)
