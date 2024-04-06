import collections
import unittest
from unittest import mock

import itertools
import dataclasses
import shutil
import os
from typing import List, Tuple

from Game import HeartGame
from CharacterSheet import HeartCharacter
from utils.format import strikethrough, bold

@dataclasses.dataclass
class MockMember:
    name: str = 'Big Bob'

class TestHeartGame(unittest.TestCase):
    HEART_GAME_DATA = {
        "guild_id": 123,
        "system": "heart",
        "spreadsheet_id": "1Hzxegn3Z9EHHeYCp98vQQUCtTmsgrhf9-kfjP2AYZnk",
        "characters": {
            "jaffa6": {
                "discord_username": "jaffa6",
                "character_name": "Gruffle McStiltskin (she / her)",
                "spreadsheet_id": "1Hzxegn3Z9EHHeYCp98vQQUCtTmsgrhf9-kfjP2AYZnk",
                "sheet_name": "Example Character Sheet"
            }
        }
    }

    ALL_INVALID_DATA = {
        'spire': {
            ** HEART_GAME_DATA,
            "system": 'spire'
        }
    }

    def test_format_roll(self):
        all_rolled = self.get_rolls()

        for rolled in all_rolled:
            highest = max(rolled)

            for size in range(1, len(rolled)):
                combinations = itertools.combinations(range(1, len(rolled)), size)

                for indices_to_remove in combinations:
                    with self.subTest(rolled=rolled, indices_to_remove=indices_to_remove, highest=highest):
                        formatted = HeartGame.format_roll(rolled, indices_to_remove, highest)

                        for index, formatted_value in enumerate(formatted):
                            value = rolled[index]

                            if index in indices_to_remove:
                                self.assertEqual(
                                    strikethrough(value),
                                    formatted_value
                                )
                            elif rolled[index] == highest:
                                self.assertEqual(
                                    bold(value),
                                    formatted_value
                                )
                            else:
                                self.assertEqual(
                                    str(value),
                                    formatted_value
                                )

    def test_compute_downgrade_difficulty(self):
        all_subtests = {}

        for num_dice in range(1, 5):
            for difficulty in [0, 1, 2]:
                key = (num_dice, difficulty)

                if num_dice > difficulty:
                    all_subtests[key] = {
                        'expected_new_difficulty': difficulty,
                    }
                elif num_dice == 1:
                    all_subtests[key] = {
                        'expected_new_difficulty': 0,
                    }
                elif num_dice == difficulty:
                    all_subtests[key] = {
                        'expected_new_difficulty': 0,
                    }
                else:
                    all_subtests[key] = {
                        'expected_new_difficulty': (difficulty - num_dice) + 1,
                    }

        for (num_dice, difficulty), data in all_subtests.items():
            with self.subTest(num_dice=num_dice, difficulty=difficulty):
                expected_use_difficult_actions_table = data['expected_new_difficulty'] < difficulty

                use_difficult_actions_table, new_difficulty = HeartGame.compute_downgrade_difficulty(num_dice, difficulty)

                self.assertEqual(new_difficulty, data['expected_new_difficulty'])
                self.assertEqual(use_difficult_actions_table, expected_use_difficult_actions_table)

    def test_pick_highest(self):
        all_subtests = collections.defaultdict(dict)

        all_rolled = self.get_rolls()

        for rolled in all_rolled:
            sorted_rolled = sorted(rolled)

            all_subtests[0][rolled] = max(rolled)

            if len(rolled) > 1:
                all_subtests[1][rolled] = max(sorted_rolled[:-1])

            if len(rolled) > 2:
                all_subtests[2][rolled] = max(sorted_rolled[:-2])

        for difficulty, rolled_data in all_subtests.items():
            for rolled, expected_pick in rolled_data.items():
                with self.subTest(rolled=rolled):
                    picked = HeartGame.pick_highest(rolled, difficulty)

                    self.assertEqual(expected_pick, picked)

    def test_from_data(self):
        valid_game = HeartGame.from_data(self.HEART_GAME_DATA)

        self.assertTrue(isinstance(valid_game, HeartGame))

        self.assertEqual(
            valid_game.spreadsheet_id,
            self.HEART_GAME_DATA['spreadsheet_id']
        )

        self.assertEqual(
            valid_game.guild_id,
            self.HEART_GAME_DATA['guild_id']
        )

        for discord_username, character_data in self.HEART_GAME_DATA['characters'].items():
            self.assertIn(discord_username, valid_game.character_sheets)

            loaded_character = valid_game.character_sheets[discord_username]

            self.assertEqual(
                loaded_character.discord_username,
                character_data['discord_username']
            )

            self.assertEqual(
                loaded_character.character_name,
                character_data['character_name']
            )

            self.assertEqual(
                loaded_character.spreadsheet_id,
                character_data['spreadsheet_id']
            )

            self.assertEqual(
                loaded_character.sheet_name,
                character_data['sheet_name']
            )

            self.assertTrue(loaded_character, HeartCharacter)

        for label, invalid_data in self.ALL_INVALID_DATA.items():
            with self.subTest(label):
                self.assertRaises(
                    ValueError,
                    HeartGame.from_data,
                    invalid_data
                )

    def get_rolls(self) -> List[Tuple[int, ...]]:
        all_rolled = []

        thresholds = list(range(1, 10 + 1))

        for size in range(1, 5 + 1):
            for combination in itertools.combinations(thresholds, size):
                all_rolled.append(combination)

        return all_rolled

    def setUp(self) -> None:
        self.mock_me = MockMember(name='jaffa6')

        self.mock_members = [
            MockMember(),
            self.mock_me
        ]

    @classmethod
    def setUpClass(cls) -> None:
        for omit_field in cls.HEART_GAME_DATA.keys():
            if omit_field == 'characters':
                continue

            cls.ALL_INVALID_DATA[f'missing_{omit_field}'] = {
                field: value for field, value in cls.HEART_GAME_DATA.items() if field != omit_field
            }

    @classmethod
    def tearDownClass(cls) -> None:
        rm_path = HeartGame.get_server_dirpath(cls.HEART_GAME_DATA['guild_id'])

        if os.path.isdir(rm_path):
            shutil.rmtree(rm_path)

if __name__ == '__main__':
    unittest.main()