from typing import List

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database.conf import Base


class UserRole(Base):
    """Tertiary table that represent the user role attributions.

    Args:
        user_id (int): the user id, Foreign Key and primary key.
        role_id (int): the role id, Foreign Key and primary key.
    """
    __tablename__ = "user_role"

    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), primary_key=True)
    role_id: Mapped[int] = mapped_column(ForeignKey("role.id"), primary_key=True)

    def validate(self): ...


class Role(Base):
    """the role entity

    Args:
        id (int): the id of the role. Primary key with autoincrement.
        name (str): the role name. Max 10 chars, not null and unique.
        users (List[User]): the relationship reference to the user table.
    """
    __tablename__ = "role"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(10), nullable=False, unique=True)

    users: Mapped[List["User"]] = relationship(  # type: ignore # noqa: F821
        secondary='user_role', back_populates="roles"
    )

    def validate(self): ...
