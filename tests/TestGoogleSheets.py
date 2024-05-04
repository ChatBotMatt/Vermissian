import unittest
from unittest import mock

import dataclasses
from typing import Dict

import requests
import logging

from src.utils.google_sheets import get_spreadsheet_id, get_spreadsheet_sheet_gid, get_spreadsheet_metadata, get_from_spreadsheet_api, check_response, get_key, get_sheet_name_from_gid
from src.utils.exceptions import ForbiddenSpreadsheetError, TooManyRequestsError

@dataclasses.dataclass
class MockResponse:
    content: Dict
    status_code: int

    def raise_for_status(self):
        if self.status_code != 200:
            raise requests.HTTPError('Mock HTTP Error')

    def json(self):
        return self.content

class TestGoogleSheets(unittest.TestCase):

    def test_get_spreadsheet_id(self):
        for label, url_data in self.valid_spreadsheet_tracker_urls.items():
            for url, expected_spreadsheet_id in url_data.items():
                with self.subTest(label, url=url):
                    self.assertEqual(
                        get_spreadsheet_id(url),
                        expected_spreadsheet_id
                    )

        for label, url in self.invalid_spreadsheet_tracker_urls.items():
            with self.subTest(label, url=url):
                self.assertEqual(
                    get_spreadsheet_id(url),
                    None
                )

    def test_get_spreadsheet_sheet_gid(self):
        for label, url_data in self.valid_spreadsheet_gids.items():
            for url, expected_gid in url_data.items():
                with self.subTest(label, url=url):
                    self.assertEqual(
                        get_spreadsheet_sheet_gid(url),
                        expected_gid
                    )

        for label, url in self.invalid_spreadsheet_gids.items():
            with self.subTest(label, url=url):
                self.assertEqual(
                    get_spreadsheet_sheet_gid(url),
                    None
                )

    @unittest.mock.patch('utils.google_sheets.get_spreadsheet_metadata')
    def test_get_sheet_name_from_gid(self, mock_metadata: mock.Mock):
        initial_test_gid = 123
        initial_test_name = 'Sheet 123'

        mock_metadata.return_value = {
            initial_test_gid: initial_test_name,
            456: 'Sheet Named 456',
            789: 'This sheet is called 789'
        }

        spreadsheet_id = '1'

        sheet_name = get_sheet_name_from_gid(spreadsheet_id=spreadsheet_id, gid=123)

        mock_metadata.assert_called_with(spreadsheet_id)

        self.assertEqual(
            sheet_name,
            initial_test_name
        )

        for gid, expected_name in mock_metadata.return_value.items():
            if gid == initial_test_gid:
                continue

            sheet_name = get_sheet_name_from_gid(spreadsheet_id=spreadsheet_id, gid=gid)

            with self.subTest(f'Assert cached - {gid}'):
                self.assertEqual(
                    mock_metadata.call_count,
                    1
                )

            with self.subTest(f'Assert correct sheet name'):
                self.assertEqual(
                    sheet_name,
                    expected_name
                )

        with self.subTest('Unknown GIDs rejected'):
            self.assertRaises(
                IndexError,
                get_sheet_name_from_gid,
                spreadsheet_id,
                55
            )

    def test_check_response(self):
        valid_spreadsheet_id = '1saogmy4eNNKng32Pf39b7K3Ko4uHEuWClm7UM-7Kd8I'

        valid_response = MockResponse(
            status_code=200,
            content={'abc': '123'}
        )

        with self.subTest('Valid Response'):
            self.assertEqual(
                check_response(valid_response, valid_spreadsheet_id),
                None
            )

        forbidden_response = MockResponse(
            status_code=403,
            content={'error': {'status': 'PERMISSION_DENIED'}}
        )

        with self.subTest('Forbidden Response'):
            self.assertRaises(
                ForbiddenSpreadsheetError,
                check_response,
                forbidden_response,
                valid_spreadsheet_id
            )

        overloaded_response = MockResponse(
            status_code=429,
            content={'error': {'status': 'RESOURCE_EXHAUSTED'}}
        )

        with self.subTest('Overloaded Response'):
            self.assertRaises(
                TooManyRequestsError,
                check_response,
                overloaded_response,
                valid_spreadsheet_id
            )

        invalid_response = MockResponse(
            status_code=500,
            content={'error': {'status': 'PERMISSION_DENIED'}}
        )

        with self.subTest('Invalid Response'):
            self.assertRaises(
                requests.HTTPError,
                check_response,
                invalid_response,
                valid_spreadsheet_id
            )

        forbidden_response_wrong_message = MockResponse(
            status_code=403,
            content={'error': {'status': 'abc'}}
        )

        with self.subTest('Forbidden Response - Wrong message'):
            self.assertRaises(
                requests.HTTPError,
                check_response,
                forbidden_response_wrong_message,
                valid_spreadsheet_id
            )

    @mock.patch('src.utils.google_sheets.requests.get', autospec=True)
    @mock.patch('src.utils.google_sheets.get_key', autospec=True)
    def test_get_spreadsheet_metadata(self, mock_get_key: mock.Mock, mock_requests_get: mock.Mock):
        mock_key = '123'
        mock_get_key.return_value = mock_key

        valid_spreadsheet_id = '1saogmy4eNNKng32Pf39b7K3Ko4uHEuWClm7UM-7Kd8I'

        mock_requests_get.return_value = MockResponse(
            status_code=200,
            content={
                'sheets': [
                    {
                        'properties': {
                            'sheetId': 123,
                            'title': 'abc'
                        }
                    },
                    {
                        'properties': {
                            'sheetId': 456,
                            'title': 'def'
                        }
                    }
                ]
            }
        )

        get_spreadsheet_metadata(valid_spreadsheet_id)

        with self.subTest('get_key called'):
            mock_get_key.assert_called()

        with self.subTest('Metadata Call made'):
            mock_requests_get.assert_called_with(f'https://sheets.googleapis.com/v4/spreadsheets/{valid_spreadsheet_id}?key={mock_key}&fields=sheets.properties')

        with self.subTest('Metadata Call - Valid Data'):
            self.assertEqual(
                get_spreadsheet_metadata(valid_spreadsheet_id),
                {
                    123: 'abc',
                    456: 'def'
                }
            )

        mock_requests_get.return_value = MockResponse(
            status_code=403,
            content={
                'error': {
                    'status': 'PERMISSION_DENIED'
                }
            }
        )

        with self.subTest('Metadata Call - Permission Denied'):
            self.assertRaises(
                ForbiddenSpreadsheetError,
                get_spreadsheet_metadata,
                valid_spreadsheet_id
            )

        mock_requests_get.return_value = MockResponse(
            status_code=429,
            content={
                'error': {
                    'status': 'RESOURCE_EXHAUSTED'
                }
            }
        )

        with self.subTest('Metadata Call - Too Many Requests'):
            self.assertRaises(
                TooManyRequestsError,
                get_spreadsheet_metadata,
                valid_spreadsheet_id
            )

        mock_requests_get.return_value = MockResponse(
            status_code=404,
            content={
                'error': {
                    'status': 'PERMISSION_DENIED'
                }
            }
        )

        with self.subTest('Metadata Call - 404 Permissions Error'):
            self.assertRaises(
                requests.HTTPError,
                get_spreadsheet_metadata,
                valid_spreadsheet_id
            )

        mock_requests_get.return_value = MockResponse(
            status_code=403,
            content={
                'error': {
                    'status': 'abc'
                }
            }
        )

        with self.subTest('Metadata Call - 403 Non-Permissions Error'):
            self.assertRaises(
                requests.HTTPError,
                get_spreadsheet_metadata,
                valid_spreadsheet_id
            )

        mock_requests_get.return_value = MockResponse(
            status_code=500,
            content={
                'error': {
                    'status': 'abc'
                }
            }
        )

        with self.subTest('Metadata Call - 500 Non-Permissions Error'):
            self.assertRaises(
                requests.HTTPError,
                get_spreadsheet_metadata,
                valid_spreadsheet_id
            )

    @mock.patch('src.utils.google_sheets.requests.get', autospec=True)
    @mock.patch('src.utils.google_sheets.get_key', autospec=True)
    def test_get_from_spreadsheet_api(self, mock_get_key: mock.Mock, mock_requests_get: mock.Mock):
        valid_spreadsheet_id = '1saogmy4eNNKng32Pf39b7K3Ko4uHEuWClm7UM-7Kd8I'
        valid_sheet_name = 'Example Character Sheet'

        mock_key = '123'
        mock_get_key.return_value = mock_key

        valid_ranges_cells = [
            'A1',
            'B2',
            'A9500',
            'E67',
            'A3:B7',
            'B7:A3'
        ]

        for valid_range_cell in valid_ranges_cells:
            with self.subTest(range_cell=valid_range_cell):
                data_range = f'{valid_sheet_name}!{valid_range_cell}'

                get_from_spreadsheet_api(
                    spreadsheet_id=valid_spreadsheet_id,
                    raw_sheet_name_data={
                        valid_sheet_name: valid_range_cell
                    }
                )

                mock_requests_get.assert_called_with(f'https://sheets.googleapis.com/v4/spreadsheets/{valid_spreadsheet_id}/values/{data_range}?key={mock_key}')

        with self.subTest(all_range_cells=valid_ranges_cells):

            range_expression = '&'.join([
                f'ranges={valid_sheet_name}!{valid_cell_range}' for valid_cell_range in valid_ranges_cells
            ])

            get_from_spreadsheet_api(
                spreadsheet_id=valid_spreadsheet_id,
                raw_sheet_name_data={
                    valid_sheet_name: valid_ranges_cells
                }
            )

            mock_requests_get.assert_called_with(f'https://sheets.googleapis.com/v4/spreadsheets/{valid_spreadsheet_id}/values:batchGet?key={mock_key}&{range_expression}')

        mock_ranges_cells =  [
            'A1',
            'B2',
            'A9500',
            'E67',
            'A1:B2',
            'B2:A1'
        ]

        mock_multi_range_cell_return_data = {
            'A1': 1,
            'B2': 2,
            'A9500': 3,
            'E67': 4,
            'A1:B2': [
                [1, 2]
            ],
            'B2:A1': [
                [1, 2]
            ]
        }

        mock_requests_get.return_value = MockResponse(
            status_code=200,
            content={
                'valueRanges': [
                    {
                        'values': mock_multi_range_cell_return_data[cell_range] if isinstance(mock_multi_range_cell_return_data[cell_range], list) else [ [ mock_multi_range_cell_return_data[cell_range] ] ]
                    }  for cell_range in mock_ranges_cells
                ]
            }
        )

        with self.subTest('Test response parsing - multiple cells and ranges'):
            data_gotten = get_from_spreadsheet_api(
                spreadsheet_id=valid_spreadsheet_id,
                raw_sheet_name_data={
                    valid_sheet_name: mock_ranges_cells
                }
            )

            self.assertEqual(
                data_gotten[valid_sheet_name],
                mock_multi_range_cell_return_data
            )

        mock_single_cell_return_data = {
            'A1': 1
        }

        mock_requests_get.return_value = MockResponse(
            status_code=200,
            content={
                'values': [
                    [1]
                ]
            }
        )

        with self.subTest('Test response parsing - single cell'):
            data_gotten = get_from_spreadsheet_api(
                spreadsheet_id=valid_spreadsheet_id,
                raw_sheet_name_data={
                    valid_sheet_name: 'A1'
                }
            )

            self.assertEqual(
                data_gotten[valid_sheet_name],
                mock_single_cell_return_data
            )

        mock_single_cell_return_data = {
            'A1:B2': [[1, 2]]
        }

        mock_requests_get.return_value = MockResponse(
            status_code=200,
            content={
                'values': [
                    [1, 2]
                ]
            }
        )

        with self.subTest('Test response parsing - single range'):
            data_gotten = get_from_spreadsheet_api(
                spreadsheet_id=valid_spreadsheet_id,
                raw_sheet_name_data={
                    valid_sheet_name: 'A1:B2'
                }
            )

            self.assertEqual(
                data_gotten[valid_sheet_name],
                mock_single_cell_return_data
            )

        mock_multi_sheet_return_data = {
            'Character 1': {
                'A1:B2': [1, 2]
            },
            'Character 2': {
                'A2:B3': [3, 4]
            }
        }

        mock_requests_get.return_value = MockResponse(
            status_code=200,
            content={
                'valueRanges': [
                    {'values': [1, 2]},
                    {'values': [3, 4]}
                ]
            }
        )

        with self.subTest('Test response parsing - multi-sheet ranges'):
            data_gotten = get_from_spreadsheet_api(
                spreadsheet_id=valid_spreadsheet_id,
                raw_sheet_name_data={
                    'Character 1': 'A1:B2',
                    'Character 2': 'A2:B3'
                }
            )

            self.assertEqual(
                data_gotten,
                mock_multi_sheet_return_data
            )

        mock_single_cell_return_data = {
            'B2:A1': [[1, 2]]
        }

        mock_requests_get.return_value = MockResponse(
            status_code=200,
            content={
                'values': [
                    [1, 2]
                ]
            }
        )

        with self.subTest('Test response parsing - single backwards range'):
            data_gotten = get_from_spreadsheet_api(
                spreadsheet_id=valid_spreadsheet_id,
                raw_sheet_name_data={
                    valid_sheet_name: 'B2:A1'
                }
            )

            self.assertEqual(
                data_gotten[valid_sheet_name],
                mock_single_cell_return_data
            )

        with self.subTest('None ranges_or_cells'):
            self.assertRaises(
                ValueError,
                get_from_spreadsheet_api,
                valid_spreadsheet_id,
                {valid_sheet_name: None},
            )

        with self.subTest('List of None ranges_or_cells'):
            self.assertRaises(
                ValueError,
                get_from_spreadsheet_api,
                valid_spreadsheet_id,
                {valid_sheet_name: [None]},
            )

        malformed_ranges_and_cells = [
            None,
            '123',
            'abc',
            'a1',
            '1a',
            'a',
            '1',
            1,
            [],
            ['A1', 'B2', '123']
        ]

        for malformed in malformed_ranges_and_cells:
            with self.subTest('Malformed wrapped ranges_or_cells', malformed=malformed):
                self.assertRaises(
                    ValueError,
                    get_from_spreadsheet_api,
                    valid_spreadsheet_id,
                    {valid_sheet_name: [malformed]},
                )

            with self.subTest('Malformed ranges_or_cells', malformed=malformed):
                self.assertRaises(
                    ValueError,
                    get_from_spreadsheet_api,
                    valid_spreadsheet_id,
                    {valid_sheet_name: malformed},
                )

    @mock.patch('src.utils.google_sheets.json.load')
    def test_get_key(self, mock_json_load: mock.Mock):
        with self.subTest('Reads file'):
            original_key = get_key()

            mock_json_load.assert_called()

        with self.subTest('Caches result'):
            second_key = get_key()

            self.assertEqual(
                mock_json_load.call_count,
                1
            )

            with self.subTest('Key is consistent'):
                self.assertEqual(
                    original_key,
                    second_key
                )

    def setUp(self) -> None:
        if hasattr(get_key, 'key'):
            # TODO Ideally should be mocked for all of them anyway
            delattr(get_key, 'key') # In case a previous test case has made it cached

        logging.disable(logging.ERROR)

    def tearDown(self) -> None:
        if hasattr(get_key, 'key'):
            delattr(get_key, 'key')  # In case a previous test case has made it cached

        logging.disable(logging.NOTSET)

    @classmethod
    def setUpClass(cls) -> None:
        cls.valid_spreadsheet_tracker_urls = {
            'spire': {
                'https://docs.google.com/spreadsheets/d/1saogmy4eNNKng32Pf39b7K3Ko4uHEuWClm7UM-7Kd8I/edit#gid=0': '1saogmy4eNNKng32Pf39b7K3Ko4uHEuWClm7UM-7Kd8I'
            },

            'spire_no_gid': {
                'https://docs.google.com/spreadsheets/d/1saogmy4eNNKng32Pf39b7K3Ko4uHEuWClm7UM-7Kd8I/edit': '1saogmy4eNNKng32Pf39b7K3Ko4uHEuWClm7UM-7Kd8I'
            },

            'heart': {
                'https://docs.google.com/spreadsheets/d/1PzF3ZHQpXXaS0ci0Q0vbE9uHpC26GiUJ4ishIbbcpOY/edit#gid=0': '1PzF3ZHQpXXaS0ci0Q0vbE9uHpC26GiUJ4ishIbbcpOY'
            },

            'heart_no_gid': {
                'https://docs.google.com/spreadsheets/d/1PzF3ZHQpXXaS0ci0Q0vbE9uHpC26GiUJ4ishIbbcpOY/edit': '1PzF3ZHQpXXaS0ci0Q0vbE9uHpC26GiUJ4ishIbbcpOY'
            }
        }

        cls.valid_spreadsheet_gids = {
            'spire': {
                'https://docs.google.com/spreadsheets/d/1saogmy4eNNKng32Pf39b7K3Ko4uHEuWClm7UM-7Kd8I/edit#gid=0': 0
            },

            'heart': {
                'https://docs.google.com/spreadsheets/d/1PzF3ZHQpXXaS0ci0Q0vbE9uHpC26GiUJ4ishIbbcpOY/edit#gid=211': 211
            },
        }

        cls.invalid_spreadsheet_tracker_urls = {
            'garbage': 'abcd',
            'random_url': 'google.com',
            'random_url_full': 'https://google.com',
            # 'random_url_right_form': 'https://google.com/spreadsheets/d/1saogmy4eNNKng32Pf39b7K3Ko4uHEuWClm7UM-7Kd8I/edit#gid=0', # TODO Not a valid URL, but not the right place to check that
            'incomplete': 'https://docs.google.com/spreadsheets/d/',
            'missing_id': 'https://docs.google.com/spreadsheets/d//edit#gid=0'
        }

        cls.invalid_spreadsheet_gids = {
            'no_gid_param': 'https://docs.google.com/spreadsheets/d/1saogmy4eNNKng32Pf39b7K3Ko4uHEuWClm7UM-7Kd8I/edit',

            'no_gid_value': 'https://docs.google.com/spreadsheets/d/1PzF3ZHQpXXaS0ci0Q0vbE9uHpC26GiUJ4ishIbbcpOY/edit#gid=',

            'no_gid_value_no_equals': 'https://docs.google.com/spreadsheets/d/1PzF3ZHQpXXaS0ci0Q0vbE9uHpC26GiUJ4ishIbbcpOY/edit#gid',

            'non_numeric_gid': 'https://docs.google.com/spreadsheets/d/1PzF3ZHQpXXaS0ci0Q0vbE9uHpC26GiUJ4ishIbbcpOY/edit#gid=abc',

            'mixed_gid': 'https://docs.google.com/spreadsheets/d/1PzF3ZHQpXXaS0ci0Q0vbE9uHpC26GiUJ4ishIbbcpOY/edit#gid=123abc',

            'mixed_gid_letters_first': 'https://docs.google.com/spreadsheets/d/1PzF3ZHQpXXaS0ci0Q0vbE9uHpC26GiUJ4ishIbbcpOY/edit#gid=abc123'
        }

if __name__ == '__main__':
    unittest.main()