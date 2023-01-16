import asyncio
import logging
from typing import Optional

from aiogram import Dispatcher
from aiogram.types import Message, ChatActions
from gspread_asyncio import AsyncioGspreadClientManager

from tgbot.config import Config
from tgbot.services.google_sheets import create_spreadsheet, Worksheets

logger = logging.getLogger(__name__)


def get_sheet_url() -> Optional[str]:
    try:
        with open("tgbot/sheet_url.txt", mode="r") as f:
            return f.read()
    except OSError:
        logger.error("File tgbot/sheet_url.txt not found")
        return None


def save_sheet_url(url: str) -> Optional[int]:
    with open("tgbot/sheet_url.txt", mode="w") as f:
        return f.write(url)


async def create_sheet(message: Message):
    await ChatActions.typing()
    url = get_sheet_url()
    config: Config = message.bot["config"]
    google_client_manager: AsyncioGspreadClientManager = message.bot["google_client_manager"]
    if url:
        message_text = f"Таблица <a href={url}>{config.misc.google_sheet_title}</a> уже существует."
        my_message = await message.answer(message_text)
    else:
        google_client = await google_client_manager.authorize()
        spreadsheet = await create_spreadsheet(google_client, config.misc.google_sheet_title)
        for title in Worksheets.TITLES:
            await spreadsheet.add_worksheet(title, 1000, 100)
        url = spreadsheet.ss.url
        logger.info(f"Таблица {config.misc.google_sheet_title} создана. URL {url}")
        save_sheet_url(spreadsheet.ss.url)
        message_text = f"Таблица <a href={url}>{config.misc.google_sheet_title}</a> создана."
        my_message = await message.answer(message_text)
    await asyncio.sleep(30)
    await my_message.delete()


def register_sheet_commands(dp: Dispatcher):
    dp.register_message_handler(create_sheet, commands=["gsc"], state="*")
