from typing import Dict

from src.Bot import Bot
from src.ghost_detector.GhostGame import GhostGame
from src.utils.logger import get_logger

class GhostDetector(Bot):

    def __init__(self, *args, **options):
        super().__init__(*args, **options)

        self.games: Dict[int, GhostGame] = {}
        self.logger = get_logger()

    def create_game(self, guild_id: int) -> GhostGame:
        game_data = {
            'guild_id': guild_id,
        }

        new_game = GhostGame(** game_data)

        self.add_game(game=new_game)

        return new_game