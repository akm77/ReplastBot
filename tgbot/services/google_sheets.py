import datetime
import logging
from dataclasses import dataclass
from typing import Tuple, List

from aiohttp.typedefs import StrOrURL
from gspread import Cell, Worksheet
from gspread_asyncio import AsyncioGspreadClient, AsyncioGspreadSpreadsheet, AsyncioGspreadWorksheet, \
    AsyncioGspreadClientManager
from gspread_formatting import CellFormat, Borders, Border, TextFormat, format_cell_range
from sqlalchemy.orm import sessionmaker

from tgbot.misc.utils import value_to_decimal, convert_datetime_to_gsheet

logger = logging.getLogger(__name__)


@dataclass
class Worksheets:
    TITLES = ['Пр-во', 'БД пр-во']


async def create_spreadsheet(client: AsyncioGspreadClient, spreadsheet_name: str):
    spreadsheet = await client.create(spreadsheet_name)
    spreadsheet = await client.open_by_key(spreadsheet.id)
    return spreadsheet


async def add_worksheet(async_spreadsheet: AsyncioGspreadSpreadsheet,
                        worksheet_name: str):
    worksheet = await async_spreadsheet.add_worksheet(worksheet_name, rows=1000, cols=100)
    # worksheet = await async_spreadsheet.worksheet(worksheet_name)
    return worksheet


async def share_spreadsheet(async_spreadsheet: AsyncioGspreadSpreadsheet,
                            email: str, role: str = 'writer', perm_type: str = 'user', notify: bool = False):
    logger.info(f"Share {async_spreadsheet.ss.title} to {email}")
    async_spreadsheet.ss.share(email, perm_type=perm_type, role=role, notify=notify)


async def read_from_spreadsheet(google_client_manager: AsyncioGspreadClientManager,
                                spreadsheet_url: StrOrURL,
                                values_range: str):
    google_client = await google_client_manager.authorize()
    spreadsheet = await google_client.open_by_url(spreadsheet_url)
    values = spreadsheet.ss.values_get(values_range)
    return values


async def fill_in_data(worksheet: AsyncioGspreadWorksheet, data: Tuple[Tuple],
                       headers: List[str]):
    await worksheet.clear()
    headers_cells = [
        Cell(
            1, column, value=text
        ) for column, text in enumerate(headers, start=1)
    ]
    await worksheet.update_cells(
        headers_cells
    )
    # await worksheet.insert_row(headers)
    cells_list = []

    for n_row, row in enumerate(data, start=2):
        for n_col, value in enumerate(row, start=1):
            cells_list.append(
                Cell(
                    n_row, n_col, value=value
                )
            )

    await worksheet.update_cells(
        cells_list
    )
    format_header(worksheet.ws)


def format_header(worksheet: Worksheet):
    worksheet.freeze(1, 0)
    format_cell_range(
        worksheet, name='1:1',
        cell_format=CellFormat(
            borders=Borders(
                top=Border(style='SOLID_THICK'),
                bottom=Border(style='SOLID_THICK'),
                right=Border(style='SOLID'),
                left=Border(style='SOLID'),
            ),
            textFormat=TextFormat(bold=True),
            wrapStrategy='WRAP'
        )
    )


async def export_entity(Session: sessionmaker, google_client_manager: AsyncioGspreadClientManager,
                        entity: int, spreadsheet_url: StrOrURL, **kwargs):
    time_delta = kwargs.get('time_delta', 0)
    google_client = await google_client_manager.authorize()
    spreadsheet = await google_client.open_by_url(spreadsheet_url)
    worksheet_today = await spreadsheet.worksheet('Today')
    worksheet_groups = await spreadsheet.worksheet('Groups')
    worksheet_transactions = await spreadsheet.worksheet('Transactions')
    worksheet_ep_request = await spreadsheet.worksheet('EP-Request')

    op_date_time = datetime.datetime.now() - datetime.timedelta(days=time_delta)

    # entity_totals = await sea_entity_total_group_by_chat_read(op_date_time.date(), Session=Session, entity=entity)
    data = ()
    # for line in entity_totals:
    #     data += (line.account_title, line.asset_code,
    #              float(-1 * value_to_decimal(line.total_balance / 10 ** line.precision, line.precision)),
    #              float(-1 * value_to_decimal(line.total_debit / 10 ** line.precision, line.precision)),
    #              float(-1 * value_to_decimal(line.total_credit / 10 ** line.precision, line.precision))),
    if len(data):
        headers = ['Account', 'Currency', 'Total balance', 'Total debit', 'Total credit',
                   f"{op_date_time.isoformat(sep=' ', timespec='minutes')}"]
        await fill_in_data(worksheet_today, data, headers=headers)

    # entity_accounts = await sea_entity_account_read(Session=Session, entity=entity)
    # data = ()
    # for line in entity_accounts:
    #     data += (line.account.title, line.account_id),

    if len(data):
        headers = ['Group', 'Group ID', ]
        await fill_in_data(worksheet_groups, data, headers=headers)

    # entity_transactions = await sea_entity_transactions_read(
    #     Session=Session,
    #     entity=entity,
    #     first_date=op_date_time.date() - datetime.timedelta(days=1),
    #     last_date=op_date_time.date() + datetime.timedelta(days=1))
    # data = ()
    # for line in entity_transactions:
    #     sign = 1 if line.direction == 'dr' else -1
    #     data += (line.date_time.isoformat(sep=' ', timespec='seconds'),
    #              line.account_title,
    #              line.mention,
    #              line.asset_code,
    #              float(sign * value_to_decimal(line.amount / 10 ** line.precision, line.precision)),
    #              line.amount_source),

    if len(data):
        headers = ['Date', 'Group', 'User', 'Currency', 'Amount', 'Amount source']
        await fill_in_data(worksheet_transactions, data, headers=headers)

    # entity_ep_requests = await ep_entity_requests(Session, entity_id=entity, is_active=True)
    # data = ()
    # EPRequest.id,
    # account_alias.title.label('account_title'),
    # EPProvider.name.label('provider_name'),
    # EPRequest.email,
    # EPRequest.detail,
    # EPRequest.amount,
    # func.ifnull(cte_payment.c.payed_amount, 0).label('payed_amount'),
    # EPRequest.asset_code,
    # EPRequest.comment,
    # EPRequest.created_at,
    # EPRequest.updated_at
    # for line in entity_ep_requests:
    #     data += (line.id,
    #              line.account_title,
    #              line.provider_name,
    #              line.email,
    #              line.detail,
    #              float(line.amount),
    #              float(line.payed_amount),
    #              line.asset_code.upper(),
    #              line.comment,
    #              convert_datetime_to_gsheet(line.created_at),
    #              convert_datetime_to_gsheet(line.updated_at),
    #              f"/eprdel_{line.id}",
    #              f"/eprupd_{line.id}",
    #              f"/eprcmt_{line.id}",
    #              f"/eppadd_{line.id}"),
    #
    # if len(data):
    #     headers = ['ID', 'Chat', 'Provider', 'E-mail', 'Detail', 'Amount', 'Payed', 'Currency',
    #                'Comment', 'Created', 'Updated', 'Delete', 'Upd Amount', 'Set comment', 'Add payment']
    #     await fill_in_data(worksheet_ep_request, data, headers=headers)
