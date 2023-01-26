from aiogram import Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.types import Message
from aiogram_dialog import DialogManager

from tgbot.dialogs.shift_menu.states import ShiftMenu


async def user_start(message: Message, dialog_manager: DialogManager, state: FSMContext):
    dm = dialog_manager
    await dialog_manager.start(ShiftMenu.select_shift)



def register_user(dp: Dispatcher):
    dp.register_message_handler(user_start, commands=["shft"], state="*")
