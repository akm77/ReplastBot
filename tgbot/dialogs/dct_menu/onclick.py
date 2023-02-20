from aiogram.types import CallbackQuery

from ...widgets.aiogram_dialog import DialogManager
from ...widgets.aiogram_dialog.widgets.kbd import Button


async def on_click_dct(c: CallbackQuery, button: Button, manager: DialogManager):
    ctx = manager.current_context()
    current_state = ctx.state
    pass
