import discord

import requests
import dotenv

import json
import os
import functools
import atexit
import uuid
from typing import Callable, Union


from src.utils.format import underline
from src.utils.logger import get_logger
from src.utils.exceptions import BotError
from src.commands import get_donate
from src.Sociocracy import SociocracyBot

class ConsentView(discord.ui.View):
    """
    A view which allows the user to consent or withdraw consent via buttons.
    """

    def __init__(self, * args, initial_text: str,  ** kwargs):
        super().__init__(* args, timeout=None, ** kwargs)

        self.uuid = uuid.uuid4()
        self.initial_text = initial_text

        self.consents: dict[int, str] = {}

        consent_button = discord.ui.Button(label='Consent', style=discord.ButtonStyle.green)
        consent_button.callback = self.add_consent
        self.add_item(consent_button)

        withdraw_consent_button = discord.ui.Button(label='Withdraw Consent', style=discord.ButtonStyle.red)
        withdraw_consent_button.callback = self.withdraw_consent
        self.add_item(withdraw_consent_button)

    async def add_consent(self, interaction: discord.Interaction):
        print(f"Add consent: {interaction.user.id}")
        if interaction.user.id in self.consents:
            await interaction.response.send_message("You have already consented", ephemeral=True)
        else:
            self.consents[interaction.user.id] = interaction.user.mention
            await interaction.response.edit_message(content=self.initial_text + '\n'.join(sorted(self.consents.values())))
            # await sociocracy.consent_added(interaction.user, self.uuid)

    async def withdraw_consent(self, interaction: discord.Interaction):
        print(f"Withdraw consent: {interaction.user.id}")
        if interaction.user.id in self.consents:
            del self.consents[interaction.user.id]
            await interaction.response.edit_message(content=self.initial_text + '\n'.join(sorted(self.consents.values())))
        else:
            await interaction.response.send_message("You have not consented so cannot withdraw", ephemeral=True)

intents = discord.Intents.default()
intents.message_content = True

sociocracy = SociocracyBot(intents=intents)

logger = get_logger()

def error_responder_decorator(command: Callable):
    @functools.wraps(command)
    async def wrapper(ctx: discord.ApplicationContext, *args, **kwargs):
        try:
            return await command(* args, ctx=ctx, ** kwargs)
        except BotError as e:
            logger.error(e, exc_info=True)
            await ctx.respond(f'Error: {str(e)}')
        except Exception as e:
            logger.error(e, exc_info=True)
            await ctx.respond(f'An error was encountered. Sorry!')

            send_email(str(e))

    return wrapper

def command_logging_decorator(command: Callable):

    @functools.wraps(command)
    async def wrapper(ctx: Union[discord.ApplicationContext, discord.AutocompleteContext], * args, ** kwargs):
        
        if isinstance(ctx, discord.ApplicationContext):
            guild_id = ctx.guild_id
            guild_name = ctx.guild.name
            user_name = ctx.user.name
        elif isinstance(ctx, discord.AutocompleteContext):
            guild_id = ctx.interaction.guild_id
            guild_name = ctx.interaction.guild.name
            user_name = ctx.interaction.user.name
        else:
            guild_id = '[Unknown Guild ID]'
            guild_name = '[Unknown Guild Name]'
            user_name = '[Unknown User]'

        log_message = f'Command {command.__name__} called in Guild {guild_id} ("{guild_name}") by {user_name} with args {args} and kwargs {kwargs}'[:3000]
        logger.info(log_message)

        return await command(*args, ctx=ctx, **kwargs)

    return wrapper

@sociocracy.slash_command(name='donate', description='Get a link to donate to me as a thank you.')
# This command isn't logged because that would feel creepy
@error_responder_decorator
async def donate_command(
    ctx: discord.ApplicationContext,
):
    message = get_donate()

    await ctx.respond(message)

@sociocracy.slash_command(name='ask_for_consent', description='Creates a view where you can ask for consent.')
@command_logging_decorator
@error_responder_decorator
async def ask_for_consent_command(
    ctx: discord.ApplicationContext,
    topic: discord.Option(str, description='What are we consenting to?', required=True),
):

    initial_text = f'{ctx.user.mention} is looking for consent on:\n{topic}\n\n{underline("Consenting Users:")}\n\n'
    view = ConsentView(initial_text=initial_text)

    await ctx.respond(initial_text, view=view)

@sociocracy.event
async def on_ready():
    logger.info(f'We have logged in as {sociocracy.user}', stack_info=False)

def send_email(message: str):
    response = requests.post(
        url=F'https://api.mailgun.net/v3/{os.environ["MAILGUN_SANDBOX_DOMAIN_NAME"]}/messages',
        auth=('api', os.environ['MAILGUN_API_KEY']),
        data={
            'from': f'sociocracy <mailgun@{os.environ["MAILGUN_SANDBOX_DOMAIN_NAME"]}>',
            'to': os.environ['DEBUG_EMAIL'],
            'subject': 'sociocracy Error',
            'text': message
        }
    )

    response.raise_for_status()

    return response.json()

def main():
    with open('credentials_sociocracy.json', 'r') as f:
        token = json.load(f)['token']

    dotenv.load_dotenv()

    atexit.register(send_email, message='Sociocracy has stopped running.')

    sociocracy.run(token=token)

    for guild in sociocracy.guilds:
        print(guild.name)

if __name__ == '__main__':
    main()