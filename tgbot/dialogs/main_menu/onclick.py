from aiogram.types import CallbackQuery

from ...widgets.aiogram_dialog import DialogManager
from ...widgets.aiogram_dialog.widgets.kbd import Button


async def dialog_done(c: CallbackQuery, widget: Button, manager: DialogManager):
    await manager.done(result=True)