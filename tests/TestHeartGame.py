import unittest
import unittest.mock
import itertools
import logging
import shutil
import os
import requests
from typing import List, Tuple

from src.Game import HeartGame, HeartSkill, HeartDomain
from src.Roll import Roll
from src.CharacterSheet import HeartCharacter
from src.utils.format import strikethrough, bold

class TestHeartGame(unittest.TestCase):
    DISCORD_USERNAME = 'jaffa6'
    OTHER_DISCORD_USERNAME = 'other_jaffa6'

    HEART_GAME_DATA = {
        "guild_id": 123,
        "system": "heart",
        "spreadsheet_id": "1Hzxegn3Z9EHHeYCp98vQQUCtTmsgrhf9-kfjP2AYZnk",
        "characters": {
            DISCORD_USERNAME: {
                "discord_username": DISCORD_USERNAME,
                "character_name": "Gruffle McStiltskin (she / her)",
                "spreadsheet_id": "1Hzxegn3Z9EHHeYCp98vQQUCtTmsgrhf9-kfjP2AYZnk",
                "sheet_name": "Example Character Sheet"
            },
            OTHER_DISCORD_USERNAME: {
                "discord_username": OTHER_DISCORD_USERNAME,
                "character_name": "Placeholder Character",
                "spreadsheet_id": "1Hzxegn3Z9EHHeYCp98vQQUCtTmsgrhf9-kfjP2AYZnk",
                "sheet_name": "Placeholder Sheet"
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

    @unittest.mock.patch('src.Game.get_spreadsheet_metadata')
    def test_from_data(self, mock_get_spreadsheet_metadata: unittest.mock.Mock):
        mock_get_spreadsheet_metadata.return_value = {
            0: 'Example Character Sheet'
        }

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

    def test_compute_downgrade_difficulty(self):
        for num_dice in range(0, 5):
            for difficulty in range(0, num_dice + 3):
                expected_use_difficult_actions_table = ( difficulty >= num_dice )
                expected_new_difficulty = 0 if expected_use_difficult_actions_table else difficulty

                use_difficult_actions_table, new_difficulty = HeartGame.compute_downgrade_difficulty(num_dice, difficulty)

                with self.subTest(f'Use difficult actions table - {num_dice} dice, {difficulty} difficulty'):
                    self.assertEqual(
                        use_difficult_actions_table,
                        expected_use_difficult_actions_table
                    )

                with self.subTest(f'New difficulty - {num_dice} dice, {difficulty} difficulty'):
                    self.assertEqual(
                        new_difficulty,
                        expected_new_difficulty
                    )

    @unittest.mock.patch('src.Game.HeartGame.compute_downgrade_difficulty')
    def test_roll(self, mock_downgrade_difficulty: unittest.mock.Mock):
        for num_dice in range(1, 5):
            for difficulty in range(0, 3):
                for bonus in range(-2, 3):
                    for penalty in range(-2, 3):
                        roll = Roll(
                            num_dice=num_dice,
                            dice_size=10,
                            cut=difficulty,
                            bonus=bonus,
                            penalty=penalty
                        )

                        mock_use_difficult_actions_table = (difficulty >= num_dice)
                        mock_new_difficulty = 0 if mock_use_difficult_actions_table else difficulty

                        mock_downgrade_difficulty.return_value = (mock_use_difficult_actions_table, mock_new_difficulty)

                        effective_highest, formatted_results, use_difficult_actions_table, total = HeartGame.roll(roll)

                        with self.subTest(f'Uses downgrade difficulty - {roll}'):
                            mock_downgrade_difficulty.assert_called_with(roll.num_dice, roll.cut)

                        with self.subTest(f'Difficult Actions Table correctly provided - {roll}'):
                            self.assertEqual(
                                mock_use_difficult_actions_table,
                                use_difficult_actions_table
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

    @unittest.mock.patch('src.Game.HeartGame.get_result')
    @unittest.mock.patch('src.Game.HeartGame.get_character')
    def test_roll_check(self, mock_get_character: unittest.mock.Mock, mock_get_result: unittest.mock.Mock):
        mock_get_character.return_value = unittest.mock.Mock(self.heart_game.character_sheets[self.DISCORD_USERNAME], autospec=True)

        for num_dice in range(1, 3):
            for difficulty in range(0, 2 + 1):
                roll = Roll(
                    num_dice=num_dice,
                    dice_size=10,
                    cut=difficulty
                )

                for skill in HeartSkill:
                    for domain in HeartDomain:
                        for character_has_skill in [False, True]:
                            for character_has_domain in [False, True]:
                                mock_get_character.return_value.check_skill_and_domain.return_value = character_has_skill, character_has_domain

                                expected_num_dice = roll.num_dice

                                if character_has_skill:
                                    expected_num_dice += 1

                                if character_has_domain:
                                    expected_num_dice += 1

                                highest, formatted_results, outcome, total, has_skill, has_domain, use_difficult_actions_table = self.heart_game.roll_check(self.DISCORD_USERNAME, skill, domain, roll)

                                with self.subTest('Checked for skill and domain'):
                                    mock_get_character.check_skill_and_domain.called_with_args(
                                        skill,
                                        domain
                                    )

                                with self.subTest('Expected number of results'):
                                    self.assertEqual(
                                        len(formatted_results),
                                        expected_num_dice
                                    )

                                with self.subTest('get_result used'):
                                    mock_get_result.assert_called_with(
                                        highest,
                                        use_difficult_actions_table
                                    )

    @unittest.mock.patch('Game.random.randint')
    @unittest.mock.patch('src.Game.HeartGame.get_character')
    def test_roll_fallout(self, mock_get_character: unittest.mock.Mock, mock_randint: unittest.mock.Mock):
        mock_get_character.return_value = unittest.mock.Mock(self.heart_game.character_sheets[self.DISCORD_USERNAME], autospec=True)

        for should_trigger in [False, True]:
            for modifier in [0, 1]:
                for fallout_level, fallout_data in HeartGame.FALLOUT_LEVELS.items():
                    threshold = fallout_data['threshold']
                    stress_cleared_if_triggered = fallout_data['clear']

                    character_stress = threshold + modifier
                    mock_get_character.return_value.get_fallout_stress.return_value = character_stress

                    if should_trigger:
                        mock_randint.return_value = character_stress - modifier
                    else:
                        mock_randint.return_value = character_stress + modifier + 1

                    rolled, fallout_level_triggered, stress_removed, stress = self.heart_game.roll_fallout(self.DISCORD_USERNAME)

                    with self.subTest('get_character used'):
                        mock_get_character.assert_called_with(self.DISCORD_USERNAME)

                    with self.subTest('get_fallout_stress used'):
                        mock_get_character.return_value.get_fallout_stress.assert_called()

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

                    with self.subTest('Correct amount cleared'):
                        if should_trigger:
                            self.assertEqual(
                                stress_removed,
                                stress_cleared_if_triggered
                            )
                        else:
                            self.assertEqual(
                                stress_removed,
                                HeartGame.FALLOUT_LEVELS['no']['clear']
                            )

                    with self.subTest('Correct roll returned'):
                        self.assertEqual(
                            rolled,
                            mock_randint.return_value
                        )

    def test_get_result(self):
        for use_difficult_actions_table in [False, True]:
            expected_results_table = HeartGame.DIFFICULT_ACTIONS_TABLE if use_difficult_actions_table else HeartGame.CORE_RESULTS

            for threshold, expected_outcome in expected_results_table.items():
                for modifier in [0, 1, 2]:
                    highest = threshold + modifier

                    if highest not in expected_results_table or expected_results_table[highest] != expected_outcome:
                        continue

                    result = HeartGame.get_result(highest, use_difficult_actions_table)

                    with self.subTest(f'Check the result - {use_difficult_actions_table, expected_outcome, modifier}'):
                        self.assertEqual(
                            result,
                            expected_outcome,
                        )

            highest = 0
            expected_outcome = expected_results_table[1]
            result = HeartGame.get_result(highest, use_difficult_actions_table)

            with self.subTest(f'Check the result for 0 - {use_difficult_actions_table, expected_outcome}'):
                self.assertEqual(
                    result,
                    expected_outcome,
                )

    @unittest.mock.patch('src.CharacterSheet.HeartCharacter.initialise')
    @unittest.mock.patch('src.Game.get_spreadsheet_metadata')
    def test_create_character(self, mock_get_spreadsheet_metadata: unittest.mock.Mock, mock_initialise: unittest.mock.Mock):
        mock_get_spreadsheet_metadata.return_value = {
            0: 'Example Character Sheet'
        }

        mock_initialise.return_value = self.HEART_GAME_DATA['characters'][self.DISCORD_USERNAME]['character_name'], self.HEART_GAME_DATA['characters'][self.DISCORD_USERNAME]['discord_username']

        game = HeartGame.from_data(self.HEART_GAME_DATA)
        game.character_sheets = {}

        character_data = self.HEART_GAME_DATA['characters'][self.DISCORD_USERNAME]

        created_character = game.create_character(
            character_data['spreadsheet_id'],
            character_data['sheet_name']
        )

        with self.subTest('Character data is correct'):
            self.assertEqual(
                created_character.info(),
                character_data
            )

        invalid_character_data = self.HEART_GAME_DATA['characters'][self.OTHER_DISCORD_USERNAME]

        mock_initialise.side_effect = requests.HTTPError('Test Error')

        with self.assertRaises(requests.HTTPError):
            game.create_character(
                invalid_character_data['spreadsheet_id'],
                invalid_character_data['sheet_name']
            )

    @unittest.mock.patch('src.Game.get_spreadsheet_metadata')
    def setUp(self, mock_get_spreadsheet_metadata: unittest.mock.Mock) -> None:
        mock_get_spreadsheet_metadata.return_value = {
            0: 'Example Character Sheet'
        }

        self.heart_game = HeartGame.from_data(self.HEART_GAME_DATA)

        logging.disable(logging.ERROR)

    def tearDown(self) -> None:
        logging.disable(logging.NOTSET)

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