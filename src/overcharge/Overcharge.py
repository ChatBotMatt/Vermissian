from typing import Dict

from src.Bot import Bot
from src.overcharge.DieGame import DieGame
from src.utils.google_sheets import get_spreadsheet_id
from src.utils.exceptions import BadCharacterKeeperError
from src.utils.logger import get_logger

class Overcharge(Bot):

    def __init__(self, *args, **options):
        super().__init__(*args, **options)

        self.games: Dict[int, DieGame] = {}
        self.logger = get_logger()

    def create_game(self, guild_id: int, spreadsheet_url: str) -> DieGame:
        spreadsheet_id = get_spreadsheet_id(spreadsheet_url)

        if spreadsheet_id is None:
            raise BadCharacterKeeperError(spreadsheet_url=spreadsheet_url)

        new_game = DieGame(guild_id=guild_id, spreadsheet_id=spreadsheet_id)

        self.add_game(game=new_game)

        return new_game
