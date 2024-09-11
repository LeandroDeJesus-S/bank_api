from databases import Database
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base

from .settings import settings

DB = Database(settings.DATABASE_URI)
Base = declarative_base()
engine = create_engine(
    settings.DATABASE_URI,
    connect_args={'check_same_thread': settings.ENVIRONMENT != 'production'}
)
