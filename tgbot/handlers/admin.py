from aiogram import Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.types import Message

from ..dialogs.main_menu.states import MainMenu
from ..widgets.aiogram_dialog import DialogManager


async def admin_start(message: Message, dialog_manager: DialogManager, state: FSMContext, **kwargs):
    await dialog_manager.start(MainMenu.select_action)


def register_admin(dp: Dispatcher):
    dp.register_message_handler(admin_start, commands=["start"], state="*", is_admin=True)
