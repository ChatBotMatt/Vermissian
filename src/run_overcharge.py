import discord
from discord.ext.pages import Page, Paginator

import requests
import dotenv

import json
import random
import os
import glob
import functools
import atexit
from typing import Callable, Union, Literal

from src.Roll import Roll
from src.utils.format import bold, underline, code
from src.utils.logger import get_logger
from src.utils.exceptions import BotError, NoCharacterError, NoGameError, UnknownSystemError
from src.overcharge.Overcharge import Overcharge
from src.overcharge.DieGame import DieGame
from src.commands import get_privacy_policy, get_donate, get_commands_page_content, help_roll, get_character_list
from src.overcharge.commands import get_credits, get_legal, get_about, get_getting_started_page_content, \
    get_debugging_page_content, get_ability, link, unlink, add_character, log_suggestion, simple_roll, get_changelog, \
    roll_action

intents = discord.Intents.default()
intents.message_content = True

overcharge = Overcharge(intents=intents)

random.seed(20) # TODO Temporary for testing purposes

logger = get_logger()

# TODO Move these somewhere common, at least those that aren't bot-specific
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
            await ctx.respond(f'An error was encountered. Please try the debugging steps in {code("/help")}. Sorry!')

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

def guild_required_decorator(command: Callable):

    @functools.wraps(command)
    async def wrapper(ctx: discord.ApplicationContext, * args, ** kwargs):
        if not ctx.guild_id in overcharge.games:
            raise NoGameError()

        return await command(*args, ctx=ctx, **kwargs)

    return wrapper

def character_required_decorator(command: Callable):

    @functools.wraps(command)
    @guild_required_decorator
    async def wrapper(ctx: discord.ApplicationContext, * args, ** kwargs):
        if not ctx.user.name.lower() in overcharge.games[ctx.guild_id].character_sheets:
            raise NoCharacterError(username=ctx.user.name)

        return await command(*args, ctx=ctx, **kwargs)

    return wrapper

@overcharge.slash_command(name='credits', description='Get the credits')
@command_logging_decorator
@error_responder_decorator
async def credits_command(
    ctx: discord.ApplicationContext,
):
    message = get_credits()

    await ctx.respond(message, ephemeral=True)

@overcharge.slash_command(name='about', description='Get info about the bot.')
@command_logging_decorator
@error_responder_decorator
async def about_command(
    ctx: discord.ApplicationContext,
):
    message = get_about()

    await ctx.respond(message, ephemeral=True)

@overcharge.slash_command(name='legal', description='Get the legal information.')
@command_logging_decorator
@error_responder_decorator
async def legal_command(
    ctx: discord.ApplicationContext,
):
    message = get_legal()

    await ctx.respond(message)

@overcharge.slash_command(name='donate', description='Get a link to donate to me as a thank you.')
# This command isn't logged because that would feel creepy
@error_responder_decorator
async def donate_command(
    ctx: discord.ApplicationContext,
):
    message = get_donate()

    await ctx.respond(message)

@overcharge.slash_command(name='suggest', description='Have a suggestion to improve the bot? Let me know!')
@command_logging_decorator
@error_responder_decorator
async def suggest_command(
    ctx: discord.ApplicationContext,
    suggestion: str,
):
    response = log_suggestion(ctx.user.name, suggestion)

    await ctx.respond(response)

@overcharge.slash_command(name='privacy', description='Describes what happens to your data when using the bot (nothing bad).')
@command_logging_decorator
@error_responder_decorator
async def privacy_policy_command(
    ctx: discord.ApplicationContext,
):
    message = get_privacy_policy()

    await ctx.respond(message)

@overcharge.slash_command(name='help', description='Provides help text.')
@command_logging_decorator
@error_responder_decorator
async def help_command(
    ctx: discord.ApplicationContext
):
    raw_pages = [
        get_getting_started_page_content(),
        get_commands_page_content(overcharge.walk_application_commands()),
        get_debugging_page_content()
    ]

    headers = [
        raw_page[0] for raw_page in raw_pages
    ]

    pages = []

    for page_index, (page_header, raw_page_content) in enumerate(raw_pages):
        page_content = f'{bold(underline(page_header))}\n{raw_page_content}'

        if page_index > 0:
            page_content += f'\n\nPrevious: {headers[page_index - 1]}'

        if page_index < len(raw_pages) - 1:
            page_content += f'\n\nNext: {bold(headers[page_index + 1])}'

        pages.append(Page(content=page_content, embeds=[]))

    paginator = Paginator(pages)

    await paginator.respond(ctx.interaction, ephemeral=True)

@overcharge.slash_command(name='list', description='Lists existing characters and the character tracker they\'re connected to.')
@command_logging_decorator
@error_responder_decorator
@guild_required_decorator
async def list_characters_command(
    ctx: discord.ApplicationContext,
):
    game = overcharge.games[ctx.guild_id]

    message = get_character_list(game)

    await ctx.respond(message)

# TODO Allow optionally specifying system (or both), otherwise fallback to reading from server, otherwise both.
@overcharge.slash_command(name='ability', description='Describes a given ability')
@command_logging_decorator
@error_responder_decorator
async def ability_command(
    ctx: discord.ApplicationContext,
    ability: discord.Option(str, "The ability to describe"),
):
    message = get_ability(ability)

    await ctx.respond(message)

@overcharge.slash_command(name='add_character', description='Adds a character.')
@command_logging_decorator
@error_responder_decorator
@guild_required_decorator
async def add_character_command(
    ctx: discord.ApplicationContext,
    character_sheet_url: discord.Option(str, "The URL for your character sheet in the character tracker.")
):
    interaction = await ctx.respond('Adding character...')

    response = add_character(
        game=overcharge.games[ctx.guild_id],
        discord_username=ctx.user.name,
        discord_display_name=ctx.user.display_name,
        character_sheet_url=character_sheet_url
    )

    await interaction.edit(content=response)

@overcharge.slash_command(name='roll', description='Rolls dice, using the same syntax as the non-command rolling')
@command_logging_decorator
@error_responder_decorator
async def roll_command(
    ctx: Union[discord.ApplicationContext, discord.Message],
    rolls: discord.Option(str, 'The rolls to make, e.g. "3d6 + 1, 4d2 - 3, Difficulty 1 # This is an example roll."')
):
    try:
        if not rolls.lower().strip().startswith('roll'):
            rolls = 'Roll ' + rolls.strip()

        parsed_rolls, note = Roll.parse_roll(rolls)

        response = simple_roll(parsed_rolls, note)

        await ctx.respond(response)
    except BotError as e:
        await ctx.respond(str(e))
    except ValueError as v:
        logger.warning(v, exc_info=True)
        await ctx.respond(
            'Cannot understand that roll.\n\n' + help_roll(),
        )

@overcharge.slash_command(name='die_action', description='Rolls dice for an action.', guild_ids=[1218845257899446364])
@command_logging_decorator
@error_responder_decorator
# @character_required_decorator
async def die_action_command(
    ctx: Union[discord.ApplicationContext, discord.Message],
    stat: discord.Option(str, 'Stat to Use', choices=['str', 'dex', 'con', 'int', 'wis', 'cha'], required=True),
    include_class_die: bool,
    advantages: int = 0,
    disadvantages: int = 0,
    difficulty: int = 0,
):
    game = None # TODO overcharge.games[ctx.guild_id]
    username = ctx.user.name

    response = roll_action(game=game, username=username, stat=stat, include_class_die=include_class_die, advantages=advantages, disadvantages=disadvantages, difficulty=difficulty)

    await ctx.respond(response)

@overcharge.slash_command(name='help_roll', description='Provides help text for rolling.')
@command_logging_decorator
@error_responder_decorator
async def help_roll_command(ctx: discord.ApplicationContext):
    raw_pages = help_roll()

    headers = [
        raw_page[0] for raw_page in raw_pages
    ]

    pages = []

    for page_index, (page_header, raw_page_content) in enumerate(raw_pages):
        page_content = f'{bold(underline(page_header))}\n\n{raw_page_content}'

        if page_index > 0:
            page_content += f'\n\nPrevious: {headers[page_index - 1]}'

        if page_index < len(raw_pages) - 1:
            page_content += f'\n\nNext: {bold(headers[page_index + 1])}'

        pages.append(Page(content=page_content, embeds=[]))

    paginator = Paginator(pages)

    await paginator.respond(ctx.interaction, ephemeral=True)

@overcharge.slash_command(name='unlink', description='Unlinks game information from the current server, undoing the last /link')
@command_logging_decorator
@error_responder_decorator
async def unlink_command(
    ctx: discord.ApplicationContext,
):
    response = unlink(overcharge, ctx.guild_id)

    await ctx.respond(response)

@overcharge.slash_command(name='link', description='Links the bot to a specified game and character tracker. Adds characters it finds.')
@command_logging_decorator
@error_responder_decorator
async def link_command(
    ctx: discord.ApplicationContext,
    spreadsheet_url: str
):
    """
    Adds a guild to the bot and links it to a character tracker and game. Also links users to any characters it finds with matching usernames.

    :param ctx: The Discord application context to work within.

    :param spreadsheet_url: The spreadsheet URL for the character tracker.

    :param less_lethal: Whether the game uses the "less lethal" rules.

    :param system: The system used for the game.
    """

    interaction = await ctx.respond('Linking...')

    response = link(overcharge, ctx.guild_id, spreadsheet_url)

    await interaction.edit(content=response)

@overcharge.slash_command(name='changelog', description='Provides a changelog and version number.')
@command_logging_decorator
@error_responder_decorator
async def link_command(
    ctx: discord.ApplicationContext
):
    """
    Provides a changelog and version number.
    """

    changelog = get_changelog()

    await ctx.respond(changelog, ephemeral=True)

@overcharge.event
async def on_ready():
    logger.info(f'We have logged in as {overcharge.user}', stack_info=False)

    await overcharge.change_presence(activity=discord.Activity(type=discord.ActivityType.playing, name='Run /help to get started.'))

@overcharge.event
async def on_message(message: discord.Message):
    if message.author == overcharge.user:
        return

    if message.content.lower().strip().startswith('roll'):
        try:
            rolls, note = Roll.parse_roll(message.content)

            response = simple_roll(rolls, note)

            await message.reply(response)
        except BotError as v:
            logger.error(v)
            await message.reply(str(v))
        except Exception as e:
            logger.error(e)

def send_email(message: str):
    response = requests.post(
        url=F'https://api.mailgun.net/v3/{os.environ["MAILGUN_SANDBOX_DOMAIN_NAME"]}/messages',
        auth=('api', os.environ['MAILGUN_API_KEY']),
        data={
            'from': f'Vermissian <mailgun@{os.environ["MAILGUN_SANDBOX_DOMAIN_NAME"]}>',
            'to': os.environ['DEBUG_EMAIL'],
            'subject': 'Vermissian Error',
            'text': message
        }
    )

    response.raise_for_status()

    return response.json()

def main():
    with open('credentials_overcharge.json', 'r') as f:
        token = json.load(f)['token']

    dotenv.load_dotenv()

    atexit.register(send_email, message='Overcharge has stopped running.')

    if False: # TODO
        for server_data_dir in glob.glob(os.path.join('servers', '*')):
            guild_id = int(server_data_dir.split(os.sep)[1])

            try:
                game = DieGame.load(guild_id)

                overcharge.add_game(game=game)

                logger.info(f'Loaded {game}', stack_info=False)
            except FileNotFoundError as f:
                logger.error(f, exc_info=True)
                continue
            except UnknownSystemError as u:
                logger.debug(u)
                continue

    overcharge.run(token=token)

if __name__ == '__main__':
    main()