import abc
from typing import List, Iterable, Optional

from src.System import System
from src.Game import CharacterKeeperGame
from src.overcharge.DieCharacter import DieCharacter
from src.utils.format import strikethrough, bold
from src.utils.exceptions import UnknownSystemError

class DieGame(CharacterKeeperGame, abc.ABC):
    """
    Represents a Discord server using the bot to play DIE.
    """

    success_threshold = 4
    special_threshold = 6

    def __init__(self, guild_id: int, spreadsheet_id: str, characters: Optional[List[DieCharacter]] = None):
        super().__init__(guild_id, spreadsheet_id, System.DIE, characters)

    @classmethod
    def load(cls, guild_id: int) -> 'DieGame':
        game_data = cls.load_game_data(guild_id)

        if int(game_data['guild_id']) != guild_id:
            raise ValueError(f'Guild IDs do not match up, cannot load data.')

        if game_data['system'] == System.DIE.value:
            return DieGame.from_data(game_data)
        else:
            raise UnknownSystemError(system=game_data['system'])

    @classmethod
    def format_roll(cls, rolled: Iterable[int], indices_to_remove: Iterable[int]) -> List[str]:
        formatted_results = []

        str_cast = lambda s: str(s)

        for index, roll in enumerate(rolled):
            if index in indices_to_remove:
                formatter = strikethrough
            elif roll >= 6:
                formatter = bold
            else:
                formatter = str_cast

            formatted_results.append(formatter(roll))

        return formatted_results