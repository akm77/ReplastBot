from aiogram import Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.types import Message

from tgbot.dialogs.shift_menu.states import ShiftMenu
from tgbot.widgets.aiogram_dialog import DialogManager


async def user_start(message: Message, dialog_manager: DialogManager, state: FSMContext, **kwargs):
    await dialog_manager.start(ShiftMenu.select_shift)


def register_user(dp: Dispatcher):
    dp.register_message_handler(user_start, commands=["shft"], state="*")
