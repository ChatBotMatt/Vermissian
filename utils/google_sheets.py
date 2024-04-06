import datetime

import requests
import json
import re
from urllib.parse import urlparse
from dateutil.parser import isoparse
import time
from typing import List, Dict, Union, Optional

from utils.exceptions import ForbiddenSpreadsheetError
from utils.logger import get_logger

def get_key():
    if not hasattr(get_key, 'key'):
        with open('credentials.json', 'r') as f:
            credentials = json.load(f)

            get_key.key = credentials['google_sheets_api_key']

    return get_key.key

def get_spreadsheet_id(spreadsheet_url: str) -> Optional[str]:
    tokens = urlparse(spreadsheet_url).path.split('/')  # TODO Check for if we need to sanitise this

    spreadsheet_id = None
    for idx, token in enumerate(tokens):
        if token == 'd' and idx < len(tokens) - 1:
            spreadsheet_id = tokens[idx + 1]
            break

    return spreadsheet_id

def get_spreadsheet_sheet_gid(spreadsheet_url: str) -> Optional[int]:
    gid_match = re.search('gid=(\d+)', spreadsheet_url)

    if gid_match is None:
        return None
    else:
        return int(gid_match.group(1))

def get_sheet_name_from_gid(spreadsheet_id: str, gid: int, force: bool = False):
    if force or not hasattr(get_sheet_name_from_gid, 'metadata'):
        get_sheet_name_from_gid.metadata = get_spreadsheet_metadata(spreadsheet_id)

    if gid in get_sheet_name_from_gid.metadata:
        return get_sheet_name_from_gid.metadata[gid]
    else:
        raise IndexError(f'Cannot find "{gid}" in the known spreadsheets: {get_sheet_name_from_gid.metadata}.')

def get_spreadsheet_metadata(spreadsheet_id: str) -> Dict[int, str]:
    logger = get_logger()

    key = get_key()

    try:
        response = requests.get(f'https://sheets.googleapis.com/v4/spreadsheets/{spreadsheet_id}?key={key}&fields=sheets.properties')

        if response.status_code == 403 and response.json()['error']['status'] == 'PERMISSION_DENIED':
            raise ForbiddenSpreadsheetError(spreadsheet_id=spreadsheet_id)

        response.raise_for_status()

        return {
            sheet['properties']['sheetId']: sheet['properties']['title'] for sheet in response.json()['sheets']
        }

    except requests.HTTPError as h:
        logger.error(h, exc_info=True)

        raise h

def get_from_spreadsheet_api(spreadsheet_id: str, sheet_name: str, ranges_or_cells: Union[str, List[str]]) -> Dict[str, Optional[Union[str, int, float]]]:
    logger = get_logger()

    if isinstance(ranges_or_cells, str):
        ranges_or_cells = [ranges_or_cells]

    if len(ranges_or_cells) == 0:
        raise ValueError(f'Must pass at least one range or cell to query.')

    start_time = time.time()

    key = get_key()

    try:
        if len(ranges_or_cells) == 1:
            data_range = f'{sheet_name}!{ranges_or_cells[0]}'

            response = requests.get(f'https://sheets.googleapis.com/v4/spreadsheets/{spreadsheet_id}/values/{data_range}?key={key}')
        else:
            range_expression_tokens = []

            for range_or_cell in ranges_or_cells:
                range_expression_tokens.append(f'ranges={sheet_name}!{range_or_cell}')

            range_expression = '&'.join(range_expression_tokens)

            response = requests.get(f'https://sheets.googleapis.com/v4/spreadsheets/{spreadsheet_id}/values:batchGet?key={key}&{range_expression}')

        if response.status_code == 403 and response.json()['error']['status'] == 'PERMISSION_DENIED':
            raise ForbiddenSpreadsheetError(spreadsheet_id=spreadsheet_id)

        response.raise_for_status()

        logger.debug(f'Duration: {time.time() - start_time}')

        response_json = response.json()

        if len(ranges_or_cells) == 1:
            raw_response_data = [ response_json ]
        else:
            raw_response_data = response_json['valueRanges']

        response_data = {}
        for range_or_cell, response_datum in zip(ranges_or_cells, raw_response_data):
            if 'values' in response_datum:
                is_range = ( ':' in range_or_cell )

                if is_range:
                    response_data[range_or_cell] = response_datum['values']
                else:
                    response_data[range_or_cell] = response_datum['values'][0][0]
            else:
                response_data[range_or_cell] = None

        return response_data

    except requests.HTTPError as h:
        logger.error(h, exc_info=True)

        raise h
