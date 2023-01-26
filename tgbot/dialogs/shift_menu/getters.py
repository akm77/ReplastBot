from aiogram_dialog import DialogManager

from tgbot.models.erp_shift_staff_activity import shift_list_full


async def get_shift_list(dialog_manager: DialogManager, **middleware_data):
    session = middleware_data.get('session')

    db_shift_list = await shift_list_full(session, reverse=True)

    data = {
        'shift_list': [
            (f'{shift.date: %d.%m.%Y} смена: {shift.number} ({shift.duration} ч)', f'{shift.date}_{shift.number}')
            for shift in db_shift_list
        ],
    }
    return data

