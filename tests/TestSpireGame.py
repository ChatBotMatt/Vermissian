import unittest
import unittest.mock

import requests
import itertools
import logging
import shutil
import os
from typing import List, Tuple

from src.vermissian.ResistanceGame import SpireGame
from src.vermissian.ResistanceCharacterSheet import SpireCharacter, SpireSkill, SpireDomain
from src.Roll import Roll
from src.utils.format import strikethrough, bold

class TestSpireGame(unittest.TestCase):
    DISCORD_USERNAME = 'jaffa6'
    OTHER_DISCORD_USERNAME = 'other_jaffa6'

    SPIRE_GAME_DATA = {
        "guild_id": 123,
        "system": "spire",
        "spreadsheet_id": "1saogmy4eNNKng32Pf39b7K3Ko4uHEuWClm7UM-7Kd8I",
        "less_lethal": False,
        "characters": {
            DISCORD_USERNAME: {
                "discord_username": DISCORD_USERNAME,
                "character_name": "Azuro (he / him)",
                "spreadsheet_id": "1saogmy4eNNKng32Pf39b7K3Ko4uHEuWClm7UM-7Kd8I",
                "sheet_name": "Example Character Sheet"
            },
            OTHER_DISCORD_USERNAME: {
                "discord_username": OTHER_DISCORD_USERNAME,
                "character_name": "Placeholder Character",
                "spreadsheet_id": "1saogmy4eNNKng32Pf39b7K3Ko4uHEuWClm7UM-7Kd8I",
                "sheet_name": "Placeholder Sheet"
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

        with self.subTest('Downgrade < 0'):
            self.assertRaises(
                ValueError,
                SpireGame.apply_downgrade,
                5,
                -1
            )

        with self.subTest('Highest < 1'):
            self.assertRaises(
                ValueError,
                SpireGame.apply_downgrade,
                0,
                0
            )

        with self.subTest('Highest > 10'):
            self.assertRaises(
                ValueError,
                SpireGame.apply_downgrade,
                11,
                0
            )

    @unittest.mock.patch('src.Game.get_spreadsheet_metadata')
    def test_from_data(self, mock_get_spreadsheet_metadata: unittest.mock.Mock):
        mock_get_spreadsheet_metadata.return_value = {
            0: 'Example Character Sheet'
        }

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

                print(type(loaded_character))
                self.assertTrue(isinstance(loaded_character, SpireCharacter))

        for label, invalid_data in self.ALL_INVALID_DATA.items():
            with self.subTest(label):
                self.assertRaises(
                    ValueError,
                    SpireGame.from_data,
                    invalid_data
                )

    @unittest.mock.patch('src.vermissian.ResistanceGame.SpireGame.get_result')
    @unittest.mock.patch('src.vermissian.ResistanceGame.SpireGame.get_character')
    def test_roll_check(self, mock_get_character: unittest.mock.Mock, mock_get_result: unittest.mock.Mock):
        mock_get_character.return_value = unittest.mock.Mock(self.spire_game.character_sheets[self.DISCORD_USERNAME], autospec=True)

        for original_num_dice in range(1, 3):
            for difficulty in range(0, 2 + 1):
                roll = Roll(
                    num_dice=original_num_dice,
                    dice_size=10,
                    drop=difficulty
                )

                for skill in SpireSkill:
                    for domain in SpireDomain:
                        for character_has_skill in [False, True]:
                            for character_has_domain in [False, True]:
                                mock_get_character.return_value.check_skill_and_domain.return_value = character_has_skill, character_has_domain

                                expected_num_dice = roll.num_dice

                                if character_has_skill:
                                    expected_num_dice += 1

                                if character_has_domain:
                                    expected_num_dice += 1

                                roll_str = str({'expected_num_dice': expected_num_dice, 'difficulty': difficulty})

                                highest, formatted_results, outcome, total, has_skill, has_domain, did_downgrade = self.spire_game.roll_check(
                                    self.DISCORD_USERNAME,
                                    skill,
                                    domain,
                                    roll
                                )

                                if difficulty < expected_num_dice:
                                    expected_downgrade = 0
                                else:
                                    expected_downgrade = (difficulty - expected_num_dice) + 1

                                with self.subTest(f'Checked for skill and domain - {roll_str}'):
                                    mock_get_character.check_skill_and_domain.called_with_args(
                                        skill,
                                        domain
                                    )

                                with self.subTest(f'Expected number of results - {roll_str}'):
                                    self.assertEqual(
                                        len(formatted_results),
                                        expected_num_dice
                                    )

                                with self.subTest(f'get_result used - {roll_str}'):
                                    mock_get_result.assert_called_with(
                                        highest,
                                        expected_downgrade
                                    )

    def test_roll(self):
        for num_dice in range(1, 5):
            for difficulty in range(0, 3):
                for bonus in range(-2, 3):
                    for penalty in range(-2, 3):
                        roll = Roll(
                            num_dice=num_dice,
                            dice_size=10,
                            drop=difficulty,
                            bonus=bonus,
                            penalty=penalty
                        )

                        if difficulty < num_dice:
                            expected_downgrade = 0
                        else:
                            expected_downgrade = (difficulty - num_dice) + 1

                        effective_highest, formatted_results, downgrade, total = SpireGame.roll(roll)

                        with self.subTest(f'Downgrade computed properly - {roll}'):
                            self.assertEqual(
                                expected_downgrade,
                                downgrade
                            )

                        with self.subTest(f'Correct number of results - {roll}'):
                            self.assertEqual(
                                len(formatted_results),
                                num_dice
                            )

                        # Not rigorous proof, but a reasonable sanity check at least - unit testing random outcomes is otherwise kind of a nightmare.
                        with self.subTest(f'Highest bounded by dice size - {roll}'):
                            self.assertLessEqual(
                                effective_highest,
                                10 + bonus - penalty
                            )

                        with self.subTest(f'Lowest bounded by 0 - {roll}'):
                            self.assertGreaterEqual(
                                effective_highest,
                                0 + bonus - penalty
                            )

    def test_get_result(self):
        downgrade_map = {
            SpireGame.CRIT_SUCCESS: SpireGame.SUCCESS,
            SpireGame.SUCCESS: SpireGame.SUCCESS_AT_A_COST,
            SpireGame.SUCCESS_AT_A_COST: SpireGame.FAILURE,
            SpireGame.FAILURE: SpireGame.CRIT_FAILURE,
            SpireGame.CRIT_FAILURE: SpireGame.CRIT_FAILURE
        }

        for downgrade in range(0, 5):
            for threshold, original_expected_outcome in SpireGame.CORE_RESULTS.items():
                remaining_downgrade = downgrade
                expected_outcome = original_expected_outcome

                while remaining_downgrade > 0:
                    expected_outcome = downgrade_map[expected_outcome]
                    remaining_downgrade -= 1

                for modifier in [0, 1, 2]:
                    highest = threshold + modifier

                    if highest not in SpireGame.CORE_RESULTS or SpireGame.CORE_RESULTS[highest] != original_expected_outcome:
                        continue

                    result = SpireGame.get_result(highest, downgrade)

                    with self.subTest(f'Check the result - {original_expected_outcome, highest, downgrade, modifier}'):
                        self.assertEqual(
                            result,
                            expected_outcome,
                        )

    @unittest.mock.patch('src.vermissian.ResistanceGame.random.randint')
    @unittest.mock.patch('src.vermissian.ResistanceGame.SpireGame.get_character')
    def test_roll_fallout(self, mock_get_character: unittest.mock.Mock, mock_randint: unittest.mock.Mock):
        mock_get_character.return_value = unittest.mock.Mock(self.spire_game.character_sheets[self.DISCORD_USERNAME], autospec=True)

        for should_trigger in [False, True]:
            for resistance in SpireCharacter.RESISTANCES:
                for modifier in [0, 1]:
                    for fallout_level, fallout_data in SpireGame.FALLOUT_LEVELS.items():
                        threshold = fallout_data['threshold']
                        stress_cleared_if_triggered = fallout_data['clear']

                        character_stress = threshold + modifier
                        mock_get_character.return_value.get_fallout_stress.return_value = character_stress

                        if should_trigger:
                            mock_randint.return_value = character_stress - modifier - 1
                        else:
                            mock_randint.return_value = character_stress + modifier + 1

                        rolled, fallout_level_triggered, stress_removed, stress = self.spire_game.roll_fallout(self.DISCORD_USERNAME, resistance)

                        with self.subTest(f'get_character used - {should_trigger, modifier, fallout_level}'):
                            mock_get_character.assert_called_with(self.DISCORD_USERNAME)

                        with self.subTest(f'get_fallout_stress used - {should_trigger, modifier, fallout_level}'):
                            mock_get_character.return_value.get_fallout_stress.assert_called_with(self.spire_game.less_lethal, resistance)

                        with self.subTest(f'Correct level triggered - {should_trigger, modifier, fallout_level}'):
                            if should_trigger:
                                self.assertEqual(
                                    fallout_level_triggered,
                                    fallout_level
                                )
                            else:
                                self.assertEqual(
                                    fallout_level_triggered,
                                    'no'
                                )

                        with self.subTest(f'Correct amount cleared - {should_trigger, modifier, fallout_level}'):
                            if should_trigger:
                                self.assertEqual(
                                    stress_removed,
                                    stress_cleared_if_triggered
                                )
                            else:
                                self.assertEqual(
                                    stress_removed,
                                    SpireGame.FALLOUT_LEVELS['no']['clear']
                                )

                        with self.subTest(f'Correct roll returned - {should_trigger, modifier, fallout_level}'):
                            self.assertEqual(
                                rolled,
                                mock_randint.return_value
                            )

    @unittest.mock.patch('src.vermissian.ResistanceCharacterSheet.SpireCharacter.initialise')
    @unittest.mock.patch('src.Game.get_spreadsheet_metadata')
    def test_create_character(self, mock_get_spreadsheet_metadata: unittest.mock.Mock, mock_initialise: unittest.mock.Mock):
        mock_get_spreadsheet_metadata.return_value = {
            0: 'Example Character Sheet'
        }

        mock_initialise.return_value = self.SPIRE_GAME_DATA['characters'][self.DISCORD_USERNAME]['character_name'], self.SPIRE_GAME_DATA['characters'][self.DISCORD_USERNAME]['discord_username']

        game = SpireGame.from_data(self.SPIRE_GAME_DATA)
        game.character_sheets = {}

        with self.subTest('Metadata gotten'):
            mock_get_spreadsheet_metadata.assert_called()

        character_data = self.SPIRE_GAME_DATA['characters'][self.DISCORD_USERNAME]

        created_character = game.create_character(
            character_data['spreadsheet_id'],
            character_data['sheet_name']
        )

        with self.subTest('Character data is correct'):
            self.assertEqual(
                created_character.info(),
                character_data
            )

        mock_initialise.side_effect = requests.HTTPError('Test Error')

        invalid_character_data = self.SPIRE_GAME_DATA['characters'][self.OTHER_DISCORD_USERNAME]

        with self.assertRaises(requests.HTTPError):
            game.create_character(
                invalid_character_data['spreadsheet_id'],
                invalid_character_data['sheet_name']
            )

    @staticmethod
    def get_rolls() -> List[Tuple[int, ...]]:
        all_rolled = []

        thresholds = list(range(1, 10 + 1))

        for size in range(1, 5 + 1):
            for combination in itertools.combinations(thresholds, size):
                all_rolled.append(combination)

        return all_rolled

    @unittest.mock.patch('src.Game.get_spreadsheet_metadata')
    def setUp(self, mock_get_spreadsheet_metadata: unittest.mock.Mock) -> None:
        mock_get_spreadsheet_metadata.return_value = {
            0: 'Example Character Sheet'
        }

        self.spire_game = SpireGame.from_data(self.SPIRE_GAME_DATA)

        logging.disable(logging.ERROR)

    def tearDown(self) -> None:
        logging.disable(logging.NOTSET)

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

    @classmethod
    def tearDownClass(cls) -> None:
        rm_path = SpireGame.get_server_dirpath(cls.SPIRE_GAME_DATA['guild_id'])

        if os.path.isdir(rm_path):
            shutil.rmtree(rm_path)


if __name__ == '__main__':
    unittest.main()