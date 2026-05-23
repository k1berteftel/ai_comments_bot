import os
import base64
import tempfile
import aiofiles
from pyrogram.types import Photo
from pyrogram import Client


async def photo_to_base64(photo: Photo, client: Client) -> str | None:
    """
    Конвертирует Photo из Telegram в base64 и автоматически удаляет файл.

    Args:
        photo: Объект Photo от Pyrogram
        client: Экземпляр клиента Pyrogram для скачивания файла

    Returns:
        Tuple[str, str] - (base64_data, media_type) или None в случае ошибки
        media_type всегда 'image/jpeg' для фото Telegram
    """
    # Создаем временный файл с уникальным именем
    with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp_file:
        temp_path = tmp_file.name

    try:
        # Получаем наибольшее доступное качество фото
        # У Photo в Pyrogram есть атрибут file_id для наибольшего размера
        file_id = photo.file_id

        try:
            await client.download_media(
                message=photo,  # Можно передать file_id напрямую
                file_name=temp_path
            )
        except Exception:
            await client.download_media(
                message=file_id,  # Можно передать file_id напрямую
                file_name=temp_path
            )

        # Читаем и кодируем в base64
        async with aiofiles.open(temp_path, 'rb') as f:
            file_content = await f.read()
            base64_data = base64.b64encode(file_content).decode('utf-8')

        # Для фото Telegram всегда JPEG
        return base64_data

    except Exception as e:
        print(f"Ошибка при обработке фото: {e}")
        return None

    finally:
        # Гарантированно удаляем временный файл
        try:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
        except Exception:
            pass