import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.contrib.fsm_storage.redis import RedisStorage2
from gspread_asyncio import AsyncioGspreadClientManager

from tgbot.config import load_config
from tgbot.dialogs import setup_dialogs
from tgbot.filters.admin import AdminFilter
from tgbot.handlers.admin import register_admin
from tgbot.handlers.echo import register_echo
from tgbot.handlers.google_sheets_commands import register_sheet_commands
from tgbot.handlers.user import register_user
from tgbot.middlewares.environment import EnvironmentMiddleware
from tgbot.models.base import create_db_session

logger = logging.getLogger(__name__)


def register_all_middlewares(dp, config, session):
    dp.setup_middleware(EnvironmentMiddleware(config=config, session=session))


def register_all_filters(dp):
    dp.filters_factory.bind(AdminFilter)


def register_all_handlers(dp):
    register_admin(dp)
    register_user(dp)
    register_sheet_commands(dp)
    register_echo(dp)


async def main():
    logging.basicConfig(
        level=logging.INFO,
        format=u'%(filename)s:%(lineno)d #%(levelname)-8s [%(asctime)s] - %(name)s - %(message)s',
    )
    logger.info("Starting bot")
    config = load_config(".env")

    storage = RedisStorage2(prefix="r_fsm") if config.tg_bot.use_redis else MemoryStorage()
    # await storage.reset_all()
    bot = Bot(token=config.tg_bot.token, parse_mode='HTML')
    dp = Dispatcher(bot, storage=storage)
    google_client_manager: AsyncioGspreadClientManager = AsyncioGspreadClientManager(
        config.misc.scoped_credentials
    )

    bot['google_client_manager'] = google_client_manager
    bot['config'] = config
    bot['Session'] = await create_db_session(config)

    register_all_middlewares(dp, config, bot['Session'])
    register_all_filters(dp)
    setup_dialogs(dp, tz=config.misc.tzinfo, calendar_locale=config.misc.calendar_locale)
    register_all_handlers(dp)

    # start
    try:
        await dp.start_polling()
    finally:
        await dp.storage.close()
        await dp.storage.wait_closed()
        await bot.session.close()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.error("Bot stopped!")
