from typing import Dict

from src.Bot import Bot
from src.goblin.GoblinGame import GoblinGame
from src.utils.logger import get_logger

class Goblin(Bot):

    def __init__(self, *args, **options):
        super().__init__(*args, **options)

        self.games: Dict[int, GoblinGame] = {}
        self.logger = get_logger()

    def create_game(self, guild_id: int) -> GoblinGame:
        game_data = {
            'guild_id': guild_id,
        }

        new_game = GoblinGame(** game_data)

        self.add_game(game=new_game)

        return new_game