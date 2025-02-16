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
from typing import Callable, Union

from src.utils.format import bold, underline, code
from src.utils.logger import get_logger
from src.utils.exceptions import BotError, NoGameError, UnknownSystemError
from src.ghost_detector.GhostDetector import GhostDetector
from src.ghost_detector.GhostGame import GhostGame
from src.commands import get_privacy_policy, get_donate, get_commands_page_content, help_roll, should_respond
from src.vermissian.commands import simple_roll # TODO
from src.Roll import Roll
from src.ghost_detector.commands import get_credits, get_legal, get_about, link, unlink, log_suggestion, get_changelog, \
    draw_question_card, draw_fate_card, shuffle, draw_card

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

logger = get_logger()

ghost_detector = GhostDetector(intents=intents)

random.seed(666) # TODO Temporary for testing purposes

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
        if not ctx.guild_id in ghost_detector.games:
            raise NoGameError(msg=f'You need to set up a "Get Out, Run!" game before you can do this. Use {code("/explore")} to do so.')

        return await command(*args, ctx=ctx, **kwargs)

    return wrapper

@ghost_detector.slash_command(name='credits', description='Get the credits', guild_ids=[1218845257899446364, 1253037821040525342, 1193578278175375432, 1277727007890866196])
@command_logging_decorator
@error_responder_decorator
async def credits_command(
    ctx: discord.ApplicationContext,
):
    message = get_credits()

    await ctx.respond(message, ephemeral=True)

@ghost_detector.slash_command(name='about', description='Get info about the bot.', guild_ids=[1218845257899446364, 1253037821040525342, 1193578278175375432, 1277727007890866196])
@command_logging_decorator
@error_responder_decorator
async def about_command(
    ctx: discord.ApplicationContext,
):
    message = get_about()

    await ctx.respond(message, ephemeral=True)

@ghost_detector.slash_command(name='legal', description='Get the legal information.', guild_ids=[1218845257899446364, 1253037821040525342, 1193578278175375432, 1277727007890866196])
@command_logging_decorator
@error_responder_decorator
async def legal_command(
    ctx: discord.ApplicationContext,
):
    message = get_legal()

    await ctx.respond(message)

@ghost_detector.slash_command(name='donate', description='Get a link to donate to me as a thank you.', guild_ids=[1218845257899446364, 1253037821040525342, 1193578278175375432, 1277727007890866196])
# This command isn't logged because that would feel creepy
@error_responder_decorator
async def donate_command(
    ctx: discord.ApplicationContext,
):
    message = get_donate()

    await ctx.respond(message)

@ghost_detector.slash_command(name='suggest', description='Have a suggestion to improve the bot? Let me know!', guild_ids=[1218845257899446364, 1253037821040525342, 1193578278175375432, 1277727007890866196])
@command_logging_decorator
@error_responder_decorator
async def suggest_command(
    ctx: discord.ApplicationContext,
    suggestion: str,
):
    response = log_suggestion(ctx.user.name, suggestion)

    await ctx.respond(response)

@ghost_detector.slash_command(name='privacy', description='Describes what happens to your data when using the bot (nothing bad).', guild_ids=[1218845257899446364, 1253037821040525342, 1193578278175375432, 1277727007890866196])
@command_logging_decorator
@error_responder_decorator
async def privacy_policy_command(
    ctx: discord.ApplicationContext,
):
    message = get_privacy_policy()

    await ctx.respond(message)

@ghost_detector.slash_command(name='help', description='Provides help text.', guild_ids=[1218845257899446364, 1253037821040525342, 1193578278175375432, 1277727007890866196])
@command_logging_decorator
@error_responder_decorator
async def help_command(
    ctx: discord.ApplicationContext
): # TODO Prioritise "functional" commands at the top and maybe add a divider too.
    # TODO Duplicates in the list?
    raw_pages = [
        get_commands_page_content(ghost_detector.walk_application_commands()),
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

        if len(page_content) > 2000:
            pages.append(Page(content=page_content[:2000], embeds=[])) # TODO Very hacky
            pages.append(Page(content=page_content[2000:], embeds=[]))
        else:
            pages.append(Page(content=page_content, embeds=[]))

    paginator = Paginator(pages)

    await paginator.respond(ctx.interaction, ephemeral=True)

@ghost_detector.slash_command(name='get_out', description='Ends the "Get Out, Run!" game in the server leaving it free for other games.', guild_ids=[1218845257899446364, 1253037821040525342, 1193578278175375432, 1277727007890866196])
@command_logging_decorator
@error_responder_decorator
async def get_out_command(
    ctx: discord.ApplicationContext,
):
    response = unlink(ghost_detector, ctx.guild_id)

    await ctx.respond(response)

@ghost_detector.slash_command(name='draw_card', description='Draws a card and then shuffles it back into the deck.', guild_ids=[1218845257899446364, 1253037821040525342, 1193578278175375432, 1277727007890866196])
@command_logging_decorator
@error_responder_decorator
async def draw_card_command(
    ctx: discord.ApplicationContext,
):
    # TODO Track rounds and read them out alongside? Counting down
    response = draw_card()

    await ctx.respond(response)

@ghost_detector.slash_command(name='draw_question_card', description='Draws a question card. Should be done once per round.', guild_ids=[1218845257899446364, 1253037821040525342, 1193578278175375432, 1277727007890866196])
@command_logging_decorator
@error_responder_decorator
@guild_required_decorator
async def draw_question_card_command(
    ctx: discord.ApplicationContext,
):
    game = ghost_detector.games[ctx.guild_id]

    # TODO Track rounds and read them out alongside? Counting down
    response = draw_question_card(game)

    await ctx.respond(response)

@ghost_detector.slash_command(name='draw_fate_card', description='Draws a fate card. Should be done once per player at the end of the game.', guild_ids=[1218845257899446364, 1253037821040525342, 1193578278175375432, 1277727007890866196])
@command_logging_decorator
@error_responder_decorator
@guild_required_decorator
async def draw_fate_card_command(
    ctx: discord.ApplicationContext,
):
    game = ghost_detector.games[ctx.guild_id]

    response = draw_fate_card(game)

    await ctx.respond(response)

@ghost_detector.slash_command(name='shuffle', description='Reshuffles all cards into the deck.', guild_ids=[1218845257899446364, 1253037821040525342, 1193578278175375432, 1277727007890866196])
@command_logging_decorator
@error_responder_decorator
@guild_required_decorator
async def shuffle_command(
    ctx: discord.ApplicationContext,
):
    game = ghost_detector.games[ctx.guild_id]

    response = shuffle(game)

    await ctx.respond(response)

@ghost_detector.slash_command(name='explore', description='Starts a "Get Out, Run!" game in the server.', guild_ids=[1218845257899446364, 1253037821040525342, 1193578278175375432, 1277727007890866196])
@command_logging_decorator
@error_responder_decorator
async def explore_command(
    ctx: discord.ApplicationContext,
):
    response = link(ghost_detector, ctx.guild_id)

    await ctx.respond(response)

@ghost_detector.slash_command(name='changelog', description='Provides a changelog and version number.', guild_ids=[1218845257899446364, 1253037821040525342, 1193578278175375432, 1277727007890866196])
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

@ghost_detector.event
async def on_ready():
    logger.info(f'We have logged in as {ghost_detector.user}', stack_info=False)

    await ghost_detector.change_presence(activity=discord.Activity(type=discord.ActivityType.playing, name='Run /help to get started.'))

def send_email(message: str):
    response = requests.post(
        url=F'https://api.mailgun.net/v3/{os.environ["MAILGUN_SANDBOX_DOMAIN_NAME"]}/messages',
        auth=('api', os.environ['MAILGUN_API_KEY']),
        data={
            'from': f'Ghost Detector <mailgun@{os.environ["MAILGUN_SANDBOX_DOMAIN_NAME"]}>',
            'to': os.environ['DEBUG_EMAIL'],
            'subject': 'Ghost Detector Error',
            'text': message
        }
    )

    response.raise_for_status()

    return response.json()


@ghost_detector.slash_command(name='roll', description='Rolls dice, using the same syntax as the non-command rolling', guild_ids=[1277727007890866196])
@command_logging_decorator
@error_responder_decorator
async def roll_command(
    ctx: Union[discord.ApplicationContext, discord.Message],
    rolls: discord.Option(str, 'The rolls to make, e.g. "3d6 + 1, 4d2 - 3, Drop 1 # This is an example roll."')
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
            f'Cannot understand that roll.\n\nPlease use {code("/help_roll")} to see guidance on valid rolls.',
        )

@ghost_detector.slash_command(name='help_roll', description='Provides help text for rolling.', guild_ids=[1277727007890866196])
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


@ghost_detector.event
async def on_message(message: discord.Message):
    if message.author == ghost_detector.user:
        return

    if message.content.lower().strip().startswith('roll') and should_respond('Ghost Detector', message.channel.members):
        try:
            rolls, note = Roll.parse_roll(message.content)

            response = simple_roll(rolls, note)

            await message.reply(response)
        except BotError as v:
            logger.error(v)
            await message.reply(str(v))
        except Exception as e:
            logger.error(e)


def main():
    with open('credentials_ghost.json', 'r') as f:
        token = json.load(f)['token']

    dotenv.load_dotenv()

    atexit.register(send_email, message='Ghost Detector has stopped running.')

    for server_data_dir in glob.glob(os.path.join('servers', '*')):
        guild_id = int(server_data_dir.split(os.sep)[1])

        try:
            game = GhostGame.load(guild_id)

            ghost_detector.add_game(game=game)

            logger.info(f'Loaded {game}', stack_info=False)
        except FileNotFoundError as f:
            logger.error(f, exc_info=True)
            continue
        except UnknownSystemError as u:
            logger.debug(u)
            continue

    ghost_detector.run(token=token)

if __name__ == '__main__':
    main()