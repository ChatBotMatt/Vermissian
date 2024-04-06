import unittest
from unittest import mock

import dataclasses
import itertools
import abc
from typing import Dict

import requests

from CharacterSheet import SpireCharacter, SpireSkill, SpireDomain, HeartCharacter, HeartSkill, HeartDomain
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

class TestCharacterSheet(abc.ABC):
    @mock.patch('utils.google_sheets.requests.get', autospec=True)
    def test_initialise(self, mock_get: mock.Mock):

        expected_name_label = 'Player Name (Pronouns)'
        expected_discord_username = 'Test Username'
        expected_character_name = 'Test Character Name'

        valid_response = MockResponse(
            status_code=200,
            content={
                'valueRanges': [
                    {
                        'values': [[expected_name_label]]
                    },
                    {
                        'values': [[expected_discord_username]]
                    },
                    {
                        'values': [[expected_character_name]]
                    }
                ]
            }
        )

        with self.subTest('Valid Character'):
            mock_get.return_value = valid_response

            unnamed_character = SpireCharacter(spreadsheet_id='abc', sheet_name='def')

            with self.subTest('Mock used'):
                self.assertTrue(mock_get.called)

            with self.subTest('Discord Username'):
                self.assertEqual(
                    unnamed_character.discord_username,
                    expected_discord_username
                )

            with self.subTest('Character Name'):
                self.assertEqual(
                    unnamed_character.character_name,
                    expected_character_name
                )

        invalid_response = MockResponse(
            status_code=200,
            content={
                'valueRanges': [
                    {
                        'values': [['abc']]
                    },
                    {
                        'values': [[expected_discord_username]]
                    },
                    {
                        'values': [[expected_character_name]]
                    }
                ]
            }
        )

        with self.subTest('Invalid Character'):
            mock_get.return_value = invalid_response

            with self.subTest('Initialisation Fails'):
                self.assertRaises(
                    ValueError,
                    SpireCharacter,
                    self.valid_spreadsheet_id, self.valid_sheet_name
                )

            with self.subTest('Mock used'):
                self.assertTrue(mock_get.called)

        forbidden_response = MockResponse(
            status_code=403,
            content={'error': {'status': 'PERMISSION_DENIED'}}
        )

        with self.subTest('Invalid Character'):
            mock_get.return_value = forbidden_response

            with self.subTest('Initialisation Fails'):
                self.assertRaises(
                    ForbiddenSpreadsheetError,
                    SpireCharacter,
                    self.valid_spreadsheet_id, self.valid_sheet_name
                )

            with self.subTest('Mock used'):
                self.assertTrue(mock_get.called)

    @mock.patch('utils.google_sheets.requests.get', autospec=True)
    def test_check_skill_and_domain(self, mock_get: mock.Mock):
        for expected_has_skill, expected_has_domain in itertools.product([False, True], [False, True]):
            for skill, domain in itertools.product(self.skills, self.domains):
                valid_response = MockResponse(
                    status_code=200,
                    content={
                        'valueRanges': [
                            {
                                'values': [['TRUE' if expected_has_skill else 'FALSE']]
                            },
                            {
                                'values': [['TRUE' if expected_has_domain else 'FALSE']]
                            }
                        ]
                    }
                )

                mock_get.return_value = valid_response

                has_skill, has_domain = self.valid_unnamed_character.check_skill_and_domain(
                    skill=skill,
                    domain=domain
                )

                with self.subTest('Mock Used'):
                    self.assertTrue(mock_get.called)

                with self.subTest(f'Check Skill - {skill}'):
                    self.assertEqual(
                        has_skill,
                        expected_has_skill
                    )

                with self.subTest(f'Check Domain - {domain}'):
                    self.assertEqual(
                        has_domain,
                        expected_has_domain
                    )

    def test_info(self):
        self.assertEqual(
            self.valid_unnamed_character.info(),
            {
                'discord_username': self.valid_unnamed_character.discord_username,
                'character_name': self.valid_unnamed_character.character_name,
                'spreadsheet_id': self.valid_unnamed_character.spreadsheet_id,
                'sheet_name': self.valid_unnamed_character.sheet_name
            }
        )

class TestSpireCharacter(TestCharacterSheet, unittest.TestCase):
    valid_spreadsheet_id = '1saogmy4eNNKng32Pf39b7K3Ko4uHEuWClm7UM-7Kd8I'
    valid_sheet_name = 'Example Character Sheet'

    def test_load(self):
        valid_info_including_name = {
            'discord_username': self.valid_unnamed_character.discord_username,
            'character_name': self.valid_unnamed_character.character_name,
            'spreadsheet_id': self.valid_unnamed_character.spreadsheet_id,
            'sheet_name': self.valid_unnamed_character.sheet_name
        }

        with self.subTest('Load unnamed character, given named info'):
            self.assertEqual(
                self.valid_unnamed_character,
                SpireCharacter.load(valid_info_including_name)
            )

        valid_info_without_name = {
            'discord_username': None,
            'character_name': None,
            'spreadsheet_id': self.valid_unnamed_character.spreadsheet_id,
            'sheet_name': self.valid_unnamed_character.sheet_name
        }

        with self.subTest('Load unnamed character, given info without name'):
            self.assertEqual(
                self.valid_unnamed_character,
                SpireCharacter.load(valid_info_without_name)
            )

    def test_equality(self):
        with self.subTest('Identical Objects'):
            self.assertEqual(
                self.valid_unnamed_character,
                self.valid_unnamed_character
            )

        with self.subTest('Identical Data'):
            dupe_character = SpireCharacter(
                spreadsheet_id=self.valid_unnamed_character.spreadsheet_id,
                sheet_name=self.valid_unnamed_character.sheet_name,
                character_name=self.valid_unnamed_character.character_name,
                discord_username=self.valid_unnamed_character.discord_username
            )

            self.assertEqual(
                self.valid_unnamed_character,
                dupe_character
            )

        with self.subTest('Non-identical Characters'):
            self.assertNotEqual(
                self.valid_unnamed_character,
                self.valid_named_character
            )

    @classmethod
    def setUp(self) -> None:
        self.valid_unnamed_character = SpireCharacter(spreadsheet_id=self.valid_spreadsheet_id, sheet_name=self.valid_sheet_name)

        self.valid_named_character = SpireCharacter(
            spreadsheet_id=self.valid_spreadsheet_id,
            sheet_name=self.valid_sheet_name,
            character_name='Test Character Name',
            discord_username='Test Discord Username'
        )

        self.skills = [skill for skill in SpireSkill]
        self.domains = [domain for domain in SpireDomain]

class TestHeartCharacter(TestCharacterSheet, unittest.TestCase):
    valid_spreadsheet_id = '1PzF3ZHQpXXaS0ci0Q0vbE9uHpC26GiUJ4ishIbbcpOY'
    valid_sheet_name = 'Example Character Sheet'

    def test_load(self):
        valid_info_including_name = {
            'discord_username': self.valid_unnamed_character.discord_username,
            'character_name': self.valid_unnamed_character.character_name,
            'spreadsheet_id': self.valid_unnamed_character.spreadsheet_id,
            'sheet_name': self.valid_unnamed_character.sheet_name
        }

        with self.subTest('Load unnamed character, given named info'):
            self.assertEqual(
                self.valid_unnamed_character,
                HeartCharacter.load(valid_info_including_name)
            )

        valid_info_without_name = {
            'discord_username': None,
            'character_name': None,
            'spreadsheet_id': self.valid_unnamed_character.spreadsheet_id,
            'sheet_name': self.valid_unnamed_character.sheet_name
        }

        with self.subTest('Load unnamed character, given info without name'):
            self.assertEqual(
                self.valid_unnamed_character,
                HeartCharacter.load(valid_info_without_name)
            )

    def test_equality(self):
        with self.subTest('Identical Objects'):
            self.assertEqual(
                self.valid_unnamed_character,
                self.valid_unnamed_character
            )

        with self.subTest('Identical Data'):
            dupe_character = HeartCharacter(
                spreadsheet_id=self.valid_unnamed_character.spreadsheet_id,
                sheet_name=self.valid_unnamed_character.sheet_name,
                character_name=self.valid_unnamed_character.character_name,
                discord_username=self.valid_unnamed_character.discord_username
            )

            self.assertEqual(
                self.valid_unnamed_character,
                dupe_character
            )

        with self.subTest('Non-identical Characters'):
            self.assertNotEqual(
                self.valid_unnamed_character,
                self.valid_named_character
            )

    @classmethod
    def setUp(cls) -> None:
        cls.valid_unnamed_character = HeartCharacter(spreadsheet_id=cls.valid_spreadsheet_id, sheet_name=cls.valid_sheet_name)

        cls.valid_named_character = HeartCharacter(
            spreadsheet_id=cls.valid_spreadsheet_id,
            sheet_name=cls.valid_sheet_name,
            character_name='Test Character Name',
            discord_username='Test Discord Username'
        )

        cls.skills = [skill for skill in HeartSkill]
        cls.domains = [domain for domain in HeartDomain]

if __name__ == '__main__':
    unittest.main()