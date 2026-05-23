import logging
from typing import Optional, Tuple, Union, List

from aiogram import Bot
from pyrogram import Client
from pyrogram import Client
from pyrogram.types import Chat, Message
from pyrogram.errors import (
    UsernameNotOccupied,
    ChatAdminRequired,
    ChannelInvalid,
    InviteHashExpired,
    InviteHashInvalid,
    PeerIdInvalid
)

from services.session_manager import SessionManager
from database.action_data_class import DataInteraction
from database.model import AccountsTable
from config_data.config import Config, load_config

config: Config = load_config()

api_id = config.user_bot.api_id
api_hash = config.user_bot.api_hash


logger = logging.getLogger(__name__)


class ChannelSubscriptionError(Exception):
    """Базовое исключение для ошибок подписки на каналы"""
    pass


class CommentsChatError(Exception):
    """Исключение для ошибок, связанных с чатом комментариев"""
    pass


async def subscribe_accounts(base_id: int, channel: int, manager: SessionManager, session: DataInteraction):
    base = await session.get_base(base_id)
    accounts: list[AccountsTable] = base.accounts
    status, _, chat = False, None, None
    for account in accounts:
        client = manager.get(account.account)
        try:
            data = await subscribe_to_channel(client, channel)
        except Exception as err:
            print(err)
            continue
        status, _, chat = data
    return status, _, chat


async def _get_last_message(client: Client, chat_id: Union[int, str]) -> Optional[Message]:
    """
    Вспомогательная функция для получения последнего сообщения из чата.

    Args:
        client: Клиент Kurigram
        chat_id: ID чата

    Returns:
        Optional[Message]: Последнее сообщение или None
    """
    try:
        # Получаем итератор истории
        history_iterator = client.get_chat_history(
            chat_id=chat_id,
            limit=1  # Нам нужно только последнее сообщение
        )

        # Получаем первое (последнее) сообщение из итератора
        async for message in history_iterator:
            return message

        return None  # Если сообщений нет

    except Exception as e:
        logger.warning(f"⚠️ Ошибка при получении истории чата: {e}")
        return None


async def _get_last_messages(client: Client, chat_id: Union[int, str], limit: int = 5) -> List[Message]:
    """
    Вспомогательная функция для получения нескольких последних сообщений.

    Args:
        client: Клиент Kurigram
        chat_id: ID чата
        limit: Количество сообщений

    Returns:
        List[Message]: Список последних сообщений
    """
    messages = []
    try:
        # Получаем итератор истории
        history_iterator = client.get_chat_history(
            chat_id=chat_id,
            limit=limit
        )

        # Собираем сообщения из итератора
        async for message in history_iterator:
            messages.append(message)
            if len(messages) >= limit:
                break

    except Exception as e:
        logger.warning(f"⚠️ Ошибка при получении истории чата: {e}")

    return messages


async def subscribe_to_channel(
        client: Client,
        channel: Union[str, int],
        check_existing: bool = True
) -> Tuple[bool, Optional[Chat], Optional[Chat]]:
    """
    Подписывается на канал и опционально вступает в чат комментариев.

    Args:
        client: Клиент Kurigram для выполнения действий
        channel: Username (с @ или без) или ID канала
        check_existing: Проверить, уже подписан ли аккаунт

    Returns:
        Tuple[bool, Optional[Chat], Optional[Chat]]:
            - Успех операции
            - Информация о канале (или None)
            - Информация о чате комментариев (или None)

    Raises:
        ChannelSubscriptionError: При критических ошибках подписки
    """
    try:
        # Нормализуем username (убираем @ если есть)
        if isinstance(channel, str):
            channel = channel.replace('@', '')

        logger.info(f"🔍 Начинаем подписку на канал: {channel}")

        # Шаг 1: Получаем информацию о канале
        try:
            chat = await client.get_chat(channel)
            logger.info(f"✅ Получена информация о канале: {chat.title} (ID: {chat.id})")
        except UsernameNotOccupied:
            raise ChannelSubscriptionError(f"Канал {channel} не существует")
        except PeerIdInvalid:
            raise ChannelSubscriptionError(f"Некорректный идентификатор канала: {channel}")
        except Exception as e:
            raise ChannelSubscriptionError(f"Ошибка при получении информации о канале: {e}")

        # Проверяем, что это действительно канал
        # if chat.type not in ["channel", "supergroup"]:
        #     raise ChannelSubscriptionError(f"{chat.title} не является каналом (тип: {chat.type})")
        print(chat.type)

        # Шаг 2: Проверяем, подписан ли уже аккаунт
        if check_existing:
            try:
                member = await client.get_chat_member(chat.id, "me")
                if member and member.status in ["member", "administrator", "creator"]:
                    logger.info(f"ℹ️ Аккаунт уже подписан на канал {chat.title}")

                    # Если уже подписан, сразу пробуем получить чат комментариев
                    comments_chat = await _join_comments_chat(client, chat)
                    return True, chat, comments_chat

            except Exception as e:
                logger.warning(f"⚠️ Не удалось проверить статус подписки: {e}")

        # Шаг 3: Подписываемся на канал
        try:
            # Пробуем разные методы подписки
            if chat.username:
                # Если есть username, используем прямой метод
                await client.join_chat(chat.username)
                logger.info(f"✅ Успешно подписались на канал {chat.title} (через username)")
            else:
                # Если нет username, пробуем через invite link
                if hasattr(chat, 'invite_link') and chat.invite_link:
                    await client.join_chat(chat.invite_link)
                    logger.info(f"✅ Успешно подписались на канал {chat.title} (через invite link)")
                else:
                    # Последний шанс - присоединиться по ID (только для супергрупп)
                    await client.join_chat(chat.id)
                    logger.info(f"✅ Успешно подписались на канал {chat.title} (через ID)")

        except InviteHashExpired:
            raise ChannelSubscriptionError(f"Пригласительная ссылка для канала {chat.title} истекла")
        except InviteHashInvalid:
            raise ChannelSubscriptionError(f"Недействительная пригласительная ссылка для канала {chat.title}")
        except ChatAdminRequired:
            raise ChannelSubscriptionError(f"Требуются права администратора для канала {chat.title}")
        except Exception as e:
            raise ChannelSubscriptionError(f"Не удалось подписаться на канал {chat.title}: {e}")

        # Шаг 4: Автоматически вступаем в чат комментариев (если нужно)
        comments_chat = await _join_comments_chat(client, chat)

        logger.info(f"🎉 Завершена подписка на канал {chat.title}")
        return True, chat, comments_chat

    except ChannelSubscriptionError:
        # Пробрасываем наши кастомные ошибки дальше
        raise
    except Exception as e:
        logger.error(f"❌ Неожиданная ошибка при подписке на канал {channel}: {e}")
        raise ChannelSubscriptionError(f"Внутренняя ошибка: {e}")


async def _join_comments_chat(client: Client, channel: Chat) -> Optional[Chat]:
    """
    Внутренняя функция для вступления в чат комментариев канала.

    Args:
        client: Клиент Kurigram
        channel: Объект канала

    Returns:
        Optional[Chat]: Чат комментариев или None, если не удалось вступить
    """
    try:
        logger.info(f"💬 Пытаемся вступить в чат комментариев канала {channel.title}")

        # Шаг 1: Получаем последнее сообщение канала для определения чата комментариев
        try:
            # Получаем последнее сообщение канала
            last_message = await _get_last_message(client, channel.id)

            if not last_message:
                logger.info(f"ℹ️ В канале {channel.title} нет сообщений, чат комментариев не найден")
                return None

            # Шаг 2: Пробуем определить чат комментариев из сообщения
            comments_chat_id = None

            # Метод 1: Через reply_to_message (для постов с комментариями)
            if hasattr(last_message, 'reply_to_message') and last_message.reply_to_message:
                if hasattr(last_message.reply_to_message, 'chat'):
                    comments_chat_id = last_message.reply_to_message.chat.id
                    logger.info(f"✅ Найден чат комментариев через reply: {comments_chat_id}")

            # Метод 2: Через reply_to_top (для обсуждений)
            elif hasattr(last_message, 'reply_to_top') and last_message.reply_to_top:
                if hasattr(last_message.reply_to_top, 'chat'):
                    comments_chat_id = last_message.reply_to_top.chat.id
                    logger.info(f"✅ Найден чат комментариев через reply_to_top: {comments_chat_id}")

            # Метод 3: Пробуем получить связанный чат через get_chat
            if not comments_chat_id:
                try:
                    # Для каналов с обсуждениями часто есть поле linked_chat_id
                    full_chat = await client.get_chat(channel.id)
                    if hasattr(full_chat, 'linked_chat_id') and full_chat.linked_chat_id:
                        comments_chat_id = full_chat.linked_chat_id
                        logger.info(f"✅ Найден чат комментариев через linked_chat_id: {comments_chat_id}")
                except:
                    pass

            # Метод 4: Проверяем последние сообщения на наличие ссылок на чат обсуждения
            if not comments_chat_id:
                last_messages = await _get_last_messages(client, channel.id, limit=5)
                for msg in last_messages:
                    if hasattr(msg, 'reply_to_message') and msg.reply_to_message:
                        if hasattr(msg.reply_to_message, 'chat'):
                            comments_chat_id = msg.reply_to_message.chat.id
                            logger.info(f"✅ Найден чат комментариев в одном из последних сообщений: {comments_chat_id}")
                            break

            # Шаг 3: Если нашли ID чата комментариев, пробуем вступить
            if comments_chat_id:
                try:
                    # Проверяем, не состоим ли уже
                    try:
                        await client.get_chat_member(comments_chat_id, "me")
                        logger.info(f"ℹ️ Уже состоим в чате комментариев {comments_chat_id}")
                        return await client.get_chat(comments_chat_id)
                    except:
                        pass

                    # Пробуем вступить в чат комментариев
                    await client.join_chat(comments_chat_id)
                    logger.info(f"✅ Успешно вступили в чат комментариев канала {channel.title}")

                    # Получаем информацию о чате
                    return await client.get_chat(comments_chat_id)

                except Exception as e:
                    logger.warning(f"⚠️ Не удалось вступить в чат комментариев: {e}")
                    return None
            else:
                logger.info(f"ℹ️ У канала {channel.title} нет отдельного чата комментариев")
                return None

        except Exception as e:
            logger.warning(f"⚠️ Ошибка при получении сообщений канала: {e}")
            return None

    except Exception as e:
        logger.warning(f"⚠️ Ошибка при вступлении в чат комментариев: {e}")
        return None


async def get_channel(app: Client, channel: str | int):
    try:
        chat = await app.get_chat(channel)
        return chat
    except Exception:
        return None

