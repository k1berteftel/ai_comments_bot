from datetime import datetime
from typing import Literal

from sqlalchemy import BigInteger, VARCHAR, ForeignKey, DateTime, Boolean, Column, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship, DeclarativeBase
from sqlalchemy.ext.asyncio import AsyncAttrs


class Base(AsyncAttrs, DeclarativeBase):
    pass


class BasesTable(Base):
    __tablename__ = 'bases'

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    name: Mapped[str] = mapped_column(VARCHAR)
    channels: Mapped[list["ChannelsTable"]] = relationship('ChannelsTable', lazy="selectin", cascade='all, delete', uselist=True)
    accounts: Mapped[list["AccountsTable"]] = relationship('AccountsTable', lazy="selectin", cascade='all, delete', uselist=True)


class ChannelsTable(Base):
    __tablename__ = 'channels'

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    base_id: Mapped[int] = mapped_column(ForeignKey('bases.id', ondelete='CASCADE'))
    channel_id: Mapped[int] = mapped_column(BigInteger, unique=True)
    chat_id: Mapped[int] = mapped_column(BigInteger)
    name: Mapped[str] = mapped_column(VARCHAR, unique=True)

    topic: Mapped[str] = mapped_column(VARCHAR)
    tone: Mapped[str] = mapped_column(VARCHAR)
    audience: Mapped[str] = mapped_column(VARCHAR)


class AccountsTable(Base):
    __tablename__ = 'accounts'

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    base_id: Mapped[int] = mapped_column(ForeignKey('bases.id', ondelete='CASCADE'))
    name: Mapped[str] = mapped_column(VARCHAR)
    account: Mapped[str] = mapped_column(VARCHAR, unique=True)
    usage: Mapped[datetime] = mapped_column(DateTime(timezone=False), default=None, nullable=True)
    type: Mapped[Literal['special', 'general']] = mapped_column(VARCHAR)


class AdminsTable(Base):
    __tablename__ = 'admins'

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    user_id: Mapped[int] = mapped_column(BigInteger)
    name: Mapped[str] = mapped_column(VARCHAR)


class OneTimeLinksIdsTable(Base):
    __tablename__ = 'links'

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    link: Mapped[str] = mapped_column(VARCHAR)


