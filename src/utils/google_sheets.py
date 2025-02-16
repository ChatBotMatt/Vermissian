import string

import requests
from urllib.parse import urlparse

import json
import re
import collections
import time
from string import ascii_uppercase
from typing import List, Dict, Union, Optional

from src.utils.exceptions import ForbiddenSpreadsheetError, TooManyRequestsError
from src.utils.logger import get_logger

def get_key():
    if not hasattr(get_key, 'key'):
        with open('credentials_vermissian.json', 'r') as f:
            credentials = json.load(f)

            get_key.key = credentials['google_sheets_api_key']

    return get_key.key

def get_spreadsheet_id(spreadsheet_url: str) -> Optional[str]:
    tokens = urlparse(spreadsheet_url).path.split('/')  # TODO Check for if we need to sanitise this

    spreadsheet_id = None
    for idx, token in enumerate(tokens):
        if token == 'd' and idx < len(tokens) - 1 and len(tokens[idx+1].strip()):
            spreadsheet_id = tokens[idx + 1]

            break

    return spreadsheet_id

def get_spreadsheet_sheet_gid(spreadsheet_url: str) -> Optional[int]:
    gid_match = re.search('gid=(\d+)$', spreadsheet_url)

    if gid_match is None:
        return None
    else:
        return int(gid_match.group(1))

def get_sheet_name_from_gid(spreadsheet_id: str, gid: int, force: bool = False):
    if force or not hasattr(get_sheet_name_from_gid, 'metadata'):
        get_sheet_name_from_gid.metadata = {}

    if spreadsheet_id not in get_sheet_name_from_gid.metadata:
        get_sheet_name_from_gid.metadata[spreadsheet_id] = get_spreadsheet_metadata(spreadsheet_id)

    if gid in get_sheet_name_from_gid.metadata[spreadsheet_id]:
        return get_sheet_name_from_gid.metadata[spreadsheet_id][gid]
    else:
        raise IndexError(f'Cannot find GID "{gid}" in the known spreadsheets: {get_sheet_name_from_gid.metadata}.')

def get_spreadsheet_metadata(spreadsheet_id: str) -> Dict[int, str]:
    logger = get_logger()

    key = get_key()

    try:
        response = requests.get(f'https://sheets.googleapis.com/v4/spreadsheets/{spreadsheet_id}?key={key}&fields=sheets.properties')

        check_response(response, spreadsheet_id)

        return {
            sheet['properties']['sheetId']: sheet['properties']['title'] for sheet in response.json()['sheets']
        }

    except requests.HTTPError as h:
        logger.error(h, exc_info=True)

        raise h

def check_response(response: requests.Response, spreadsheet_id: str):
    if response.status_code == 403 and response.json()['error']['status'] == 'PERMISSION_DENIED':
        raise ForbiddenSpreadsheetError(spreadsheet_id=spreadsheet_id)
    elif response.status_code == 429 and response.json()['error']['status'] == 'RESOURCE_EXHAUSTED':
        raise TooManyRequestsError()

    response.raise_for_status()

def check_is_valid_range_or_cell(range_or_cell):
    single_cell_regex = '[A-Z]+\d+'
    cell_range_regex = f'{single_cell_regex}:{single_cell_regex}'

    if not isinstance(range_or_cell, str):
        raise ValueError(f'range_or_cell must be str, not {range_or_cell}')
    elif not re.fullmatch(single_cell_regex, range_or_cell) and not re.fullmatch(cell_range_regex, range_or_cell):
        raise ValueError(f'Malformed range_or_cell: "{range_or_cell}"')

def _compute_num_new_columns(current_column: int, current_column_offset: int) -> int:
    if current_column_offset == 0:
        return 0

    if current_column_offset < 0:
        raise ValueError(f'Does not yet handle negatives.') # TODO

    if 0 < current_column + current_column_offset < len(string.ascii_uppercase):
        return 0

    num_new_columns = int( (current_column + current_column_offset) / len(string.ascii_uppercase) )

    return num_new_columns

def column_offset_to_column_name(column: int):
    """
    From https://stackoverflow.com/a/71155186, adapted to use string.ascii_uppercase rather than chr
    """

    if column < 0:
        return ""

    quotient, remainder = divmod(column, 26)

    return column_offset_to_column_name(quotient - 1) + string.ascii_uppercase[remainder]

def _compute_new_column_alpha(current_column_alpha: str, current_column_offset: int) -> str:

    sum_column_index = sum([ascii_uppercase.index(subcolumn) for subcolumn in current_column_alpha]) + (26 * (len(current_column_alpha) - 1))

    new_column_index = sum_column_index + current_column_offset

    if new_column_index < 0:
        raise ValueError(
                f'Invalid combination of column "{current_column_alpha}" and column offset "{current_column_offset}" '
                f'given column "{current_column_alpha}" - cannot go back past column 1.'
            )

    return column_offset_to_column_name(new_column_index)

def _compute_new_row(current_row: int, current_row_offset: int) -> int:
    if current_row_offset == 0:
        return current_row

    new_row = current_row + current_row_offset

    return new_row

def offset_reference(reference: str, column_offset: int, row_offset: int) -> str:
    match = re.fullmatch('([A-Z]+)([0-9]+)', reference)

    if match is None:
        raise ValueError(f'Invalid sheet reference "{reference}": It should be capital letters followed by numbers.')

    if column_offset == 0 and row_offset == 0:
        return reference

    column_alpha = match.group(1)
    row = int(match.group(2))

    if row + row_offset <= 0:
        raise ValueError(f'Invalid combination of sheet reference "{reference}" and row offset "{row_offset}" given row "{row}" - cannot go above row 1.')

    new_column_alpha = _compute_new_column_alpha(column_alpha, column_offset)
    new_row = _compute_new_row(row, row_offset)

    new_reference = new_column_alpha + str(new_row)

    return new_reference

def get_from_spreadsheet_api(
    spreadsheet_id: str,
    raw_sheet_name_data: Dict[str, Union[str, List[str]]]
) -> Dict[str, Dict[str, Optional[Union[str, int, float]]]]:
    logger = get_logger()

    all_ranges_or_cells = []

    for sheet_name, raw_ranges_or_cells in raw_sheet_name_data.items():
        sheet_name = sheet_name.replace('/', '%2F') # Doesn't get encoded properly otherwise. # TODO Test?

        if isinstance(raw_ranges_or_cells, list):
            for raw_range_or_cell in raw_ranges_or_cells:
                check_is_valid_range_or_cell(raw_range_or_cell)

                all_ranges_or_cells.append(f'{sheet_name}!{raw_range_or_cell}')
        elif isinstance(raw_ranges_or_cells, str):
            check_is_valid_range_or_cell(raw_ranges_or_cells)

            all_ranges_or_cells.append(f'{sheet_name}!{raw_ranges_or_cells}')
        else:
            raise ValueError(f'Non-str non-list ranges_or_cells "{raw_ranges_or_cells}" inside "{sheet_name}" cannot be passed in.')

    if len(all_ranges_or_cells) == 0:
        raise ValueError(f'Must pass at least one range or cell to query.')

    start_time = time.time()

    key = get_key()

    try:
        if len(all_ranges_or_cells) == 1:
            url = f'https://sheets.googleapis.com/v4/spreadsheets/{spreadsheet_id}/values/{all_ranges_or_cells[0]}?key={key}'
        else:
            range_expression_tokens = []

            for range_or_cell in all_ranges_or_cells:
                range_expression_tokens.append(f'ranges={range_or_cell}')

            range_expression = '&'.join(range_expression_tokens)

            url = f'https://sheets.googleapis.com/v4/spreadsheets/{spreadsheet_id}/values:batchGet?key={key}&{range_expression}'

        logger.info(url)

        response = requests.get(url)

        check_response(response, spreadsheet_id)

        logger.debug(f'Duration: {time.time() - start_time}')

        response_json = response.json()

        if len(all_ranges_or_cells) == 1:
            raw_response_data = [ response_json ]
        else:
            raw_response_data = response_json['valueRanges']

        response_data = collections.defaultdict(dict)
        for sheet_range_or_cell, response_datum in zip(all_ranges_or_cells, raw_response_data):
            sheet_name, range_or_cell = sheet_range_or_cell.split('!')

            sheet_name = sheet_name.replace('%2F', '/')

            if 'values' in response_datum:
                is_range = ( ':' in range_or_cell )

                if is_range:
                    response_data[sheet_name][range_or_cell] = response_datum['values']
                else:
                    response_data[sheet_name][range_or_cell] = response_datum['values'][0][0]
            else:
                response_data[sheet_name][range_or_cell] = None

        logger.info(url, response_json, response_data)

        return response_data

    except requests.HTTPError as h:
        logger.error(h, exc_info=True)

        raise h
