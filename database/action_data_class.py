from datetime import datetime
from typing import Literal

from sqlalchemy import select, insert, update, column, text, delete
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from database.model import (BasesTable, AccountsTable, ChannelsTable, AdminsTable, OneTimeLinksIdsTable)


class DataInteraction():
    def __init__(self, session: async_sessionmaker):
        self._sessions = session

    async def add_link(self, link: str):
        async with self._sessions() as session:
            await session.execute(insert(OneTimeLinksIdsTable).values(
                link=link
            ))
            await session.commit()

    async def add_admin(self, user_id: int, name: str):
        async with self._sessions() as session:
            await session.execute(insert(AdminsTable).values(
                user_id=user_id,
                name=name
            ))
            await session.commit()

    async def add_base(self, name: str):
        async with self._sessions() as session:
            await session.execute(insert(BasesTable).values(
                name=name,
            ))
            await session.commit()

    async def add_base_account(self, base_id: int, account: str, name: str, type: Literal['special', 'general']):
        async with self._sessions() as session:
            await session.execute(insert(AccountsTable).values(
                base_id=base_id,
                name=name,
                account=account,
                type=type
            ))
            await session.commit()

    async def add_channel(self, base_id: int, channel_id: int, chat_id: int, name: str, topic: str, tone: str, audience: str):
        async with self._sessions() as session:
            await session.execute(insert(ChannelsTable).values(
                base_id=base_id,
                channel_id=channel_id,
                chat_id=chat_id,
                name=name,
                topic=topic,
                tone=tone,
                audience=audience
            ))
            await session.commit()

    async def get_account(self, id: int):
        async with self._sessions() as session:
            result = await session.scalar(select(AccountsTable).where(AccountsTable.id == id))
        return result

    async def get_accounts(self, base_id: int):
        async with self._sessions() as session:
            result = await session.scalars(select(AccountsTable).where(AccountsTable.base_id == base_id))
        return result.fetchall()

    async def get_all_accounts(self):
        async with self._sessions() as session:
            result = await session.scalars(select(AccountsTable))
        return result.fetchall()

    async def get_channel(self, id: int):
        async with self._sessions() as session:
            result = await session.scalar(select(ChannelsTable).where(ChannelsTable.channel_id == id))
        return result

    async def get_channel_by_id(self, id):
        async with self._sessions() as session:
            result = await session.scalar(select(ChannelsTable).where(ChannelsTable.id == id))
        return result

    async def get_channels(self, base_id: int):
        async with self._sessions() as session:
            result = await session.scalars(select(ChannelsTable).where(ChannelsTable.base_id == base_id))
        return result.fetchall()

    async def get_base(self, id: int):
        async with self._sessions() as session:
            result = await session.scalar(select(BasesTable).where(BasesTable.id == id))
        return result

    async def get_bases(self):
        async with self._sessions() as session:
            result = await session.scalars(select(BasesTable))
        return result.fetchall()

    async def get_links(self):
        async with self._sessions() as session:
            result = await session.scalars(select(OneTimeLinksIdsTable))
        return result.fetchall()

    async def get_admins(self):
        async with self._sessions() as session:
            result = await session.scalars(select(AdminsTable))
        return result.fetchall()

    async def set_base_data(self, id: int, column: str, value: any):
        async with self._sessions() as session:
            await session.execute(update(BasesTable).where(BasesTable.id == id).values(
                {
                    getattr(BasesTable, column): value
                }
            ))
            await session.commit()

    async def set_account_usage(self, id: int, usage: datetime):
        async with self._sessions() as session:
            await session.execute(update(AccountsTable).where(AccountsTable.id == id).values(
                usage=usage
            ))
            await session.commit()

    async def del_base(self, id):
        async with self._sessions() as session:
            await session.execute(delete(BasesTable).where(BasesTable.id == id))
            await session.commit()

    async def del_account(self, id: int):
        async with self._sessions() as session:
            await session.execute(delete(AccountsTable).where(AccountsTable.id == id))
            await session.commit()

    async def del_channel(self, id: int):
        async with self._sessions() as session:
            await session.execute(delete(ChannelsTable).where(ChannelsTable.id == id))
            await session.commit()

    async def del_link(self, link_id: str):
        async with self._sessions() as session:
            await session.execute(delete(OneTimeLinksIdsTable).where(OneTimeLinksIdsTable.link == link_id))
            await session.commit()

    async def del_admin(self, user_id: int):
        async with self._sessions() as session:
            await session.execute(delete(AdminsTable).where(AdminsTable.user_id == user_id))
            await session.commit()

