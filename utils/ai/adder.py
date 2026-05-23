import re
import json
from pydantic import ValidationError

from pyrogram import Client
from pyrogram.types import Chat, Message

from utils.ai.errors import AIGenerationError
from utils.ai.request import get_ai_answer
from utils.ai.models import PostAnalytics, ChannelAnalytics


def _clean_json_response(text: str) -> str:
    """Очищает ответ от markdown-разметки JSON"""
    # Убираем ```json и ``` в начале и конце
    text = re.sub(r'^```json\s*', '', text, flags=re.MULTILINE)
    text = re.sub(r'```\s*$', '', text, flags=re.MULTILINE)
    # Убираем любые другие markdown-блоки
    text = re.sub(r'^```\s*', '', text, flags=re.MULTILINE)
    text = re.sub(r'```\s*$', '', text, flags=re.MULTILINE)
    return text.strip()


async def get_channel_analysis(client: Client, chat: Chat) -> ChannelAnalytics | None:
    posts = []
    async for post in client.get_chat_history(chat.id, reverse=False, limit=5):
        post = post.content.replace('\n', ' ').replace('\r', '')
        posts.append(post)
    print('Success get posts')
    posts = "\n".join(posts)
    prompt = f'''
    Ты — аналитик Telegram-каналов. Проанализируй канал по следующим данным и верни ТОЛЬКО JSON без пояснений.

    Данные канала:
    Название канала: {chat.title}
    Описание канала: {chat.description}
    Username: @{chat.username}
    Количество подписчиков: {chat.members_count}

    Последние 5 постов канала:
    {posts}

    Определи:
    1. Тематика канала (одно слово из списка: Политика, Треш, Познавательное, Сатира, Новости, Регионалка, Технологии, Бизнес, Здоровье, Юмор)
    2. Тон канала (одно слово из списка: агрессивный, ироничный, нейтральный, восторженный, экспертный, пафосный, простой)
    3. Целевая аудитория (коротко, 2-3 слова)

    Ответ должен быть строго в формате JSON:
    {{
        "topic": "тематика",
        "tone": "тон",
        "audience": "целевая аудитория",
        "confidence": 0.95
    }}
    '''
    try:
        result = await get_ai_answer(prompt)
    except Exception as err:
        print(f'Generation Error: {err}')
        raise AIGenerationError(err)
    print(f'AI gen result: {result}')
    result = _clean_json_response(result)
    try:
        result = json.loads(result)
        analytics = ChannelAnalytics(**result)
    except ValidationError as err:
        print(f'Validation error: {err}')
        raise err

    return analytics


async def get_post_analysis(message: Message) -> PostAnalytics:
    prompt = f'''
    Ты — аналитик контента. Проанализируй пост в Telegram и верни ТОЛЬКО JSON без пояснений.

    Текст поста:
    {message.content}

    Определи:
    1. Краткая суть поста (одно предложение, 10-15 слов)
    2. Настроение/тональность поста (одно слово из списка: позитивное, негативное, нейтральное, саркастичное, возмущенное, восторженное, тревожное, ироничное)
    3. Главная тема поста (что обсуждается: конкретная проблема, событие, человек, явление)
    4. Есть ли в посте провокация/скрытый смысл (да/нет, если да - кратко описать)
    5. Ключевые сущности (список из 1-3 важных упоминаний: имена, названия, места)

    Ответ должен быть строго в формате JSON:
    {{
        "summary": "краткая суть поста",
        "mood": "настроение",
        "main_topic": "главная тема",
        "comment_length_style": "ultrashort / short / medium" # ультракороткий (2-5 слов), короткий (1 предложение), средний (2-3 предложения)
        "recommended_emotion": "sarcasm / outrage / humor / observation / common_sense"
        "is_provocative": "если есть, иначе пустая строка",
        "hidden_meaning": "если есть, иначе пустая строка",
        "key_entities": ["сущность1", "сущность2"],
        "confidence": 0.95
    }}
    '''
    try:
        result = await get_ai_answer(prompt)
    except Exception as err:
        print(f'Generation Error: {err}')
        raise AIGenerationError(err)
    print(f'AI gen result: {result}')
    result = _clean_json_response(result)
    try:
        result = json.loads(result)
        analytics = PostAnalytics(**result)
    except ValidationError as err:
        print(f'Validation error: {err}')
        raise err

    return analytics