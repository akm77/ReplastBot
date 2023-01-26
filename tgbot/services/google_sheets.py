import asyncio
import logging
from dataclasses import dataclass
from typing import Tuple, List

from aiohttp.typedefs import StrOrURL
from gspread import Cell, Worksheet
from gspread_asyncio import AsyncioGspreadClient, AsyncioGspreadSpreadsheet, AsyncioGspreadWorksheet, \
    AsyncioGspreadClientManager
from gspread_formatting import CellFormat, Borders, Border, TextFormat, format_cell_range
from sqlalchemy.orm import sessionmaker

from tgbot.misc.utils import convert_date_to_gsheet
from tgbot.models.erp_shift_staff_activity import shift_activity_list, shift_material_intake_list, shift_production_list, \
    shift_bags_list, staff_time_sheet

logger = logging.getLogger(__name__)


@dataclass
class Worksheets:
    TITLES = ["Пр-во", "БД пр-во"]


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
        worksheet,
        name='1:1',
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


async def export_production(Session: sessionmaker, google_client_manager: AsyncioGspreadClientManager,
                            spreadsheet_url: StrOrURL, **kwargs):
    google_client = await google_client_manager.authorize()
    spreadsheet = await google_client.open_by_url(spreadsheet_url)
    worksheet_db = await spreadsheet.worksheet("БД пр-во")
    # convert_date_to_gsheet(date: datetime.date, / )
    production_db = await asyncio.gather(shift_activity_list(Session),
                                         shift_material_intake_list(Session),
                                         shift_production_list(Session),
                                         shift_bags_list(Session),
                                         staff_time_sheet(Session))

    activity_list_header_range = "A1:C1"
    activity_list_header_values = [["shift_date", "name", "quantity"]]
    activity_list_range = "A2:C"
    activity_list = [[convert_date_to_gsheet(row.shift_date), row.name, float(row.quantity)]
                     for row in production_db[0]]

    material_intake_list_header_range = "E1:H1"
    material_intake_list_header_values = [["shift_date", "name", "state", "quantity"]]
    material_intake_list_range = "E2:H"
    material_intake_list = [[convert_date_to_gsheet(row.shift_date), row.name, row.state, float(row.quantity)]
                            for row in production_db[1]]

    production_list_header_range = "J1:N1"
    production_list_header_values = [["shift_date", "name", "state", "bag_num", "quantity"]]
    production_list_range = "J2:N"
    production_list = [[convert_date_to_gsheet(row.shift_date), row.name, row.state, row.bag_num,
                        float(row.quantity) if row.quantity else row.quantity]
                       for row in production_db[2]]

    bags_list_header_range = "P1:R1"
    bags_list_header_values = [["shift_date", "shift_number", "bag_num"]]
    bags_list_range = "P2:R"
    bags_list = [[convert_date_to_gsheet(row.shift_date), row.shift_number, row.bag_num] for row in production_db[3]]

    time_sheet_header_range = "T1:X1"
    time_sheet_header_values = [["name", "shift_date", "shift_number", "duration", "hours_worked"]]
    time_sheet_range = "T2:X"
    time_sheet = [[row.name, convert_date_to_gsheet(row.shift_date), row.shift_number,
                   float(row.duration) if row.duration else None,
                   float(row.hours_worked) if row.hours_worked else None]
                  for row in production_db[4]]

    await worksheet_db.clear()
    await worksheet_db.batch_update([{
        'range': activity_list_header_range,
        'values': activity_list_header_values,
    }, {
        'range': material_intake_list_header_range,
        'values': material_intake_list_header_values,
    }, {
        'range': production_list_header_range,
        'values': production_list_header_values,
    }, {
        'range': bags_list_header_range,
        'values': bags_list_header_values,
    }, {
        'range': time_sheet_header_range,
        'values': time_sheet_header_values,
    }])

    await worksheet_db.batch_update([{
        'range': activity_list_range,
        'values': activity_list,
    }, {
        'range': material_intake_list_range,
        'values': material_intake_list,
    }, {
        'range': production_list_range,
        'values': production_list,
    }, {
        'range': bags_list_range,
        'values': bags_list,
    }, {
        'range': time_sheet_range,
        'values': time_sheet,
    }])
