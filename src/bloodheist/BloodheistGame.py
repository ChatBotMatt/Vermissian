import random
import abc
from typing import List, Dict, Tuple, Literal, Iterable, Optional, Any, Union

from src.System import System
from src.bloodheist.BloodheistCharacterSheet import BloodheistCharacterSheet
from src.Roll import Roll
from src.utils.format import bold
from src.utils.logger import get_logger
from src.utils.exceptions import UnknownSystemError

from src.Game import CharacterKeeperGame

class BloodheistGame(CharacterKeeperGame, abc.ABC):
    """
    Represents a Discord server using the bot to play a Bloodheist game.
    """

    CRIT_SUCCESS = 'Full Success'
    SUCCESS = 'Success (no stress)'
    SUCCESS_AT_A_COST = 'Success at a Cost (stress, one dice size lower if avoiding damage)'
    FAILURE = 'Failure'
    CRIT_FAILURE = 'Critical Failure'

    CORE_RESULTS = {
        6: CRIT_SUCCESS,
        4: SUCCESS_AT_A_COST,
        2: FAILURE,
        1: CRIT_FAILURE,
    }

    RESERVED_SHEET_NAMES = [
        'Credits',
        'Changelog',
        'GM Tracker',
        'Lines and Veils',
        'Notes',
        # 'Example Character Sheet' # TODO Re-enable when done testing
        'Special Rules',
        'Rituals',
        'Follies',
        'Professions',
        'Backgrounds',
        'Murderer',
        'Shadowjack',
        'Gearhead',
        'Occultist',
        'Alchemist',
        'Liesmith'
    ]

    def __init__(self, guild_id:  int, spreadsheet_id: str, characters: Optional[List[BloodheistCharacterSheet]] = None):
        super().__init__(guild_id, spreadsheet_id, system=System.BLOODHEIST, characters=characters)

    @classmethod
    def load(cls, guild_id: int) -> 'BloodheistGame':
        game_data = cls.load_game_data(guild_id)

        if int(game_data['guild_id']) != guild_id:
            raise ValueError(f'Guild IDs do not match up, cannot load data.')

        if game_data['system'] == System.BLOODHEIST.value:
            return BloodheistGame.from_data(game_data)
        else:
            raise UnknownSystemError(system=game_data['system'])

    @classmethod
    def format_roll(cls, rolled: Iterable[int], highest: int) -> List[str]:
        formatted_results = []

        str_cast = lambda s: str(s)

        for roll in rolled:
            if roll == highest:
                formatter = bold
            else:
                formatter = str_cast

            formatted_results.append(formatter(roll))

        return formatted_results

    def roll_check(self, username: str, initial_roll: Roll) -> Tuple[int, List[str], str, int]:
        roll = initial_roll

        # TODO Handle Doom here, or a layer above this?

        highest, formatted_results, total = self.roll(roll)

        outcome = self.get_result(highest)

        return highest, formatted_results, outcome, total

    @classmethod
    def roll(cls, roll: Roll) -> Tuple[int, List[str], int]:
        results = []

        for i in range(roll.num_dice):
            result = random.randint(1, roll.dice_size)

            results.append(result + roll.bonus - roll.penalty)

        effective_highest = max(results)

        total = sum(results)

        formatted_results = cls.format_roll(results, effective_highest)

        return effective_highest, formatted_results, total

    @classmethod
    def get_result(cls, highest: int) -> str:
        for threshold, outcome in cls.CORE_RESULTS.items():
            if threshold <= highest:
                return cls.CORE_RESULTS[threshold]

        return cls.CORE_RESULTS[-1]

    def create_character(self, spreadsheet_id: str, sheet_name: str) -> BloodheistCharacterSheet:
        return BloodheistCharacterSheet(spreadsheet_id, sheet_name)

    @staticmethod
    def from_data(game_data: Dict[str, Any]) -> 'BloodheistGame':
        required_fields = ['guild_id', 'system', 'spreadsheet_id']

        for required_field in required_fields:
            if required_field not in game_data:
                raise ValueError(f'Cannot load a Bloodheist game without a "{required_field}" field.')

        if game_data['system'] != System.BLOODHEIST.value:
            raise ValueError(f'Cannot load a Bloodheist game from a non-Bloodheist savedata file.')

        characters = []

        if 'characters' in game_data:
            for discord_username, character_data in game_data['characters'].items():
                try:
                    character = BloodheistCharacterSheet.load(character_data)
                    characters.append(character)
                except ValueError as v:
                    get_logger().error(v)
                    continue

        game = BloodheistGame(
            guild_id=game_data['guild_id'],
            spreadsheet_id=game_data['spreadsheet_id'],
            characters=characters
        )

        return game

    def __str__(self):
        return f'A Bloodheist Game with Guild ID "{self.guild_id}", Spreadsheet ID {self.spreadsheet_id}, and the following characters: {[str(character) for character in self.character_sheets.values()]}'
