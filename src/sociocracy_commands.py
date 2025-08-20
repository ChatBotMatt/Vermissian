import discord
import json
import random
import functools
import re
from typing import List, Tuple, Dict, Optional, Set, Union, Literal, Iterable

from src.vermissian.Vermissian import Vermissian
from src.vermissian.ResistanceGame import ResistanceGame, SpireGame, HeartGame
from src.Game import Game
from src.System import System
from src.vermissian.ResistanceCharacterSheet import SpireSkill, SpireDomain, HeartSkill, HeartDomain
from src.Roll import Roll, Cut
from src.utils.format import bold, underline, code, quote, bullet, no_embed
from src.utils.logger import get_logger
from src.utils.exceptions import WrongGameError
from extract_abilities import Ability

class StressRollerView(discord.ui.View):
    """
    A view which allows the user to pick via buttons how much stress to roll.
    """

    def __init__(self, * args, stress_sizes: List[int], ** kwargs):
        super().__init__(* args, ** kwargs)

        if any(stress_size < 1 for stress_size in stress_sizes):
            raise ValueError(f'Invalid stress size passed in "{stress_sizes}", must be at least 1.')

        for stress_size in stress_sizes:
            button =discord.ui.Button(label=f'Roll d{stress_size} stress', style=discord.ButtonStyle.primary)
            button.callback = functools.partial(StressRollerView.roll_stress, stress_size=stress_size)

            self.add_item(button)

    @staticmethod
    async def roll_stress(interaction: discord.Interaction, stress_size: int):
        """
        Rolls the stress and sends the output as a reply to the roll message.

        :param interaction: The interaction with the button.
        :param stress_size: The amount of stress to roll.
        """

        roll_to_do = Roll(dice_size=stress_size, num_dice=1)
        result = simple_roll([roll_to_do], note='Stress')

        await interaction.response.send_message(result)
