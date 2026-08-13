import httpx
import asyncio
import base64

from anthropic import AsyncAnthropic

from config_data.config import Config, load_config

config: Config = load_config()

client = AsyncAnthropic(
    api_key=config.apimart.api_key
    #base_url="https://api.unifically.com",
    # http_client=
)


async def get_ai_answer(user_prompt: str, system_prompt: str | None = None, image_base64: str = None):
    if not image_base64:
        messages = [{"role": "user", "content": user_prompt}]
    else:
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/jpeg",
                            "data": image_base64,
                        },
                    },
                    {
                        "type": "text",
                        "text": user_prompt
                    }
                ]
            }
        ]
    message = await client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2048,
        system=system_prompt if system_prompt else None,
        messages=messages
    )
    return message.content[0].text


async def test(prompt: str = None):
    with open("menu.jpg", "rb") as img_file:
        image_data = base64.b64encode(img_file.read()).decode("utf-8")

#     messages = [
#         {
#             "role": "user",
#             "content": [
#                 {
#                     "type": "image",
#                     "source": {
#                         "type": "base64",
#                         "media_type": "image/jpeg",
#                         "data": image_data,
#                     },
#                 },
#                 {
#                     "type": "text",
#                     "text": "Опиши, что изображено на этой картинке"
#                 }
#             ],
#         }
#     ]
#     messages.append({'role': 'assistant', 'content': """# Описание изображения
#
# На картинке изображена рекламная иллюстрация на тему криптовалютных сделок на платформе Binance.
#
# ## Основные элементы:
#
# **Текст:**
# - Заголовок на русском языке: "Честные ОТС-сделки" (OTC - over-the-counter, внебиржевые сделки)
# - Логотип и название "BINANCE"
#
# **Персонажи:**
# - Два молодых человека пожимают друг другу руки
# - Один одет в черную толстовку и бейсболку
# - Второй - в желтой толстовке с капюшоном, держит в руке пачку долларовых купюр
#
# **Символы и объекты:**
# - Центральный щит с золотым замком (символ безопасности)
# - Множество стопок золотых монет
# - Ноутбук с графиком торговли
# - Судейский молоток
# - Документ с галочкой (подтверждение сделки)
# - Золотисто-черная цветовая гамма с эффектами свечения
# - Сетевые соединения на фоне
#
# Изображение передает идею безопасных, легальных и честных криптовалютных транзакций между пользователями через платформу Binance."""})
    # print(client.models.list())
    # async for model in client.models.list():
    #     print(model)
    # return
    messages = []
    messages.append({'role': 'user', 'content': 'Как у тебя вообще сегодня с настроением?'})
    message = await client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        messages=messages
    )
    return message.content[0].text


# print(asyncio.run(test()))
