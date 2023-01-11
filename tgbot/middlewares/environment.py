from aiogram import types
from aiogram.dispatcher.middlewares import LifetimeControllerMiddleware


class EnvironmentMiddleware(LifetimeControllerMiddleware):
    skip_patterns = ["error", "update"]

    async def pre_process(self, obj, data, *args):

        if isinstance(obj, types.CallbackQuery):
            message: types.Message = obj.message
            await obj.answer()
        else:
            message: types.Message = obj
