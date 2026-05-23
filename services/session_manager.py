import asyncio
import logging
import os
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime

from pyrogram import Client
from pyrogram.types import Message
from pyrogram.enums import MessageMediaType, ChatType

from utils.image_funcs import photo_to_base64
from utils.ai.commenting import get_comment
from database.action_data_class import DataInteraction


logger = logging.getLogger("pyrogram")

logger.setLevel(logging.INFO)


class SessionManager:
    """
    Менеджер для управления клиентами Kurigram на основе файлов сессий.
    Автоматически устанавливает обработчики на всех клиентов.
    """

    def __init__(self, api_id: int, api_hash: str, session: DataInteraction):
        self.api_id = api_id
        self.api_hash = api_hash
        self._clients: Dict[str, Client] = {}  # путь_к_сессии -> Client
        self._tasks: Dict[str, asyncio.Task] = {}  # для отслеживания задач клиентов
        self._running = False
        self.session = session

    async def _setup_handlers(self, client: Client, session_path: str):
        """
        Внутренний метод для установки обработчиков на клиента.
        Запускается автоматически при добавлении клиента.
        """

        @client.on_message()
        async def message_handler(client: Client, message: Message):
            """Обработчик всех входящих сообщений"""
            try:
                # Базовая информация о сообщении
                chat = message.chat
                if not chat or chat.type != ChatType.CHANNEL:
                    return
                channel = await self.session.get_channel(chat.id)
                if not channel:
                    return
                accounts = await self.session.get_accounts(channel.base_id)
                selected_account = None
                for account in accounts:
                    if selected_account is None:
                        selected_account = account
                        continue
                    if selected_account.usage is None:
                        break
                    if account.usage is None:
                        selected_account = account
                        break
                    if selected_account.usage > account.usage:
                        selected_account = account

                image = None
                if message.photo:
                    image = await photo_to_base64(message.photo, client)

                discussion_message = await client.get_discussion_message(
                    chat_id=message.chat.id,
                    message_id=message.id
                )
                if not discussion_message:
                    return

                counter = 0
                comment = None
                while True:
                    if counter >= 2:
                        break
                    try:
                        comment = await get_comment(message, channel, selected_account.type, image)
                    except Exception as err:
                        logger.info(f'Failed to generate comment| Count: {counter}| Error: {err}')
                        counter += 1
                        continue
                    break
                if comment is None:
                    return

                await self.session.set_account_usage(selected_account.id, datetime.now())
                client = self.get(selected_account.account)
                counter = 0
                while True:
                    if counter >= 2:
                        break
                    try:
                        await client.send_message(
                            chat_id=discussion_message.chat.id,
                            text=comment,
                            reply_to_message_id=discussion_message.id
                        )
                    except Exception as err:
                        logger.info(f'Failed to send comment. Count: {counter}| Error: {err}')
                        counter += 1
                    break

            except Exception as e:
                logger.error(f"❌ Ошибка в обработчике сообщений [{session_path}]: {e}")

        logger.info(f"✅ Обработчики установлены для клиента {session_path}")

    async def _run_client(self, session_path: str):
        """
        Внутренний метод для запуска клиента в фоне.
        """
        client = self._clients.get(session_path)
        if not client:
            logger.error(f"❌ Клиент {session_path} не найден")
            return

        try:
            # Запускаем клиент
            await client.start()
            logger.info(f"✅ Клиент {session_path} успешно запущен и слушает обновления")

            # Держим клиент запущенным
            while self._running and session_path in self._clients:
                await asyncio.sleep(1)

        except Exception as e:
            logger.error(f"❌ Ошибка при работе клиента {session_path}: {e}")
        finally:
            # Останавливаем клиент при выходе
            if session_path in self._clients:
                try:
                    await client.stop()
                    logger.info(f"⏹️ Клиент {session_path} остановлен")
                except:
                    pass

    async def add(self, session_path: str) -> bool:
        """
        Добавляет клиента по пути к файлу сессии.
        Автоматически запускает его в фоне с обработчиками.

        Args:
            session_path: Путь к файлу сессии (.session)

        Returns:
            bool: True если успешно добавлен, False если ошибка
        """
        session_path = 'accounts/' + session_path + '.session'
        try:
            # Проверяем существование файла
            session_file = Path(session_path)
            if not session_file.exists():
                logger.error(f"❌ Файл сессии не найден: {session_path}")
                return False

            session_name = session_file.stem

            if session_path in self._clients:
                logger.warning(f"⚠️ Клиент {session_path} уже существует")
                return False

            print(session_path.rsplit('.', maxsplit=1)[0])
            print(session_name)
            client = Client(
                name=session_path.rsplit('.', maxsplit=1)[0],
                api_id=self.api_id,
                api_hash=self.api_hash
            )

            # Сохраняем клиента
            self._clients[session_path] = client

            # Устанавливаем обработчики
            await self._setup_handlers(client, session_path)

            # Запускаем клиента в фоне
            if self._running:
                task = asyncio.create_task(self._run_client(session_path))
                self._tasks[session_path] = task
                logger.info(f"✅ Клиент {session_path} добавлен и запущен")
            else:
                logger.info(f"✅ Клиент {session_path} добавлен (но менеджер не запущен)")

            return True

        except Exception as e:
            logger.error(f"❌ Ошибка при добавлении клиента {session_path}: {e}")
            # Чистим за собой
            if session_path in self._clients:
                del self._clients[session_path]
            return False

    def get(self, session_path: str) -> Optional[Client]:
        """
        Получает клиента по пути к файлу сессии.

        Args:
            session_path: Путь к файлу сессии

        Returns:
            Client или None если не найден
        """
        session_path = 'accounts/' + session_path + '.session'
        print(self._clients.get(session_path))
        return self._clients.get(session_path)

    async def remove(self, session_path: str, stop: bool = False) -> bool:
        """
        Удаляет клиента по пути к файлу сессии.
        Останавливает его перед удалением.

        Args:
            session_path: Путь к файлу сессии

        Returns:
            bool: True если успешно удален
        """
        print(session_path)
        try:
            client = self._clients.get(session_path)
            if not client:
                logger.warning(f"⚠️ Клиент {session_path} не найден")
                return False

            # Останавливаем фоновую задачу
            if session_path in self._tasks:
                self._tasks[session_path].cancel()
                del self._tasks[session_path]

            # Останавливаем клиента
            try:
                await client.stop()
            except:
                pass

            # Удаляем из словаря
            del self._clients[session_path]
            logger.info(f"✅ Клиент {session_path} удален")

            if not stop:
                try:
                    os.remove(f'{session_path}')
                    os.remove(f'{session_path.replace(".session", ".session-journal")}')
                except Exception:
                    ...

            return True

        except Exception as e:
            logger.error(f"❌ Ошибка при удалении клиента {session_path}: {e}")
            return False

    async def start(self):
        """
        Запускает менеджер и всех добавленных клиентов.
        """
        self._running = True
        logger.info("🚀 Запуск менеджера сессий...")

        # Запускаем всех существующих клиентов
        for session_path in list(self._clients.keys()):
            task = asyncio.create_task(self._run_client(session_path))
            self._tasks[session_path] = task

        logger.info(f"✅ Менеджер запущен с {len(self._clients)} клиентами")

    async def stop(self):
        """
        Останавливает менеджера и всех клиентов.
        """
        self._running = False
        logger.info("🛑 Остановка менеджера сессий...")

        # Останавливаем всех клиентов
        for session_path in list(self._clients.keys()):
            await self.remove(session_path, stop=True)

        logger.info("✅ Менеджер остановлен")

    def get_all(self) -> Dict[str, Client]:
        """
        Возвращает всех клиентов.
        """
        return self._clients.copy()


channel_id = -1001255428755


async def test_func(session: DataInteraction, manager: SessionManager):
    message_ids = [88865]

    accounts = await session.get_all_accounts()
    client = manager.get(accounts[0].account)

    channel = await session.get_channel(channel_id)
    if not channel:
        return

    accounts = await session.get_accounts(channel.base_id)

    selected_account = None
    for account in accounts:
        if selected_account is None:
            selected_account = account
            continue
        if selected_account.usage is None:
            break
        if account.usage is None:
            selected_account = account
            break
        if selected_account.usage > account.usage:
            selected_account = account

    async for message in client.get_chat_history(
        chat_id=channel_id
        #limit=1
    ):
        if message.id not in message_ids:
            continue

        image = None
        if message.photo:
            image = await photo_to_base64(message.photo, client)
        counter = 0
        comment = None
        while True:
            if counter >= 2:
                break
            try:
                comment = await get_comment(message, channel, selected_account.type, image)
                break
            except Exception as err:
                logger.error(f'Failed to generate comment| Count: {counter}| Error: {err}')
                counter += 1
                continue

        if comment is None:
            continue
        await session.set_account_usage(selected_account.id, datetime.now())

        client = manager.get(selected_account.account)
        counter = 0
        while True:
            if counter >= 2:
                break
            try:
                await client.send_message(
                    chat_id='me',
                    text=f'Пост: https://t.me/pravdadirty/{message.id} \nКомментарий:' + comment
                )
                # await client.send_message(
                #     chat_id='me',
                #     text=comment
                # )
                break
            except Exception as err:
                logger.error(f'Failed to send comment| Count: {counter}| Error: {err}')
                counter += 1
        message_ids.remove(message.id)
        print(message_ids)
        if not message_ids:
            return

# except Exception as e:
# logger.error(f"❌ Ошибка в обработчике сообщений [{session_path}]: {e}")