import abc
from typing import List, Dict, Tuple, Optional

from src.utils.google_sheets import get_from_spreadsheet_api

class CharacterSheet(abc.ABC):
    EXPECTED_NAME_LABEL = 'Player Name (Pronouns)'

    CELL_REFERENCES = {}

    def __init__(self, spreadsheet_id: str, sheet_name: str, character_name: Optional[str] = None, discord_username: Optional[str] = None, query: bool = True):
        self.spreadsheet_id = spreadsheet_id
        self.sheet_name = sheet_name

        if query and (character_name is None or discord_username is None):
            live_character_name, live_discord_username = self.initialise()

            character_name_to_use = live_character_name
            discord_username_to_use = live_discord_username
        else:
            character_name_to_use = character_name
            discord_username_to_use = discord_username

        self.character_name = character_name_to_use
        self.discord_username = discord_username_to_use

    def initialise(self) -> Tuple[Optional[str], Optional[str]]:
        raw_sheet_data = get_from_spreadsheet_api(
            spreadsheet_id=self.spreadsheet_id,
            raw_sheet_name_data={
                self.sheet_name: [
                    self.CELL_REFERENCES['name_label'],
                    self.CELL_REFERENCES['biography']['discord_username'],
                    self.CELL_REFERENCES['biography']['character_name']
                ]
            }
        )[self.sheet_name]

        # Brittle, but can't think of a better way atm whilst minimising complexity around the sheets.

        name_label_data = raw_sheet_data[self.CELL_REFERENCES["name_label"]]
        if not name_label_data == self.EXPECTED_NAME_LABEL:
            raise ValueError(f'"{self.sheet_name}" is not a character sheet - it does not have a "{self.EXPECTED_NAME_LABEL}" field at {self.CELL_REFERENCES["name_label"]}, it has "{name_label_data}" instead.')

        character_discord_username = raw_sheet_data[self.CELL_REFERENCES['biography']['discord_username']].lower() # Discord usernames are forced to be lowercase

        character_name = raw_sheet_data[self.CELL_REFERENCES['biography']['character_name']]

        return character_name, character_discord_username

    def info(self):
        return {
            'discord_username': self.discord_username,
            'character_name': self.character_name,
            'spreadsheet_id': self.spreadsheet_id,
            'sheet_name': self.sheet_name
        }

    @classmethod
    @abc.abstractmethod
    def load(cls, character_data: Dict[str, str]) -> 'CharacterSheet':
        raise NotImplementedError('Implement Me')

    @classmethod
    def bulk_create(cls, spreadsheet_id: str, sheet_names: List[str]) -> Dict[str, 'CharacterSheet']:
        raw_sheet_name_data_to_query = {
            sheet_name: [
                cls.CELL_REFERENCES['name_label'],
                cls.CELL_REFERENCES['biography']['discord_username'],
                cls.CELL_REFERENCES['biography']['character_name']
            ] for sheet_name in sheet_names
        }

        all_raw_sheet_data = get_from_spreadsheet_api(
            spreadsheet_id=spreadsheet_id,
            raw_sheet_name_data=raw_sheet_name_data_to_query
        )

        valid_characters = {}

        for sheet_name, sheet_data in all_raw_sheet_data.items():
            if cls.is_character_sheet(sheet_data):
                character_discord_username = sheet_data[cls.CELL_REFERENCES['biography']['discord_username']]

                character_name = sheet_data[cls.CELL_REFERENCES['biography']['character_name']]

                valid_characters[sheet_name] = cls(
                    spreadsheet_id=spreadsheet_id,
                    sheet_name=sheet_name,
                    discord_username=character_discord_username,
                    character_name=character_name,
                    query=False # If they don't have the names, they won't have them now either.
                )

        return valid_characters

    @classmethod
    def is_character_sheet(cls, queried_data: Dict[str, str]) -> bool:
        if cls.CELL_REFERENCES['name_label'] not in queried_data:
            return False

        # Brittle, but can't think of a better way atm whilst minimising complexity around the sheets.
        if queried_data[cls.CELL_REFERENCES['name_label']] == cls.EXPECTED_NAME_LABEL:
            return True

        return False

    def __eq__(self, other: 'CharacterSheet'):
        return type(self) == type(other) and self.info() == other.info()

    def __str__(self):
        character_name = self.character_name or '[Unnamed Character]'
        discord_username = self.discord_username or '[Unknown User]'

        return f'{character_name} is a {self.__class__} linked to {discord_username} from Spreadsheet {self.spreadsheet_id} Sheet {self.sheet_name}'
