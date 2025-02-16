import random
from dataclasses import dataclass
from typing import List, Dict, Any, Literal, Iterable, Optional

from src.System import System
from src.utils.format import strikethrough, bold
from src.utils.exceptions import UnknownSystemError

from src.Game import Game

class GoblinGame(Game):
    """
    Represents a Discord server using the bot to play a "Goblin Quest" game.
    """

    def __init__(self, guild_id: int):
        super().__init__(guild_id=guild_id, system=System.GOBLIN)

    @classmethod
    def load(cls, guild_id: int) -> 'GoblinGame':
        game_data = cls.load_game_data(guild_id)

        if int(game_data['guild_id']) != guild_id:
            raise ValueError(f'Guild IDs do not match up, cannot load data.')

        if game_data['system'] == System.GOBLIN.value:
            return GoblinGame.from_data(game_data)
        else:
            raise UnknownSystemError(system=game_data['system'])

    @classmethod
    def format_roll(cls, rolled: Iterable[int], indices_to_remove: Iterable[int], highest: int) -> List[str]:
        formatted_results = []

        str_cast = lambda s: str(s)

        for index, roll in enumerate(rolled):
            if index in indices_to_remove:
                formatter = strikethrough
            elif roll == highest:
                formatter = bold
            else:
                formatter = str_cast

            formatted_results.append(formatter(roll))

        return formatted_results

    @property
    def game_data(self):
        game_data = super().game_data

        return game_data

    @staticmethod
    def from_data(game_data: Dict[str, Any]) -> 'GoblinGame':
        required_fields = ['guild_id']

        for required_field in required_fields:
            if required_field not in game_data:
                raise ValueError(f'Cannot load a "Goblin Quest" game without a "{required_field}" field.')

        if game_data['system'] != System.GHOST_GAME.value:
            raise ValueError(f'Cannot load a "Goblin Quest" game from a non-"Goblin Quest" savedata file.')

        game = GoblinGame(
            guild_id=game_data['guild_id'],
        )

        return game
