from typing import Dict

from src.CharacterSheet import CharacterSheet

class DieCharacter(CharacterSheet):
    CELL_REFERENCES = {
        'name_label': 'B2',

        'biography': {
            'discord_username': 'F2',
            'player_name': 'B3',
            'character_name': 'B4',
        },

        'stats': {
            'str': 'B9',
            'dex': 'C9',
            'con': 'D9',
            'int': 'E9',
            'wis': 'F9',
            'cha': 'G9',

            'max_guard': 'B11',
            'guard': 'C11',
            'max_heath': 'D11',
            'current_health': 'E11',
            'willpower': 'F11',
            'defence': 'G11',
        },

    }

    EXPECTED_NAME_LABEL = 'Discord Username: '

    @classmethod
    def load(cls, character_data: Dict[str, str]) -> 'DieCharacter':
        return DieCharacter(**character_data)