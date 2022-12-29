import datetime
from decimal import Decimal

from aiogram import Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.types import Message

from tgbot.models.erp_accounting import add_entry, get_account_from_account_no


async def admin_start(message: Message, state: FSMContext):
    await message.reply("Hello, admin!")
    await state.finish()
    Session = message.bot["Session"]

    # 1 Оплата поставщику
    # 2 Поступление материалов
    # 3 Передача материалов в  производство
    # 4 Возврат брака на склад
    # 5 Передача готовой продукции на склад
    # 6 Продажа готовой продукции
    # 7 Поступление оплаты от покупателя
    # 8 Ввод начальных остатков по банку

    await add_entry(Session, operation_id=8, dr="50", cr="000", amount=Decimal(3000.00),
                    entry_dt=datetime.datetime(2021, 12, 31, 23, 59, 58))
    await add_entry(Session, operation_id=8, dr="51", cr="000", amount=Decimal(3000.00),
                    entry_dt=datetime.datetime(2021, 12, 31, 23, 59, 59))

    await add_entry(Session, operation_id=2, dr="10.1", cr="60", amount=Decimal(1500.00), entry_dt=datetime.datetime(2022, 12, 21, 15, 10, 00))
    await add_entry(Session, operation_id=1, dr="60", cr="51", amount=Decimal(1500.00), entry_dt=datetime.datetime(2022, 12, 21, 15, 11, 00))
    await add_entry(Session, operation_id=3, dr="20", cr="10.1", amount=Decimal(900.00), entry_dt=datetime.datetime(2022, 12, 21, 15, 12, 00))
    await add_entry(Session, operation_id=5, dr="43", cr="20", amount=Decimal(900.00), entry_dt=datetime.datetime(2022, 12, 21, 15, 13, 00))
    await add_entry(Session, operation_id=5, dr="90.2", cr="43", amount=Decimal(900.00), entry_dt=datetime.datetime(2022, 12, 21, 15, 14, 00))
    await add_entry(Session, operation_id=6, dr="62", cr="90.1", amount=Decimal(1200.00), entry_dt=datetime.datetime(2022, 12, 21, 15, 15, 00))
    await add_entry(Session, operation_id=7, dr="51", cr="62", amount=Decimal(1200.00), entry_dt=datetime.datetime(2022, 12, 21, 15, 16, 00))

    await add_entry(Session, operation_id=2, dr="10.1", cr="60", amount=Decimal(1500.00))
    await add_entry(Session, operation_id=1, dr="60", cr="51", amount=Decimal(1500.00))
    await add_entry(Session, operation_id=3, dr="20", cr="10.1", amount=Decimal(400.00))
    await add_entry(Session, operation_id=5, dr="43", cr="20", amount=Decimal(400.00))
    await add_entry(Session, operation_id=5, dr="90.2", cr="43", amount=Decimal(400.00))
    await add_entry(Session, operation_id=6, dr="62", cr="90.1", amount=Decimal(600.00))
    await add_entry(Session, operation_id=7, dr="51", cr="62", amount=Decimal(600.00))


def register_admin(dp: Dispatcher):
    dp.register_message_handler(admin_start, commands=["start"], state="*", is_admin=True)
