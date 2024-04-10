import abc
import enum
from typing import List, Dict, Tuple, Optional, Literal, Union

from utils.google_sheets import get_from_spreadsheet_api

class SpireSkill(enum.Enum):
    COMPEL      = 'Compel'
    DECEIVE     = 'Deceive'
    FIGHT       = 'Fight'
    FIX         = 'Fix'
    INVESTIGATE = 'Investigate'
    PURSUE      = 'Pursue'
    RESIST      = 'Resist'
    SNEAK       = 'Sneak'
    STEAL       = 'Steal'

    @classmethod
    def get(cls, name: str):
        for skill in SpireSkill:
            if skill.value.lower() == name.lower():
                return skill

        raise ValueError(f'Unknown Spire skill: {name}')

class SpireDomain(enum.Enum):
    ACADEMIA        = 'Academia'
    CRIME           = 'Crime'
    COMMERCE        = 'Commerce'
    HIGH_SOCIETY    = 'High Society'
    LOW_SOCIETY     = 'Low Society'
    OCCULT          = 'Occult'
    ORDER           = 'Order'
    RELIGION        = 'Religion'
    TECHNOLOGY      = 'Technology'

    @classmethod
    def get(cls, name: str):
        for domain in SpireDomain:
            if domain.value.lower() == name.lower():
                return domain

        raise ValueError(f'Unknown Spire domain: {name}')

class HeartSkill(enum.Enum):
    COMPEL  = 'Compel'
    DELVE   = 'Delve'
    DISCERN = 'Discern'
    ENDURE  = 'Endure'
    EVADE   = 'Evade'
    HUNT    = 'Hunt'
    KILL    = 'Kill'
    MEND    = 'Mend'
    SNEAK   = 'Sneak'

    @classmethod
    def get(cls, name: str):
        for skill in HeartSkill:
            if skill.value.lower() == name.lower():
                return skill

        raise ValueError(f'Unknown Heart skill: {name}')

class HeartDomain(enum.Enum):
     CURSED     = 'Cursed'
     DESOLATE   = 'Desolate'
     HAVEN      = 'Haven'
     OCCULT     = 'Occult'
     RELIGION   = 'Religion'
     TECHNOLOGY = 'Technology'
     WARREN     = 'Warren'
     WILD       = 'Wild'

     @classmethod
     def get(cls, name: str):
         for domain in HeartDomain:
             if domain.value.lower() == name.lower():
                 return domain

         raise ValueError(f'Unknown Heart Domain: {name}')

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

    def check_skill_and_domain(self, skill: Union[SpireSkill, HeartSkill], domain: Union[SpireDomain, HeartDomain]) -> Tuple[bool, bool]:
        skill_reference = self.CELL_REFERENCES['skills'][skill.value.title()]
        domain_reference = self.CELL_REFERENCES['domains'][domain.value.title()]

        raw_skills_domains = get_from_spreadsheet_api(
            spreadsheet_id=self.spreadsheet_id,
            raw_sheet_name_data={
                self.sheet_name: [
                    skill_reference,
                    domain_reference
                ]
            }
        )[self.sheet_name]

        has_skill = False
        has_domain = False

        if raw_skills_domains[skill_reference] == 'TRUE':
            has_skill = True

        if raw_skills_domains[domain_reference] == 'TRUE':
            has_domain = True

        return has_skill, has_domain

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
        if raw_sheet_data[self.CELL_REFERENCES['name_label']] == self.EXPECTED_NAME_LABEL:
            valid_character = True
        else:
            valid_character = False

        if not valid_character:
            raise ValueError(f'"{self.sheet_name}" is not a character sheet - it does not have a "{self.EXPECTED_NAME_LABEL}" field at {self.CELL_REFERENCES["name_label"]}')

        character_discord_username = raw_sheet_data[self.CELL_REFERENCES['biography']['discord_username']]

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

class SpireCharacter(CharacterSheet):
    character_name: str

    CELL_REFERENCES = {
        'name_label': 'B4',

        'biography': {
            'discord_username': 'D3',
            'player_name': 'D4',
            'character_name': 'D5',
        },

        'stress': {
            'Blood': {
                'free': 'C12',
                'total': 'D12',
                'fallout': 'E12',
            },
            'Mind': {
                'free': 'C13',
                'total': 'D13',
                'fallout': 'E13',
            },
            'Silver': {
                'free': 'C14',
                'total': 'D14',
                'fallout': 'E14',
            },
            'Shadow': {
                'free': 'C15',
                'total': 'D15',
                'fallout': 'E15',
            },
            'Reputation': {
                'free': 'C16',
                'total': 'D16',
                'fallout': 'E16',
            },
            'Total': {
                'fallout': 'E18'
            }
        },

        'skills': {
            'Compel': 'H11',
            'Deceive': 'H12',
            'Fight': 'H13',
            'Fix': 'H14',
            'Investigate': 'H15',
            'Pursue': 'H16',
            'Resist': 'H17',
            'Sneak': 'H18',
            'Steal': 'H19'
        },

        'domains': {
            'Academia': 'J11',
            'Crime': 'J12',
            'Commerce': 'J13',
            'High Society': 'J14',
            'Low Society': 'J15',
            'Occult': 'J16',
            'Order': 'J17',
            'Religion': 'J18',
            'Technology': 'J19'
        },

        'abilities': 'L3:L19',  # Every other row

        'knacks': 'L23:L32',
        'equipment': 'O23:O32',
        'refresh': 'R23:R32',

        'bonds': {
            'names': 'U23:U32',
            'levels': 'U23:U32',
            'stresses': 'X23:X32'
        }
    }

    RESISTANCES = ['Blood', 'Mind', 'Silver', 'Shadow', 'Reputation']

    def get_fallout_stress(self, less_lethal: bool = False, resistance: Optional[Literal['Blood', 'Mind', 'Silver', 'Shadow', 'Reputation']] = None) -> int:
        if resistance not in self.RESISTANCES:
            raise ValueError(f'Unknown resistance: "{resistance}"')

        if less_lethal:
            ranges_or_cells = self.CELL_REFERENCES['stress'][resistance]['fallout']
        else:
            ranges_or_cells = self.CELL_REFERENCES['stress']['Total']['fallout']

        stress = get_from_spreadsheet_api(
            spreadsheet_id=self.spreadsheet_id,
            raw_sheet_name_data={
                self.sheet_name: ranges_or_cells
            }
        )[self.sheet_name][ranges_or_cells]

        return stress

    @classmethod
    def load(cls, character_data: Dict[str, str]) -> 'SpireCharacter':
        return SpireCharacter(**character_data)

class HeartCharacter(CharacterSheet):

    CELL_REFERENCES = {
        'name_label': 'B4',

        'biography': {
            'discord_username': 'D3',
            'player_name': 'D4',
            'character_name': 'D5',
        },

        'stress': {
            'Blood': {
                'protection': 'C13',
                'fallout': 'D13',
            },
            'Echo': {
                'protection': 'C14',
                'fallout': 'D14',
            },
            'Mind': {
                'protection': 'C15',
                'fallout': 'D15',
            },
            'Fortune': {
                'protection': 'C16',
                'fallout': 'D16',
            },
            'Supplies': {
                'protection': 'C17',
                'fallout': 'D17',
            },
            'Total': {
                'fallout': 'D18'
            }
        },

        'skills': {
            'Compel': 'G12',
            'Delve': 'G13',
            'Discern': 'G14',
            'Endure': 'G15',
            'Evade': 'G16',
            'Hunt': 'G17',
            'Kill': 'G18',
            'Mend': 'G19',
            'Sneak': 'G20'
        },

        'domains': {
            'Cursed': 'I12',
            'Desolate': 'I13',
            'Haven': 'I14',
            'Occult': 'I15',
            'Religion': 'I16',
            'Technology': 'I17',
            'Warren': 'I18',
            'Wild': 'I19',
        },

        'abilities': 'L3:L19',  # Every other row

        'knacks': 'L26:L35',
        'equipment': 'O26:O35',
        'refresh': 'R26:R35',

        'bonds': {
            'names': 'U26:U35',
            'levels': 'U26:U35',
            'stresses': 'X26:X35'
        }
    }

    RESISTANCES = ['Blood', 'Echo', 'Mind', 'Fortune', 'Supplies']

    def get_fallout_stress(self) -> int:
        ranges_or_cells = self.CELL_REFERENCES['stress']['Total']['fallout']

        stress = get_from_spreadsheet_api(
            spreadsheet_id=self.spreadsheet_id,
            raw_sheet_name_data={
                self.sheet_name: ranges_or_cells
            }
        )[self.sheet_name][ranges_or_cells]

        return stress

    @classmethod
    def load(cls, character_data: Dict[str, str]) -> 'HeartCharacter':
        return HeartCharacter(**character_data)