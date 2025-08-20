import abc
from typing import Dict

from src.CharacterSheet import CharacterSheet
from src.utils.google_sheets import get_from_spreadsheet_api

class BloodheistCharacterSheet(CharacterSheet, abc.ABC):
    character_name: str

    CELL_REFERENCES = {
        'name_label': 'C3',

        'biography': {
            'discord_username': 'D2',
            'player_name': 'D3',
            'character_name': 'D4',
        },

        'doom': {
            0: 'T3',
            1: 'T4',
            2: 'T5',
            3: 'T6',
            4: 'T7',
            5: 'T8',
            6: 'T9'
        }
    }

    def get_doom_count(self) -> int:
        doom_tracker = get_from_spreadsheet_api(
            spreadsheet_id=self.spreadsheet_id,
            raw_sheet_name_data={
                self.sheet_name: list(self.CELL_REFERENCES['doom'].values())
            }
        )

        for doom_number, cell_reference in self.CELL_REFERENCES['doom'].items():
            if doom_tracker[cell_reference]:
                return doom_number

    @classmethod
    def load(cls, character_data: Dict[str, str]) -> 'BloodheistCharacterSheet':
        return BloodheistCharacterSheet(** character_data)

