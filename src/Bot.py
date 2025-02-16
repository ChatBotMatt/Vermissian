import discord

import abc
from typing import Dict

from src.Game import Game
from src.utils.logger import get_logger

class Bot(discord.Bot, abc.ABC):

    def __init__(self, *args, **options):
        super().__init__(*args, **options)

        self.games: Dict[int, Game] = {}
        self.logger = get_logger()

    def add_game(self, game: Game):
        self.games[game.guild_id] = game
        game.save()

    def remove_game(self, guild_id: int):
        if guild_id in self.games:
            game = self.games[guild_id]
            game.remove()
            del self.games[guild_id]
        else:
            self.logger.warning(f'Asked to remove game with guild ID {guild_id}, but no game by that ID exists.')
