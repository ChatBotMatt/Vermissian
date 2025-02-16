from typing import Dict, Union

from src.Bot import Bot
from src.vermissian.ResistanceGame import SpireGame, HeartGame
from src.System import System
from src.utils.google_sheets import get_spreadsheet_id
from src.utils.exceptions import BadCharacterKeeperError, UnknownSystemError
from src.utils.logger import get_logger

class Vermissian(Bot):

    def __init__(self, *args, **options):
        super().__init__(*args, **options)

        self.games: Dict[int, Union[SpireGame, HeartGame]] = {}
        self.logger = get_logger()

    def create_game(self, guild_id: int, spreadsheet_url: str, system: System, less_lethal: bool = False) -> Union[SpireGame, HeartGame]:
        spreadsheet_id = get_spreadsheet_id(spreadsheet_url)

        if spreadsheet_id is None:
            raise BadCharacterKeeperError(spreadsheet_url=spreadsheet_url)

        game_data = {
            'guild_id': guild_id,
            'spreadsheet_id': spreadsheet_id,
        }

        if system == System.SPIRE:
            game_cls = SpireGame
            game_data['less_lethal'] = less_lethal
        elif system == System.HEART:
            game_cls = HeartGame
        else:
            raise UnknownSystemError(system=system.value)

        new_game = game_cls(** game_data)

        self.add_game(game=new_game)

        return new_game