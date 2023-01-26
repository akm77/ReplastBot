import logging

from aiogram import Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.types import Message, ChatActions

logger = logging.getLogger(__name__)


async def shift_start(message: Message, state: FSMContext):
    await ChatActions.typing()
    Session = message.bot["Session"]


def register_shift_processing(dp: Dispatcher):
    dp.register_message_handler(shift_start, commands=["shift"], state="*")
