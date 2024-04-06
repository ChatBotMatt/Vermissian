import discord

from typing import Literal, List, Dict, Tuple, Union, Optional

from CharacterSheet import CharacterSheet, SpireSkill, SpireDomain, HeartSkill, HeartDomain
from Game import SpireGame, HeartGame
from Roll import Roll
from utils.google_sheets import get_sheet_name_from_gid, get_spreadsheet_id, get_spreadsheet_sheet_gid
from utils.exceptions import NoSpreadsheetGidError, BadCharacterKeeperError, UnknownSystemError
from System import System

class Vermissian(discord.Bot):

    def __init__(self, *args, **options):
        super().__init__(*args, **options)

        self.player_guilds: Dict[int, Union[SpireGame, HeartGame]] = {}

    def create_game(self, ctx: discord.ApplicationContext, spreadsheet_url: str, system: System, less_lethal: bool = False):
        spreadsheet_id = get_spreadsheet_id(spreadsheet_url)

        if spreadsheet_id is None:
            raise BadCharacterKeeperError(spreadsheet_url=spreadsheet_url)

        game_data = {
            'guild_id': ctx.guild.id,
            'spreadsheet_id': spreadsheet_id,
        }

        if system == System.SPIRE:
            game_cls = SpireGame
            game_data['less_lethal'] = less_lethal
        elif system == System.HEART:
            game_cls = HeartGame
        else:
            raise UnknownSystemError(system=system)

        new_game = game_cls(** game_data)

        self.add_game(guild_id=ctx.guild.id, game=new_game)

    def add_game(self, guild_id: int, game: Union[SpireGame, HeartGame]):
        self.player_guilds[guild_id] = game

    def remove_game(self, guild_id: int):
        if guild_id in self.player_guilds:
            game = self.player_guilds[guild_id]
            game.remove()
            del self.player_guilds[guild_id]

    def add_character(self, guild_id: int, spreadsheet_url: str, user: discord.Member) -> CharacterSheet:
        sheet_gid = get_spreadsheet_sheet_gid(spreadsheet_url)

        if sheet_gid is None:
            raise NoSpreadsheetGidError(spreadsheet_url=spreadsheet_url)

        spreadsheet_id = get_spreadsheet_id(spreadsheet_url)

        sheet_name = get_sheet_name_from_gid(spreadsheet_id, sheet_gid)

        guild = self.player_guilds[guild_id]

        character = guild.create_character(spreadsheet_id, sheet_name)

        character.discord_username = user.name

        guild.add_character(character)

        return character

    def roll_check(self, guild_id: int, user: discord.Member, initial_roll: Roll, skill: Union[SpireSkill, HeartSkill], domain: Union[SpireDomain, HeartDomain]) -> Tuple[int, List[str], str, int, bool, bool, bool]:
        guild = self.player_guilds[guild_id]

        return guild.roll_check(initial_roll=initial_roll, user=user, skill=skill, domain=domain)

    def roll_fallout(self, guild_id: int, user: discord.Member, resistance: Optional[str]) -> Tuple[int, Literal['no', 'Minor', 'Moderate', 'Severe'], int, int]:
        guild = self.player_guilds[guild_id]

        return guild.roll_fallout(user, resistance)

    def get_character(self, guild_id: int, character_name: str) -> CharacterSheet:
        guild = self.player_guilds[guild_id]

        return guild.get_character(character_name)

    def get_fallout_stress(self, guild_id: int, character_name: str):
        guild = self.player_guilds[guild_id]

        character = self.get_character(guild_id, character_name)

        return character.get_fallout_stress(less_lethal=guild.less_lethal)

    def get_result(self, guild_id: int, highest: int):
        guild = self.player_guilds[guild_id]

        return guild.get_result(highest=highest)