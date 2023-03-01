from aiogram.types import CallbackQuery
from gspread_asyncio import AsyncioGspreadClientManager

from ..dct_menu.states import DictMenuStates
from ..shift_menu.states import ShiftMenu
from ...handlers.google_sheets_commands import get_sheet_url
from ...services.google_sheets import export_production
from ...widgets.aiogram_dialog import DialogManager
from ...widgets.aiogram_dialog.widgets.kbd import Button


async def on_click_dct_button(c: CallbackQuery, button: Button, manager: DialogManager):
    await manager.start(DictMenuStates.select_dct)


async def on_click_shift_button(c: CallbackQuery, button: Button, manager: DialogManager):
    await manager.start(ShiftMenu.select_shift)


async def on_click_export_production(c: CallbackQuery, button: Button, manager: DialogManager):
    google_client_manager = c.bot.get("google_client_manager")
    session = manager.data.get("session")
    url = get_sheet_url()
    await export_production(session, google_client_manager, url)
