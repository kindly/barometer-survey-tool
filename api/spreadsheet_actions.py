import json

import gspread
from django.conf import settings
from google.oauth2.service_account import Credentials
from gspread.utils import absolute_range_name

service_account_data = json.loads(settings.GOOGLE_SERVICE_ACCOUNT)

scopes = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

credentials = Credentials.from_service_account_info(service_account_data, scopes=scopes)

gc = gspread.authorize(credentials)


def sheets_data(spreadsheet, sheets, id_name="id"):

    spreadsheet = gc.open_by_key(spreadsheet)

    all_data = spreadsheet.values_batch_get(sheets)

    sheets_data = {}

    for num, value_range in enumerate(all_data["valueRanges"]):
        headings = value_range["values"][0]
        records = []
        for line in value_range["values"][1:]:
            records.append(dict(zip(headings, line)))
        records_by_id = {}
        id_to_row_number = {}
        for row_num, line in enumerate(records):
            line_id = line.get(id_name)
            if line_id:
                records_by_id[line_id] = line
                id_to_row_number[line_id] = row_num

        sheets_data[sheets[num]] = {
            "headings": headings,
            "records": records,
            "records_by_id": records_by_id,
            "data": value_range["values"][1:],
            "count": len(value_range["values"][1:]),
            "id_to_row_number": id_to_row_number,
        }
    return sheets_data


def insert_row(spreadsheet, sheet, row, sheet_data=None, id_name="id"):

    if not sheet_data:
        sheet_data = sheets_data(spreadsheet, [sheet])[sheet]

    new_row = {heading: "" for heading in sheet_data["headings"]}

    for key, value in row.items():
        if key not in new_row:
            continue
        new_row[key] = value

    new_row_id = new_row.get(id_name)

    insert_index = None
    if new_row_id in sheet_data["id_to_row_number"]:
        insert_index = sheet_data["id_to_row_number"][new_row_id] + 1

    spreadsheet = gc.open_by_key(spreadsheet)

    if insert_index:
        range_label = absolute_range_name(sheet, "A%s" % (insert_index + 1))

        params = {"valueInputOption": "RAW"}

        body = {
            "majorDimension": "ROWS",
            "values": [[value for value in new_row.values()]],
        }

        return spreadsheet.values_update(range_label, params, body)

    else:
        params = {
            'valueInputOption': "RAW",
        }

        body = {'values': [[value for value in new_row.values()]]}

        return spreadsheet.values_append(sheet, params, body)


def delete_row(spreadsheet, sheet, id, sheet_data=None, id_name="id"):

    if not sheet_data:
        sheet_data = sheets_data(spreadsheet, [sheet])[sheet]

    delete_index = None
    if id in sheet_data["id_to_row_number"]:
        delete_index = sheet_data["id_to_row_number"][id] + 1

    spreadsheet = gc.open_by_key(spreadsheet)

    if delete_index:
        worksheet = spreadsheet.worksheet(sheet)
        worksheet.delete_rows(delete_index+1)

