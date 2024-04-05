import unittest
from unittest import mock

import itertools
import dataclasses
from typing import List, Tuple

from Game import SpireGame
from utils.format import strikethrough, bold

@dataclasses.dataclass
class MockMember:
    name: str = 'Big Bob'

class TestSpireGame(unittest.TestCase):
    SPIRE_GAME_DATA = {
        "guild_id": 123,
        "system": "spire",
        "spreadsheet_id": "1saogmy4eNNKng32Pf39b7K3Ko4uHEuWClm7UM-7Kd8I",
        "less_lethal": False,
        "characters": {
            "jaffa6": {
                "discord_username": "jaffa6",
                "character_name": "Azuro (he / him)",
                "spreadsheet_id": "1saogmy4eNNKng32Pf39b7K3Ko4uHEuWClm7UM-7Kd8I",
                "sheet_name": "Example Character Sheet"
            }
        }
    }

    ALL_INVALID_DATA = {
        'int_less_lethal': {
            ** SPIRE_GAME_DATA,
            'less_lethal': 123
        },
        'heart': {
            ** SPIRE_GAME_DATA,
            "system": 'heart'
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
                        formatted = SpireGame.format_roll(rolled, indices_to_remove, highest)

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
                        'expected_downgrade': 0,
                        'expected_new_difficulty': difficulty
                    }
                elif num_dice == 1:
                    all_subtests[key] = {
                        'expected_downgrade': difficulty,
                        'expected_new_difficulty': 0
                    }
                else:
                    all_subtests[key] = {
                        'expected_downgrade': (difficulty - num_dice) + 1,
                        'expected_new_difficulty': num_dice - 1
                    }

        for (num_dice, difficulty), data in all_subtests.items():
            with self.subTest(num_dice=num_dice, difficulty=difficulty):
                downgrade, new_difficulty = SpireGame.compute_downgrade_difficulty(num_dice, difficulty)

                self.assertEqual(downgrade, data['expected_downgrade'])
                self.assertEqual(new_difficulty, data['expected_new_difficulty'])

    def test_pick_highest(self):
        all_subtests = {}

        all_rolled = self.get_rolls()

        for rolled in all_rolled:
            all_subtests[rolled] = max(rolled)

        for rolled, expected_pick in all_subtests.items():
            with self.subTest(rolled=rolled):
                picked = SpireGame.pick_highest(rolled)

                self.assertEqual(expected_pick, picked)

    def test_apply_downgrade(self):
        downgrade_map = SpireGame.compute_downgrade_map()

        all_subtests = {}

        for highest in range(1, 10+1):
            for downgrade in [0, 1, 2]:
                key = (highest, downgrade)

                if highest == 1:
                    new_highest = highest
                else:
                    new_downgrade = downgrade
                    new_highest = highest

                    while new_downgrade > 0 and new_highest > 1:
                        new_highest = downgrade_map[new_highest]
                        new_downgrade -= 1

                all_subtests[key] = new_highest

        for (original_highest, downgrade), expected in all_subtests.items():
            with self.subTest(original_highest=original_highest, downgrade=downgrade, expected=expected):
                self.assertEqual(
                    SpireGame.apply_downgrade(original_highest, downgrade),
                    expected
                )

    def test_from_data(self):
        for valid_spire_data in [self.spire_game_data, self.spire_game_data_less_lethal]:
            valid_game = SpireGame.from_data(valid_spire_data)

            self.assertTrue(isinstance(valid_game, SpireGame))

            self.assertEqual(
                valid_game.spreadsheet_id,
                valid_spire_data['spreadsheet_id']
            )

            self.assertEqual(
                valid_game.guild_id,
                valid_spire_data['guild_id']
            )

            for discord_username, character_data in valid_spire_data['characters'].items():
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

        for label, invalid_data in self.ALL_INVALID_DATA.items():
            with self.subTest(label):
                self.assertRaises(
                    ValueError,
                    SpireGame.from_data,
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
        cls.spire_game_data = {
            "guild_id": 123,
            "system": "spire",
            "spreadsheet_id": "1saogmy4eNNKng32Pf39b7K3Ko4uHEuWClm7UM-7Kd8I",
            "less_lethal": False,
            "characters": {
                "jaffa6": {
                    "discord_username": "jaffa6",
                    "character_name": "Azuro (he / him)",
                    "spreadsheet_id": "1saogmy4eNNKng32Pf39b7K3Ko4uHEuWClm7UM-7Kd8I",
                    "sheet_name": "Example Character Sheet"
                }
            }
        }

        cls.spire_game_data_less_lethal = {
            "guild_id": 123,
            "system": "spire",
            "spreadsheet_id": "1saogmy4eNNKng32Pf39b7K3Ko4uHEuWClm7UM-7Kd8I",
            "less_lethal": True,
            "characters": {
                "jaffa6": {
                    "discord_username": "jaffa6",
                    "character_name": "Azuro (he / him)",
                    "spreadsheet_id": "1saogmy4eNNKng32Pf39b7K3Ko4uHEuWClm7UM-7Kd8I",
                    "sheet_name": "Example Character Sheet"
                }
            }
        }

        for omit_field in cls.SPIRE_GAME_DATA.keys():
            if omit_field == 'characters':
                continue

            cls.ALL_INVALID_DATA[f'missing_{omit_field}'] = {
                field: value for field, value in cls.SPIRE_GAME_DATA.items() if field != omit_field
            }

if __name__ == '__main__':
    unittest.main()