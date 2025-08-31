import abc
import os
import json
import shutil
from typing import List, Dict, Optional, Any

from src.System import System
from src.vermissian.ResistanceCharacterSheet import HeartCharacter, SpireCharacter
from src.overcharge.DieCharacter import DieCharacter
from src.astir.AstirCharacterSheet import AstirCharacter
from src.bloodheist.BloodheistCharacterSheet import BloodheistCharacterSheet
from src.CharacterSheet import CharacterSheet
from src.utils.google_sheets import get_spreadsheet_metadata, get_spreadsheet_sheet_gid, get_sheet_name_from_gid, get_spreadsheet_id
from src.utils.logger import get_logger
from src.utils.exceptions import NoSpreadsheetGidError

class Game(abc.ABC):
    """
    Represents a Discord server using the bot.
    """

    def __init__(
        self,
        guild_id: int,
        system: System
    ):
        self.guild_id = guild_id
        self.system = system

        self.server_info_dirpath = os.path.join('servers', str(guild_id))

        os.makedirs(self.server_info_dirpath, exist_ok=True)

        self.logger = get_logger()

    @staticmethod
    @abc.abstractmethod
    def from_data(game_data: Dict[str, Any]):
        raise NotImplementedError('Implement me!')

    @classmethod
    def get_server_dirpath(cls, guild_id: int) -> str:
        return os.path.join('servers', str(guild_id))

    @classmethod
    def get_game_data_filepath(cls, guild_id: int) -> str:
        return os.path.join(cls.get_server_dirpath(guild_id), 'game_data.json')

    @classmethod
    def load_game_data(cls, guild_id: int) -> Dict[str, Any]:
        game_data_filepath = cls.get_game_data_filepath(guild_id)

        if not os.path.exists(game_data_filepath):
            raise FileNotFoundError(f'No game data found for Guild ID "{guild_id}"')

        with open(game_data_filepath, 'r', encoding='utf-8') as f:
            game_data = json.load(f)

        return game_data

    def save(self):
        server_dir_path = self.get_server_dirpath(self.guild_id)

        os.makedirs(server_dir_path, exist_ok=True)

        with open(self.get_game_data_filepath(self.guild_id), 'w', encoding='utf-8') as f:
            json.dump(self.game_data, f, indent=4)

    def remove(self):
        server_dir_path = self.get_server_dirpath(self.guild_id)

        if os.path.isdir(server_dir_path):
            shutil.rmtree(server_dir_path)

    @property
    def game_data(self):
        game_data = {
            'guild_id': self.guild_id,
            'system': self.system.value
        }

        return game_data

    def __eq__(self, other: 'Game'):
        if type(self) == type(other) and self.guild_id == other.guild_id:
            return True

        return False

class CharacterKeeperGame(Game):
    """
    Represents a Discord server using the bot.
    """

    RESERVED_SHEET_NAMES = []

    def __init__(
        self,
        guild_id: int,
        spreadsheet_id: str,
        system: System,
        characters: Optional[List[CharacterSheet]] = None
    ):
        super().__init__(guild_id=guild_id, system=system)

        self.spreadsheet_id = spreadsheet_id

        self.spreadsheet_metadata = get_spreadsheet_metadata(self.spreadsheet_id)

        self.character_sheets: Dict[str, CharacterSheet] = {}

        self.character_file_data = {}

        if characters is None:
            characters = []

        characters = [character for character in characters if character.discord_username is not None]

        if len(characters) == 0:
            sheet_names_to_query = []
            sheet_gids_to_query = []
            for sheet_gid, sheet_name in self.spreadsheet_metadata.items():
                if sheet_name in self.RESERVED_SHEET_NAMES:
                    continue

                sheet_names_to_query.append(sheet_name)
                sheet_gids_to_query.append(sheet_gid)

            if system == System.SPIRE:
                character_cls = SpireCharacter
            elif system == System.HEART:
                character_cls = HeartCharacter
            elif system == System.DIE:
                character_cls = DieCharacter
            elif system == System.ASTIR:
                character_cls = AstirCharacter
            elif system == System.BLOODHEIST:
                character_cls = BloodheistCharacterSheet
            else:
                raise ValueError(f'Unknown system: {system}')

            queried_characters: Dict[str, CharacterSheet] = character_cls.bulk_create(
                spreadsheet_id=spreadsheet_id,
                sheet_names=sheet_names_to_query,
                sheet_gids=sheet_gids_to_query,
            )

            for sheet_name, character in queried_characters.items():
                if character.discord_username is not None:
                    characters.append(character)

        for character in characters:
            self.character_sheets[character.discord_username.lower()] = character

    def add_character(self, spreadsheet_url: str, username: str) -> CharacterSheet:
        sheet_gid = get_spreadsheet_sheet_gid(spreadsheet_url)

        if sheet_gid is None:
            raise NoSpreadsheetGidError(spreadsheet_url=spreadsheet_url)

        spreadsheet_id = get_spreadsheet_id(spreadsheet_url)

        sheet_name = get_sheet_name_from_gid(spreadsheet_id, sheet_gid)

        character = self.create_character(spreadsheet_id, sheet_name, sheet_gid)

        character.discord_username = username

        self.character_sheets[character.discord_username.lower()] = character

        return character

    def get_character(self, username: str) -> CharacterSheet:
        if username.lower() in self.character_sheets:
            return self.character_sheets[username.lower()]

        raise ValueError(f'No character linked to "{username}": Known user-characters are {list(self.character_sheets.keys())}')

    @abc.abstractmethod
    def create_character(self, spreadsheet_id: str, sheet_name: str, sheet_gid: int):
        raise NotImplementedError('Implement me!')

    @property
    def game_data(self):
        game_data = {
            'guild_id': self.guild_id,
            'system': self.system.value,
            'spreadsheet_id': self.spreadsheet_id,
            'characters': {
                discord_username.lower(): character.info() for discord_username, character in self.character_sheets.items()
            },
        }

        return game_data

    def __eq__(self, other: 'CharacterKeeperGame'):
        if type(self) == type(other) and \
                self.guild_id == other.guild_id and \
                self.spreadsheet_id == other.spreadsheet_id and \
                self.character_sheets == other.character_sheets:
            return True

        return False