import asyncio
import logging
import re
from typing import Optional

from aiogram import Dispatcher
from aiogram.types import Message, ChatActions
from aiogram.utils.markdown import text
from gspread_asyncio import AsyncioGspreadClientManager

from tgbot.config import Config
from tgbot.models.erp_shift_staff_activity import shift_activity_list, shift_material_intake_list, shift_bags_list, staff_time_sheet
from tgbot.services.google_sheets import create_spreadsheet, Worksheets, share_spreadsheet, export_production

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
        message_text = f"Таблица <a href='{url}'>{config.misc.google_sheet_title}</a> уже существует."
        my_message = await message.answer(message_text)
    else:
        google_client = await google_client_manager.authorize()
        spreadsheet = await create_spreadsheet(google_client, config.misc.google_sheet_title)
        for title in Worksheets.TITLES:
            await spreadsheet.add_worksheet(title, 1000, 100)
        url = spreadsheet.ss.url
        logger.info(f"Таблица {config.misc.google_sheet_title} создана. URL {url}")
        save_sheet_url(spreadsheet.ss.url)
        message_text = f"Таблица <a href='{url}'>{config.misc.google_sheet_title}</a> создана."
        my_message = await message.answer(message_text)
    await asyncio.sleep(30)
    await my_message.delete()


async def share_sheet(message: Message):
    await ChatActions.typing()
    args_string = message.get_args()
    EMAIL_PATTERN = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
    emails = args_string.split()
    email_pattern = re.compile(EMAIL_PATTERN)
    config: Config = message.bot["config"]
    google_client_manager: AsyncioGspreadClientManager = message.bot["google_client_manager"]

    google_client = await google_client_manager.authorize()
    url = get_sheet_url()
    spreadsheet = await google_client.open_by_url(url)
    logger.info(f"Open spreadsheet {spreadsheet.title}")
    share_to_email: list = []
    for email in emails:
        if email_pattern.match(email):
            await share_spreadsheet(spreadsheet, email, notify=True)
            share_to_email.append(email)

    shared_to = ", ".join(share_to_email)
    my_message = await message.answer(text(f"Google sheet\n"
                                           f"<code>Url: </code><a href='{url}'>{config.misc.google_sheet_title}</a>"
                                           f"\nshared to: {shared_to}"))
    await asyncio.sleep(30)
    await my_message.delete()


async def export_to_sheet(message: Message):
    await ChatActions.typing()
    Session = message.bot["Session"]
    google_client_manager: AsyncioGspreadClientManager = message.bot["google_client_manager"]
    url = get_sheet_url()
    await export_production(Session, google_client_manager, url)


def register_sheet_commands(dp: Dispatcher):
    dp.register_message_handler(create_sheet, commands=["gsc"], state="*")
    dp.register_message_handler(share_sheet, commands=["gss"], state="*")
    dp.register_message_handler(export_to_sheet, commands=["gse"], state="*")
