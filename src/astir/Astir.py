from typing import Dict

from src.Bot import Bot
from src.astir.AstirGame import AstirGame
from src.System import System
from src.utils.google_sheets import get_spreadsheet_id
from src.utils.exceptions import BadCharacterKeeperError, UnknownSystemError
from src.utils.logger import get_logger

class Astir(Bot):

    def __init__(self, *args, **options):
        super().__init__(*args, **options)

        self.games: Dict[int, AstirGame] = {}
        self.logger = get_logger()

    def create_game(self, guild_id: int, spreadsheet_url: str) -> AstirGame:
        spreadsheet_id = get_spreadsheet_id(spreadsheet_url)

        if spreadsheet_id is None:
            raise BadCharacterKeeperError(spreadsheet_url=spreadsheet_url)

        game_data = {
            'guild_id': guild_id,
            'spreadsheet_id': spreadsheet_id,
        }

        new_game = AstirGame(** game_data)

        self.add_game(game=new_game)

        return new_game