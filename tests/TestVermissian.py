import discord

import unittest
import unittest.mock

import logging
import os
import shutil
from typing import Dict, Any, Union

from src.Game import SpireGame, HeartGame
from src.CharacterSheet import SpireCharacter, HeartCharacter
from src.System import System
from src.Vermissian import Vermissian
from src.utils.exceptions import BadCharacterKeeperError

class TestVermissian(unittest.TestCase):

    # TODO These really should do mocks for adding/removing files

    @unittest.mock.patch('src.CharacterSheet.get_from_spreadsheet_api')
    @unittest.mock.patch('src.Game.get_spreadsheet_metadata')
    def test_create_game(self, mock_get_spreadsheet_metadata: unittest.mock.Mock, mock_get_from_spreadsheet_api: unittest.mock.Mock):
        mock_get_spreadsheet_metadata.return_value = {
            0: 'Example Character Sheet'
        }

        self.assert_no_games()

        for game_label, game_data in self.all_game_data.items():
            mock_get_from_spreadsheet_api.return_value = {
                character.sheet_name: {
                    character.CELL_REFERENCES['name_label']: character.EXPECTED_NAME_LABEL,
                    character.CELL_REFERENCES['biography']['discord_username']: character.discord_username,
                    character.CELL_REFERENCES['biography']['character_name']: character.character_name,
                } for character in game_data['characters']
            }

            with self.subTest(f'Create game - {game_label}'):
                self.vermissian.create_game(
                    game_data['guild_id'],
                    game_data['valid_spreadsheet_url'],
                    game_data['system'],
                    game_data['less_lethal']
                )

                with self.subTest(f'Game created - {game_label}'):
                    self.assertEqual(
                        self.vermissian.games[game_data['guild_id']],
                        game_data['game']
                    )

                self.vermissian.remove_game(game_data['guild_id'])

                self.assert_no_games()

            mock_get_from_spreadsheet_api.side_effect = BadCharacterKeeperError(spreadsheet_url=game_data['invalid_spreadsheet_url'])

            with self.subTest('Create game with invalid spreadsheet URL'):
                with self.assertRaises(BadCharacterKeeperError):
                    self.vermissian.create_game(
                        game_data['guild_id'],
                        game_data['invalid_spreadsheet_url'],
                        game_data['system'],
                        game_data['less_lethal']
                    )

    def test_add_game(self):
        self.assert_no_games()

        for game_label, game_data in self.all_game_data.items():
            with self.subTest(f'Add game - {game_label}'):
                self.vermissian.add_game(game_data['game'])

                self.assertEqual(
                    self.vermissian.games[game_data['guild_id']],
                    game_data['game']
                )

            with self.subTest(f'Check that game was saved to file - {game_label}'):
                if game_data['system'] == System.SPIRE:
                    server_data_path = SpireGame.get_game_data_filepath(game_data['game'].guild_id)
                else:
                    server_data_path = HeartGame.get_game_data_filepath(game_data['game'].guild_id)

                self.assertTrue(
                    os.path.isfile(server_data_path)
                )

            with self.subTest(f'Remove game - {game_label}'):
                self.vermissian.remove_game(game_data['guild_id'])

                self.assert_no_games()

    def test_remove_game(self):
        self.assert_no_games()

        for game_label, game_data in self.all_game_data.items():
            with self.subTest('Check no error when removing a non-existent game'):
                self.vermissian.remove_game(game_data['guild_id'])

            with self.subTest(f'Check can remove a game - {game_label}'):
                self.vermissian.add_game(game_data['game'])

                with self.subTest(f'Check game was added - {game_label}'):
                    self.assertEqual(
                        self.vermissian.games[game_data['guild_id']],
                        game_data['game']
                    )

                    with self.subTest(f'Check that game was saved to file - {game_label}'):
                        server_data_path = SpireGame.get_game_data_filepath(game_data['game'].guild_id)

                        self.assertTrue(
                            os.path.isfile(server_data_path)
                        )

                with self.subTest(f'Check removing the new game - {game_label}'):
                    self.vermissian.remove_game(game_data['game'].guild_id)

                    with self.subTest(f'Game removed from Vermissian - {game_label}'):
                        self.assert_no_games()

                    with self.subTest(f'Game data file removed - {game_label}'):
                        self.assertFalse(
                            os.path.isfile(server_data_path)
                        )

        games_to_add: Dict[str, Union[SpireGame, HeartGame]] = {
            game_label: game_data['game'] for game_label, game_data in self.all_game_data.items()
        }

        for game_label, game_to_add in games_to_add.items():
            self.vermissian.add_game(game_to_add)

            with self.subTest(f'Check game added - {game_label}'):
                self.assertEqual(
                    self.vermissian.games[game_to_add.guild_id],
                    game_to_add
                )

            with self.subTest(f'Check that game was saved to file - {game_label}'):
                server_data_path = SpireGame.get_game_data_filepath(game_to_add.guild_id)

                self.assertTrue(
                    os.path.isfile(server_data_path)
                )

        with self.subTest('Check all games added'):
            self.assertEqual(
                len(self.vermissian.games),
                len(games_to_add)
            )

        self.vermissian.remove_game(games_to_add['spire_lethal'].guild_id)

        with self.subTest('Check other games still exist'):
            self.assertEqual(
                len(self.vermissian.games),
                len(games_to_add) - 1
            )

        for game_label, game_to_add in games_to_add.items():
            if game_label == 'spire_lethal':
                continue

            with self.subTest(f'Check that other game\'s data still exists - {game_label}'):
                server_data_path = SpireGame.get_game_data_filepath(game_to_add.guild_id)

                self.assertTrue(
                    os.path.isfile(server_data_path)
                )

    def assert_no_games(self):
        with self.subTest('No current games'):
            self.assertEqual(
                len(self.vermissian.games),
                0
            )

    @unittest.mock.patch('src.CharacterSheet.get_from_spreadsheet_api')
    @unittest.mock.patch('src.Game.get_spreadsheet_metadata')
    def setUp(self, mock_get_spreadsheet_metadata: unittest.mock.Mock, mock_get_from_spreadsheet_api: unittest.mock.Mock) -> None:
        logging.disable(logging.ERROR)

        mock_get_spreadsheet_metadata.return_value = {
            0: 'Example Character Sheet'
        }

        self.all_game_data: Dict[str, Dict[str, Any]] = {
            'spire_lethal': {
                'guild_id': -5,
                'valid_spreadsheet_id': '1saogmy4eNNKng32Pf39b7K3Ko4uHEuWClm7UM-7Kd8I',
                'valid_sheet_name': 'Example Character Sheet',
                'valid_spreadsheet_url': 'https://docs.google.com/spreadsheets/d/1saogmy4eNNKng32Pf39b7K3Ko4uHEuWClm7UM-7Kd8I/edit#gid=0',
                'invalid_spreadsheet_url': 'abc',
                'system': System.SPIRE,
                'less_lethal': False
            },
            'spire_depopulated': {
                'guild_id': -4,
                'valid_spreadsheet_id': '1uW0RnR9O_zgKi1qj4Qjw3BzpZ2zU0zWyoa0Sw7lIdWw',
                'valid_sheet_name': 'Character 1',
                'valid_spreadsheet_url': 'https://docs.google.com/spreadsheets/d/1uW0RnR9O_zgKi1qj4Qjw3BzpZ2zU0zWyoa0Sw7lIdWw/edit?usp=sharing',
                'invalid_spreadsheet_url': 'abc',
                'system': System.SPIRE,
                'less_lethal': False
            },
            'spire_less_lethal': {
                'guild_id': -3,
                'valid_spreadsheet_id': '1saogmy4eNNKng32Pf39b7K3Ko4uHEuWClm7UM-7Kd8I',
                'valid_sheet_name': 'Example Character Sheet',
                'valid_spreadsheet_url': 'https://docs.google.com/spreadsheets/d/1saogmy4eNNKng32Pf39b7K3Ko4uHEuWClm7UM-7Kd8I/edit#gid=0',
                'invalid_spreadsheet_url': 'abc',
                'system': System.SPIRE,
                'less_lethal': True
            },
            'heart': {
                'guild_id': -2,
                'valid_spreadsheet_id': '1PzF3ZHQpXXaS0ci0Q0vbE9uHpC26GiUJ4ishIbbcpOY',
                'valid_sheet_name': 'Example Character Sheet',
                'valid_spreadsheet_url': 'https://docs.google.com/spreadsheets/d/1PzF3ZHQpXXaS0ci0Q0vbE9uHpC26GiUJ4ishIbbcpOY/edit#gid=0',
                'invalid_spreadsheet_url': 'abc',
                'system': System.HEART,
                'less_lethal': False
            },
            'heart_depopulated': {
                'guild_id': -1,
                'valid_spreadsheet_id': '1yWC4husblNB7Rd_l6xU2BqbquwpCeNZVn8NACSrqTzs',
                'valid_sheet_name': 'Character 1',
                'valid_spreadsheet_url': 'https://docs.google.com/spreadsheets/d/1yWC4husblNB7Rd_l6xU2BqbquwpCeNZVn8NACSrqTzs/edit#gid=282110671',
                'invalid_spreadsheet_url': 'abc',
                'system': System.HEART,
                'less_lethal': False
            }
        }

        for game_label, game_data in self.all_game_data.items():
            spire_server_dirpath = SpireGame.get_server_dirpath(game_data['guild_id'])
            heart_server_dirpath = HeartGame.get_server_dirpath(game_data['guild_id'])

            self.assertFalse(
                os.path.isdir(spire_server_dirpath),
                f'Cannot run tests because the server dir for "{game_label}" already exists at "{spire_server_dirpath}" - check it isn\'t valid user data somehow.'
            )
    
            self.assertFalse(
                os.path.isdir(heart_server_dirpath),
                f'Cannot run tests because the server dir for "{game_label}" already exists at "{heart_server_dirpath}" - check it isn\'t valid user data somehow.'
            )

            game_data['spire_server_dirpath'] = spire_server_dirpath
            game_data['heart_server_dirpath'] = heart_server_dirpath

            if 'depopulated' in game_label:
                game_data['characters'] = []
            elif 'spire' in game_label:
                game_data['characters'] = [
                    SpireCharacter(
                        character_name='Azuro (he / him)',
                        discord_username='jaffa6',
                        spreadsheet_id=game_data['valid_spreadsheet_id'],
                        sheet_name=game_data['valid_sheet_name']
                    )
                ]
            else:
                game_data['characters'] = [
                    HeartCharacter(
                        character_name='Gruffle McStiltskin (she / her)',
                        discord_username='jaffa6',
                        spreadsheet_id=game_data['valid_spreadsheet_id'],
                        sheet_name=game_data['valid_sheet_name']
                    )
                ]

        self.vermissian = Vermissian()

        for game_label, game_data in self.all_game_data.items():
            if len(game_data['characters']) == 0:
                mock_get_from_spreadsheet_api.return_value = {
                    character.sheet_name: {
                        character.CELL_REFERENCES['name_label']: character.EXPECTED_NAME_LABEL,
                        character.CELL_REFERENCES['biography']['discord_username']: character.discord_username,
                        character.CELL_REFERENCES['biography']['character_name']: character.character_name,
                    } for character in game_data['characters']
                }

            if game_data['system'] == System.SPIRE:
                self.all_game_data[game_label]['game'] = SpireGame(
                    guild_id=game_data['guild_id'],
                    spreadsheet_id=game_data['valid_spreadsheet_id'],
                    less_lethal=game_data['less_lethal'],
                    characters=game_data['characters']
                )
            elif game_data['system'] == System.HEART:
                self.all_game_data[game_label]['game'] = HeartGame(
                    guild_id=game_data['guild_id'],
                    spreadsheet_id=game_data['valid_spreadsheet_id'],
                    characters=game_data['characters']
                )

    def tearDown(self) -> None:
        logging.disable(logging.NOTSET)

        for game_label, game_data in self.all_game_data.items():
            if os.path.isdir(game_data['spire_server_dirpath']):
                shutil.rmtree(game_data['spire_server_dirpath'])

            if os.path.isdir(game_data['heart_server_dirpath']):
                shutil.rmtree(game_data['heart_server_dirpath'])

if __name__ == '__main__':
    unittest.main()
