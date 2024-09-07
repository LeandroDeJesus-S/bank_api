from databases import Database
from sqlalchemy.orm import declarative_base

from .settings import settings

DB = Database(settings.DATABASE_URI)
Base = declarative_base()
