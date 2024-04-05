import unittest

from string import ascii_uppercase
from Spreadsheet import Spreadsheet

class TestSpreadsheet(unittest.TestCase):

    def test_translate_cell_reference(self):

        valid_test_cases = {
            'simple': {
                'A1': (0, 0),
                'A2': (1, 0),
                'B1': (0, 1),
                'B2': (1, 1),
            },

            'multiletter': {
                'AA1': (0, 26),
                'AB1': (0, 27),
                'AA2': (1, 26)
            }
        }

        invalid_test_cases = [
            'A-1',
            'AA',
            'AB',
            None,
            '11',
            11
        ]

        for label, test_cases in valid_test_cases.items():
            with self.subTest(f'Handling {label} rows and columns'):

                for cell_reference, (expected_row_index, expected_column_index) in test_cases.items():
                    row_index, column_index = Spreadsheet.translate_cell_reference(cell_reference)

                    self.assertEqual(
                        row_index,
                        expected_row_index
                    )

                    self.assertEqual(
                        column_index,
                        expected_column_index
                    )

        for test_case in invalid_test_cases:
            self.assertRaises(
                ValueError,
                Spreadsheet.translate_cell_reference,
                test_case
            )

    def setUp(self) -> None:

        data = []
        expanded_data = []

        for row_index in range(10):
            row = []
            expanded_row = []

            for column_index in ascii_uppercase:
                value = f'{column_index}{row_index+1}'

                row.append(value)
                expanded_row.append(value)

            for column_index in ascii_uppercase:
                for second_column_index in ascii_uppercase:
                    expanded_row.append(f'{column_index}{second_column_index}{row_index+1}')

            data.append(row)
            expanded_data.append(expanded_row)

        self.data = data
        self.expanded_data = expanded_data

        self.spreadsheet = Spreadsheet(self.data)
        self.expanded_spreadsheet = Spreadsheet(self.expanded_data)

if __name__ == '__main__':
    unittest.main()
