import unittest
from unittest import mock

import dataclasses
from typing import Dict

import requests

from utils.google_sheets import get_spreadsheet_id, get_spreadsheet_sheet_gid, get_spreadsheet_metadata, get_from_spreadsheet_api, check_response
from utils.exceptions import ForbiddenSpreadsheetError

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

    def test_get_spreadsheet_gid(self):
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

    @mock.patch('utils.google_sheets.requests.get', autospec=True)
    @mock.patch('utils.google_sheets.get_key', autospec=True)
    def test_get_spreadsheet_metadata(self, mock_get_key: mock.Mock, mock_requests_get: mock.Mock):
        mock_key = '123'
        mock_get_key.return_value = mock_key

        valid_spreadsheet_id = '1saogmy4eNNKng32Pf39b7K3Ko4uHEuWClm7UM-7Kd8I'

        get_spreadsheet_metadata(valid_spreadsheet_id)

        with self.subTest('get_key called'):
            mock_get_key.assert_called()

        with self.subTest('Metadata Call made'):
            mock_requests_get.assert_called_with(f'https://sheets.googleapis.com/v4/spreadsheets/{valid_spreadsheet_id}?key={mock_key}&fields=sheets.properties')

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

    @mock.patch('utils.google_sheets.requests.get', autospec=True)
    @mock.patch('utils.google_sheets.get_key', autospec=True)
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

                get_from_spreadsheet_api(spreadsheet_id=valid_spreadsheet_id, sheet_name=valid_sheet_name, ranges_or_cells=valid_range_cell)

                mock_requests_get.assert_called_with(f'https://sheets.googleapis.com/v4/spreadsheets/{valid_spreadsheet_id}/values/{data_range}?key={mock_key}')

        with self.subTest(all_range_cells=valid_ranges_cells):

            range_expression = '&'.join([
                f'ranges={valid_sheet_name}!{valid_cell_range}' for valid_cell_range in valid_ranges_cells
            ])

            get_from_spreadsheet_api(spreadsheet_id=valid_spreadsheet_id, sheet_name=valid_sheet_name, ranges_or_cells=valid_ranges_cells)

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
            data_gotten = get_from_spreadsheet_api(valid_spreadsheet_id, valid_sheet_name, mock_ranges_cells)

            self.assertEqual(
                data_gotten,
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
            data_gotten = get_from_spreadsheet_api(valid_spreadsheet_id, valid_sheet_name, 'A1')

            self.assertEqual(
                data_gotten,
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
            data_gotten = get_from_spreadsheet_api(valid_spreadsheet_id, valid_sheet_name, 'A1:B2')

            self.assertEqual(
                data_gotten,
                mock_single_cell_return_data
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
            data_gotten = get_from_spreadsheet_api(valid_spreadsheet_id, valid_sheet_name, 'B2:A1')

            self.assertEqual(
                data_gotten,
                mock_single_cell_return_data
            )

        with self.subTest('None ranges_or_cells'):
            self.assertRaises(
                ValueError,
                get_from_spreadsheet_api,
                valid_spreadsheet_id,
                valid_sheet_name,
                None
            )

        with self.subTest('List of None ranges_or_cells'):
            self.assertRaises(
                ValueError,
                get_from_spreadsheet_api,
                valid_spreadsheet_id,
                valid_sheet_name,
                [None]
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
            with self.subTest('Malformed ranges_or_cells', malformed=malformed):
                self.assertRaises(
                    ValueError,
                    get_from_spreadsheet_api,
                    valid_spreadsheet_id,
                    valid_sheet_name,
                    [malformed]
                )

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