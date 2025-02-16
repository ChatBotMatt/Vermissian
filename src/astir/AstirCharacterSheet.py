import collections
import enum
import functools
import re
from typing import Dict, Tuple, Union, List

from src.CharacterSheet import CharacterSheet
from src.utils.google_sheets import get_from_spreadsheet_api, offset_reference
from src.utils.exceptions import BotError
from src.utils.logger import get_logger
from src.astir.utils import load_moves
from src.astir.AstirMove import AstirMove

class AstirTrait(enum.Enum):
    DEFY    = 'Defy'
    SENSE   = 'Sense'
    CLASH   = 'Clash'
    TALK    = 'Talk'
    KNOW    = 'Know'
    CHANNEL = 'Channel' # Only for Astir classes
    HOME    = 'Home' # Only for Adrift
    CREW    = 'Crew'
    GRAVITY = 'Gravity'

    @classmethod
    def get(cls, name: str):
        for skill in AstirTrait:
            if skill.value.lower() == name.lower():
                return skill

        raise ValueError(f'Unknown Armour Astir trait: {name}')

    def __hash__(self):
        return hash(self.value)

class AstirCharacter(CharacterSheet):
    character_name: str

    CELL_REFERENCES = {
        'name_label': 'Q4',

        'biography': {
            'discord_username': 'AL2',
            'player_name': 'AL2',
            'character_name': 'Q2',
        },

        'traits': {
            AstirTrait.DEFY: 'D16',
            AstirTrait.SENSE: 'K16',
            AstirTrait.CLASH: 'R16',
            AstirTrait.TALK: 'Y16',
            AstirTrait.KNOW: 'AF16',
            # Define Channel/Home dynamically since its position is class-dependent

            AstirTrait.CHANNEL: 'AM16', # For Astir character sheets
            AstirTrait.CREW: 'Cause / Factions!AQ15'
        },

        'playbook_name': 'B2',

        'dangers': 'C21:S26',

        'all_non_astir_moves_range': 'BY5:ES200',
        'astir_move_label': 'AX33' # Only Channelers will have this

        # TODO BY1:ES129 is the range where all moves are, not incl. Astir Move,
        #  may be worth setting up a query for to handle multiclassing and checking additional moves.
    }

    EXPECTED_NAME_LABEL = "NAME & PRONOUNS"

    ASTIR_PLAYBOOKS = [
        'Arcanist', 'Impostor', 'Paradigm', 'Witch',
        'Wither', 'Adrift', 'Advocate', 'Revenant', 'Summoner', # AA:Encore classes
    ]

    NON_ASTIR_PLAYBOOKS = [
        'Captain', 'Diplomat', 'Artificer', 'Scout',
        'Icon', 'Commander', 'Attendant',  # AA:Encore classes
    ]

    TWO_STARTING_MOVE_OPTIONS_PLAYBOOKS = [
        'Scout', 'Advocate',
    ]

    TWO_STARTING_MOVES_PLAYBOOKS = [
        'Commander', 'Revenant'
    ]

    def __init__(self, * args, ** kwargs):
        super().__init__(* args, ** kwargs)

        playbook_name = get_from_spreadsheet_api(
            spreadsheet_id=self.spreadsheet_id,
            raw_sheet_name_data={
                self.sheet_name: [
                    self.CELL_REFERENCES['playbook_name'],
                ]
            }
        )[self.sheet_name][self.CELL_REFERENCES['playbook_name']].title()

        if playbook_name == 'Adrift':
            self.CELL_REFERENCES['traits'][AstirTrait.HOME] = 'AL16'
            self.CELL_REFERENCES['approach'] = 'AJ11'
        else:
            if playbook_name in self.ASTIR_PLAYBOOKS:
                self.CELL_REFERENCES['approach'] = 'AJ11'
                self.CELL_REFERENCES['astir_move'] = 'AX33'
            elif playbook_name in self.NON_ASTIR_PLAYBOOKS:
                self.CELL_REFERENCES['approach'] = 'AL16'
            else:
                raise BotError(f'Unknown playbook: "{playbook_name}"')

        if playbook_name == 'Impostor':
            self.CELL_REFERENCES['arcane_augments_move_name'] = 'BY5'

        if playbook_name in self.TWO_STARTING_MOVE_OPTIONS_PLAYBOOKS:
            self.CELL_REFERENCES['starting_move_option_one'] = 'CA5'
            self.CELL_REFERENCES['starting_move_option_one_checkbox'] = 'BY5'

            self.CELL_REFERENCES['starting_move_option_two'] = 'DL5'
            self.CELL_REFERENCES['starting_move_option_two_checkbox'] = 'DJ5'

            self.get_starting_move = self._get_single_starting_move_from_options

        elif playbook_name in self.TWO_STARTING_MOVES_PLAYBOOKS:
            if playbook_name == 'Revenant':
                self.CELL_REFERENCES['starting_move_one'] = 'BY5'
                self.CELL_REFERENCES['starting_move_two'] = 'BY23'
            else:
                self.CELL_REFERENCES['starting_move_one'] = 'BY5'
                self.CELL_REFERENCES['starting_move_two'] = 'DJ5'

            self.get_starting_move = self._get_two_starting_moves
        else:
            self.CELL_REFERENCES['starting_move'] = 'BY5'

            self.get_starting_move = self._get_single_starting_move

    def _get_single_starting_move(self) -> str:
        results: Dict[str, str] = get_from_spreadsheet_api(
            spreadsheet_id=self.spreadsheet_id,
            raw_sheet_name_data={
                self.sheet_name: [
                    self.CELL_REFERENCES['starting_move']
                ]
            }
        )[self.sheet_name]

        return results[self.CELL_REFERENCES['starting_move']]

    def _get_single_starting_move_from_options(self) -> str:
        results: Dict[str, str] = get_from_spreadsheet_api(
            spreadsheet_id=self.spreadsheet_id,
            raw_sheet_name_data={
                self.sheet_name: [
                    self.CELL_REFERENCES['starting_move_option_one'],
                    self.CELL_REFERENCES['starting_move_option_one_checkbox'],
                    self.CELL_REFERENCES['starting_move_option_two'],
                    self.CELL_REFERENCES['starting_move_option_two_checkbox']
                ]
            }
        )[self.sheet_name]

        get_logger().info(results)

        if len(self.CELL_REFERENCES['starting_move_option_one_checkbox']):
            return results[self.CELL_REFERENCES['starting_move_option_one']]
        elif len(self.CELL_REFERENCES['starting_move_option_two_checkbox']):
            return results[self.CELL_REFERENCES['starting_move_option_two']]
        else:
            raise ValueError(f'No starting move found from "{self.spreadsheet_id} {self.sheet_name}": {results}')

    def _get_two_starting_moves(self) -> Tuple[str, str]:
        results: Dict[str, str] = get_from_spreadsheet_api(
            spreadsheet_id=self.spreadsheet_id,
            raw_sheet_name_data={
                self.sheet_name: [
                    self.CELL_REFERENCES['starting_move_one'],
                    self.CELL_REFERENCES['starting_move_two']
                ]
            }
        )[self.sheet_name]

        return results[self.CELL_REFERENCES['starting_move_one']], results[self.CELL_REFERENCES['starting_move_two']]

    @staticmethod
    def _check_spreadsheet_range_or_cell(range_or_cell_data: Union[str, List[str], List[List[str]]], query: str) -> bool:
        if isinstance(range_or_cell_data, str):
            return AstirCharacter._check_spreadsheet_range_or_cell([
                [
                    range_or_cell_data
                ]
            ], query)
        elif isinstance(range_or_cell_data, list) and isinstance(range_or_cell_data[0], str):
            return AstirCharacter._check_spreadsheet_range_or_cell([
                range_or_cell_data
            ], query)

        processed_query = query.lower().strip()

        if range_or_cell_data is None: # TODO This was None when Rutger tried to read the room?
            return False

        for range_or_cell_wrapper in range_or_cell_data:
            for cell in range_or_cell_wrapper:
                if cell.lower().strip() == processed_query:
                    return True

        return False

    def get_all_moves(self) -> Dict[str, AstirMove]: # TODO This needs to filter for ones they've actually got checked
        references = [
            self.CELL_REFERENCES['all_non_astir_moves_range'],
            self.CELL_REFERENCES['astir_move_label']
        ]

        raw_moves_data = get_from_spreadsheet_api(
            spreadsheet_id=self.spreadsheet_id,
            raw_sheet_name_data={
                self.sheet_name: references
            }
        )[self.sheet_name]

        all_moves = load_moves()

        all_move_names = set()

        for playbook, playbook_moves in all_moves.items():
            all_move_names = all_move_names.union(playbook_moves.keys())

        found = {}
        for cell_reference, all_cell_data in raw_moves_data.items():
            for playbook, playbook_moves in all_moves.items():
                for move_name, move in playbook_moves.items():
                    if AstirCharacter._check_spreadsheet_range_or_cell(all_cell_data, move_name):
                        found[move_name] = move

        return found

    @staticmethod
    def _find_moves_in_spreadsheet_data(spreadsheet_data: Dict[str, str]) -> Dict[str, AstirMove]:
        all_moves = load_moves()

        all_move_names = set()

        for playbook, playbook_moves in all_moves.items():
            all_move_names = all_move_names.union(playbook_moves.keys())

        found = {}
        for cell_reference, cell_data in spreadsheet_data:
            move_name_candidate = cell_data.lower().strip()
            if move_name_candidate in all_move_names:
                move = all_moves[move_name_candidate]

                found[move_name_candidate] = move

        return found

    @staticmethod
    @functools.lru_cache()
    def get_trait_label_reference(trait_reference: str):
        match = re.fullmatch('([A-Z]+)([0-9]+)', trait_reference)

        if match is None:
            raise ValueError(f'Cannot identify column and row from reference "{trait_reference}".')

        return offset_reference(trait_reference, column_offset=-1, row_offset=-2)

    def get_playbook(self) -> str:
        playbook_name_reference = self.CELL_REFERENCES['playbook_name']

        results = get_from_spreadsheet_api(
            spreadsheet_id=self.spreadsheet_id,
            raw_sheet_name_data={
                self.sheet_name: [
                    playbook_name_reference
                ]
            }
        )[self.sheet_name]

        playbook = results[playbook_name_reference]

        return playbook

    def split_sheet_name_reference(self, sheet_name_reference: str):
        match = re.fullmatch('(.+)!([A-Z]+[0-9]+)', sheet_name_reference)

        if match is None:
            sheet_name = self.sheet_name
            column_row = sheet_name_reference
        else:
            sheet_name = match.group(1)
            column_row = match.group(2)

        return sheet_name, column_row

    def get_trait(self, trait: AstirTrait) -> Tuple[int, str]:
        warning = ''

        if trait not in self.CELL_REFERENCES['traits']:
            get_logger().warning(f'We do not have a cell reference for {trait} - playbook is {self.get_playbook()}')
            modifier = 0
            warning = f'Cannot find trait "{trait.value}" in your playbook. Assuming a value of 0.'
        else:
            trait_reference = self.CELL_REFERENCES['traits'][trait]

            trait_sheet_name, trait_column_row_reference = self.split_sheet_name_reference(trait_reference)

            class_name_reference = self.CELL_REFERENCES['playbook_name']
            dangers_reference = self.CELL_REFERENCES['dangers']
            trait_label_reference = self.get_trait_label_reference(trait_column_row_reference)

            # Handle Arcane Augments boosting this by # dangers upto +3
            # TODO The sheet actually handles this automatically, so only check the multiclass of it.
            checking_for_arcane_augments = ( trait == AstirTrait.CHANNEL )

            references = []
            if checking_for_arcane_augments:
                references.append(class_name_reference)
                references.append(dangers_reference)
                references.extend([
                    self.CELL_REFERENCES['all_non_astir_moves_range'],
                    self.CELL_REFERENCES['astir_move_label']
                ])

            sheet_name_data = collections.defaultdict(list)
            sheet_name_data[self.sheet_name].extend(references)
            sheet_name_data[trait_sheet_name].append(trait_column_row_reference)
            sheet_name_data[trait_sheet_name].append(trait_label_reference)

            results = get_from_spreadsheet_api(
                spreadsheet_id=self.spreadsheet_id,
                raw_sheet_name_data=sheet_name_data
            )

            modifier = results[trait_sheet_name][trait_column_row_reference].replace('–', '-')

            # Impostor already does this on the sheet itself, so don't do again
            if checking_for_arcane_augments and results[self.sheet_name][class_name_reference].title() != 'Impostor':
                num_dangers = len([cell for cell in results[self.sheet_name][dangers_reference] if len(cell)])

                modifier = int(modifier)

                modifier += num_dangers

                modifier = min(modifier, 3)

            trait_label = results[trait_sheet_name][trait_label_reference]

            does_not_have_skill = trait_label.lower() != trait.value.lower()
            if does_not_have_skill:
                get_logger().warning(f'Queried sheet "{self.spreadsheet_id}" for "{trait.value}" but got "{trait_label}" instead.')
                warning = f'Cannot find trait "{trait.value}" in your playbook. Assuming a value of 0.'
                return 0, warning

        return int(modifier), warning

    @classmethod
    def load(cls, character_data: Dict[str, str]) -> 'AstirCharacter':
        return AstirCharacter(**character_data)