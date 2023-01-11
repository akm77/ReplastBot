from aiogram import types
from aiogram.dispatcher.middlewares import LifetimeControllerMiddleware


class EnvironmentMiddleware(LifetimeControllerMiddleware):
    skip_patterns = ["error", "update"]

    def __init__(self, **kwargs):
        super().__init__()
        self.kwargs = kwargs

    async def pre_process(self, obj, data, *args):

        if isinstance(obj, types.CallbackQuery):
            message: types.Message = obj.message
            await obj.answer()
        else:
            message: types.Message = obj