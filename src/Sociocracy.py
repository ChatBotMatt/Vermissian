import discord

import abc
import uuid
from typing import Dict

from src.utils.logger import get_logger

class SociocracyBot(discord.Bot, abc.ABC):

    def __init__(self, *args, **options):
        super().__init__(*args, **options)

        self.votes: Dict[uuid.UUID, discord.Message] = {}
        self.logger = get_logger()

    async def consent_added(self, text: str, view_uuid: uuid.UUID):
        message = self.votes[view_uuid]

        #print(message.content)

        await message.edit_original_message(content=text)

    async def consent_withdrawn(self, text: str, view_uuid: uuid.UUID):
        message = self.votes[view_uuid]

        #print(message.content)

        await message.edit_original_message(content=text)
