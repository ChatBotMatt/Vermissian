import string

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
from string import Template, punctuation, whitespace
import re
from typing import Callable, Union, Set, Dict


from src.System import System
from src.Roll import Roll, Cut
from src.utils.format import bold, underline, code, bullet, strikethrough
from src.utils.logger import get_logger
from src.utils.exceptions import BotError, NoCharacterError, NoGameError, UnknownSystemError
from src.vermissian.Vermissian import Vermissian
from src.vermissian.ResistanceGame import ResistanceGame, HeartGame
from src.vermissian.ResistanceCharacterSheet import SpireCharacter, SpireSkill, SpireDomain, HeartSkill, HeartDomain
from src.commands import get_privacy_policy, get_donate, get_commands_page_content, get_character_list, help_roll, should_respond
from src.vermissian.commands import get_credits, get_legal, get_about, get_getting_started_page_content, \
    get_debugging_page_content, get_tag, get_ability, get_delve_draw, link, unlink, spire_fallout, roll_spire_action, \
    heart_fallout, roll_heart_action, add_character, log_suggestion, simple_roll, get_changelog, roll_circulation, NEWSPAPERS
from src.goblin.commands import roll as goblin_roll # TODO

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

vermissian = Vermissian(intents=intents)

random.seed(7) # TODO Temporary for testing purposes

logger = get_logger()

spire_skills = [skill.value for skill in SpireSkill]
spire_domains = [domain.value for domain in SpireDomain]

heart_skills = [skill.value for skill in HeartSkill]
heart_domains = [domain.value for domain in HeartDomain]

heart_difficulties = list(HeartGame.DIFFICULTIES.keys())

newspapers = list(NEWSPAPERS.keys())

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
        if not ctx.guild_id in vermissian.games:
            raise NoGameError()

        return await command(*args, ctx=ctx, **kwargs)

    return wrapper

def character_required_decorator(command: Callable):

    @functools.wraps(command)
    @guild_required_decorator
    async def wrapper(ctx: discord.ApplicationContext, * args, ** kwargs):
        if not ctx.user.name.lower() in vermissian.games[ctx.guild_id].character_sheets:
            raise NoCharacterError(username=ctx.user.name)

        return await command(*args, ctx=ctx, **kwargs)

    return wrapper

@vermissian.slash_command(name='credits', description='Get the credits')
@command_logging_decorator
@error_responder_decorator
async def credits_command(
    ctx: discord.ApplicationContext,
):
    message = get_credits()

    await ctx.respond(message, ephemeral=True)

@vermissian.slash_command(name='about', description='Get info about the bot.')
@command_logging_decorator
@error_responder_decorator
async def about_command(
    ctx: discord.ApplicationContext,
):
    message = get_about()

    await ctx.respond(message, ephemeral=True)

@vermissian.slash_command(name='legal', description='Get the legal information.')
@command_logging_decorator
@error_responder_decorator
async def legal_command(
    ctx: discord.ApplicationContext,
):
    message = get_legal()

    await ctx.respond(message)

@vermissian.slash_command(name='donate', description='Get a link to donate to me as a thank you.')
# This command isn't logged because that would feel creepy
@error_responder_decorator
async def donate_command(
    ctx: discord.ApplicationContext,
):
    message = get_donate()

    await ctx.respond(message)

@vermissian.slash_command(name='suggest', description='Have a suggestion to improve the bot? Let me know!')
@command_logging_decorator
@error_responder_decorator
async def suggest_command(
    ctx: discord.ApplicationContext,
    suggestion: str,
):
    response = log_suggestion(ctx.user.name, suggestion)

    await ctx.respond(response, ephemeral=True)

@vermissian.slash_command(name='privacy', description='Describes what happens to your data when using the bot (nothing bad).')
@command_logging_decorator
@error_responder_decorator
async def privacy_policy_command(
    ctx: discord.ApplicationContext,
):
    message = get_privacy_policy()

    await ctx.respond(message)

@vermissian.slash_command(name='help', description='Provides help text.')
@command_logging_decorator
@error_responder_decorator
async def help_command(
    ctx: discord.ApplicationContext
):
    raw_pages = [
        get_getting_started_page_content(),
        get_commands_page_content(vermissian.walk_application_commands()),
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

@vermissian.slash_command(name='list', description='Lists existing characters and the character tracker they\'re connected to.')
@command_logging_decorator
@error_responder_decorator
@guild_required_decorator
async def list_characters_command(
    ctx: discord.ApplicationContext,
):
    game = vermissian.games[ctx.guild_id]

    message = get_character_list(game)

    await ctx.respond(message)

# TODO Allow optionally specifying system (or both), otherwise fallback to reading from server, otherwise both.
@vermissian.slash_command(name='tag', description='Describes a given resource or equipment tag')
@command_logging_decorator
@error_responder_decorator
async def get_tag_command(
    ctx: discord.ApplicationContext,
    tag: discord.Option(str, "The tag to describe"),
):
    game = vermissian.games.get(ctx.guild_id)
    system = game.system if game is not None else None

    message = get_tag(tag, system)

    await ctx.respond(message)

# TODO Allow optionally specifying system (or both), otherwise fallback to reading from server, otherwise both.
@vermissian.slash_command(name='ability', description='Describes a given ability')
@command_logging_decorator
@error_responder_decorator
async def ability_command(
    ctx: discord.ApplicationContext,
    ability: discord.Option(str, "The ability to describe"),
):
    game = vermissian.games.get(ctx.guild_id)
    system = game.system if game is not None else None

    message = get_ability(ability, system)

    await ctx.respond(message)

@vermissian.slash_command(name='delve_draw', description='Does an ichor-drowned delve-draw')
@command_logging_decorator
@error_responder_decorator
async def delve_draw_command(
    ctx: discord.ApplicationContext,
    expand_draws: discord.Option(bool, "Whether or not to expand the draws into specific results rather than just titles") = False,
    five_card_draw: discord.Option(bool, "Whether or not to additionally draw cards to flavour the positive and negative aspects") = False,
    allow_duplicates: discord.Option(bool, "Whether or not to allow duplicate cards in the same draw") = False
):
    response = get_delve_draw(expand_draws, five_card_draw, allow_duplicates)

    await ctx.respond(response, ephemeral=True)

@vermissian.slash_command(name='add_character', description='Adds a character.')
@command_logging_decorator
@error_responder_decorator
@guild_required_decorator
async def add_character_command(
    ctx: discord.ApplicationContext,
    character_sheet_url: discord.Option(str, "The URL for your character sheet in the character tracker.")
):
    interaction = await ctx.respond('Adding character...')

    response = add_character(
        game=vermissian.games[ctx.guild_id],
        discord_username=ctx.user.name,
        discord_display_name=ctx.user.display_name,
        character_sheet_url=character_sheet_url
    )

    await interaction.edit(content=response)

@vermissian.slash_command(name='spire_action', description='Rolls dice for taking an action in Spire')
@command_logging_decorator
@error_responder_decorator
@character_required_decorator
async def roll_spire_action_command(
    ctx: discord.ApplicationContext,
    skill: discord.Option(str, 'Relevant Skill', choices=spire_skills, required=True),
    domain: discord.Option(str, 'Relevant Domain', choices=spire_domains, required=True),
    mastery: discord.Option(bool, 'Has mastery?', default=False),
    num_helpers: discord.Option(int, 'How many other players are helping? (Requires relevant skill or domain, shares stress)', default=0, min=0),
    difficulty: discord.Option(int, "Difficulty of the action", default=0, min_value=0, max_value=2)
):
    response, view = roll_spire_action(
        game=vermissian.games[ctx.guild_id],
        username=ctx.user.name,
        skill=skill,
        domain=domain,
        mastery=mastery,
        num_helpers=num_helpers,
        difficulty=difficulty
    )

    await ctx.respond(response, view=view)

@vermissian.slash_command(name='heart_action', description='Rolls dice for taking an action in Heart')
@command_logging_decorator
@error_responder_decorator
@character_required_decorator
async def roll_heart_action_command(
    ctx: discord.ApplicationContext,
    skill: discord.Option(str, 'Relevant Skill', choices=heart_skills, required=True),
    domain: discord.Option(str, 'Relevant Domain', choices=heart_domains, required=True),
    mastery: discord.Option(bool, 'Has mastery?', default=False),
    num_helpers: discord.Option(int, 'How many other players are helping? (Requires relevant skill or domain, shares stress)', default=0, min=0),
    difficulty: discord.Option(int, "Difficulty of the action", default=0, min_value=0, max_value=2)
):
    response, view = roll_heart_action(
        game=vermissian.games[ctx.guild_id],
        username=ctx.user.name,
        skill=skill,
        domain=domain,
        mastery=mastery,
        num_helpers=num_helpers,
        difficulty=difficulty
    )

    await ctx.respond(response, view=view)

@vermissian.slash_command(name='spire_fallout', description='Rolls dice for a Spire fallout check')
@command_logging_decorator
@error_responder_decorator
@character_required_decorator
async def spire_fallout_command( # TODO Nice to not always have to specify resistance track, but less lethal interferes there
    ctx: discord.ApplicationContext,
    resistance: discord.Option(str, 'Resistance track that triggered this', choices=SpireCharacter.RESISTANCES, default=None)
):
    response = spire_fallout(
        vermissian.games[ctx.guild_id],
        ctx.user.name,
        resistance
    )

    await ctx.respond(response)

@vermissian.slash_command(name='heart_fallout', description='Rolls dice for a Heart fallout check')
@command_logging_decorator
@error_responder_decorator
@character_required_decorator
async def heart_fallout_command(
    ctx: discord.ApplicationContext
):
    response = heart_fallout(
        vermissian.games[ctx.guild_id],
        ctx.user.name
    )

    await ctx.respond(response)


@vermissian.slash_command(name='circulation', description='Rolls dice for newspaper circulation in the Sulphurous Presses scenario')
@command_logging_decorator
@error_responder_decorator
async def roll_circulation_command(
    ctx: discord.ApplicationContext,
    fits_domain: discord.Option(bool, 'Does this fit the target domain?', required=True),
    fits_stance: discord.Option(bool, 'Does this match your editorial stance?', required=True),
    in_local_area: discord.Option(bool, 'Is this story taking place in the paper\'s local area?', required=True),
    target_paper: discord.Option(str, description='The newspaper you\'re competing with. Determines initial difficulty and stress they inflict.', choices=newspapers),
    additional_difficulty: discord.Option(int, "Any difficulty stemming from fallout or other factors", default=0, min_value=0)
):
    response, view = roll_circulation(
        fits_domain=fits_domain,
        fits_stance=fits_stance,
        within_local_area=in_local_area,
        target=target_paper,
        additional_difficulty=additional_difficulty
    )

    await ctx.respond(response, view=view)


@vermissian.slash_command(name='roll', description='Rolls dice, using the same syntax as the non-command rolling')
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

@vermissian.slash_command(name='goblin_roll', description='Rolls dice for an action', guild_ids=[1193578278175375432])
@command_logging_decorator
@error_responder_decorator
async def goblin_roll_command(
    ctx: Union[discord.ApplicationContext, discord.Message],
    num_bonus_dice: discord.Option(int, "The number of additional d6 to roll."),
    bonus: discord.Option(bool, "Do you have a bonus +1?", default=False),
    penalty: discord.Option(bool, "Do you have a penalty -1?", default=False),
):

    bonus_num = 1 if bonus else 0
    penalty_num = 1 if penalty else 0
    rolls = goblin_roll(num_bonus_dice, bonus_num, penalty_num)

    OUTCOME_MAP = {
        0: 'Death! Describe the comical way in which your Goblin dies',
        1: 'Injury! Lose a HP, if this would kill you describe the comical way in which your Goblin dies',
        2: 'Injury! Lose a HP, if this would kill you describe the comical way in which your Goblin dies',
        3: 'Something bad - a setback, the next goblin to act gets -1 to their next roll',
        4: 'Something good - a lucky break - the next goblin gets +1 to their next roll',
        5: 'Victory - Succeed at your task, often in some barely noticeable way - describe what happens and subtract 1 from the current challenge\'s difficulty rating. If it hits 0 you complete that challenge.',
        6: 'Victory - Succeed at your task, often in some barely noticeable way - describe what happens and subtract 1 from the current challenge\'s difficulty rating. If it hits 0 you complete that challenge.',
        7: 'Double Victory! - Succeed at your task fantastically - describe what happens and subtract 2 from the current challenge\'s difficulty rating. If it hits 0 you complete that challenge.'
    }

    outcomes = [f'Rolled {rolls}{" + " + str(bonus_num) if bonus_num > 0 else ""}{" - " + str(penalty_num) if penalty_num > 0 else ""}\n']

    modified_rolls = [roll + bonus_num - penalty_num for roll in rolls]

    for roll in modified_rolls:
        outcomes.append(f'* {bold(roll)} - {OUTCOME_MAP[roll]}')

    await ctx.respond('\n'.join(outcomes))

@vermissian.slash_command(name='help_roll', description='Provides help text for rolling.')
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

@vermissian.slash_command(name='unlink', description='Unlinks game information from the current server, undoing the last /link')
@command_logging_decorator
@error_responder_decorator
async def unlink_command(
    ctx: discord.ApplicationContext,
):
    response = unlink(vermissian, ctx.guild_id)

    await ctx.respond(response)

@vermissian.slash_command(name='link', description='Links the bot to a specified game and character tracker. Adds characters it finds.')
@command_logging_decorator
@error_responder_decorator
async def link_command(
    ctx: discord.ApplicationContext,
    spreadsheet_url: str,
    system: discord.Option(System, "System to use"),
    less_lethal: discord.Option(bool, "Whether or not to use less lethal fallout", default=False)
):
    """
    Adds a guild to the bot and links it to a character tracker and game. Also links users to any characters it finds with matching usernames.

    :param ctx: The Discord application context to work within.

    :param spreadsheet_url: The spreadsheet URL for the character tracker.

    :param less_lethal: Whether the game uses the "less lethal" rules.

    :param system: The system used for the game.
    """

    interaction = await ctx.respond('Linking...')

    response = link(vermissian, ctx.guild_id, system, spreadsheet_url, less_lethal)

    await interaction.edit(content=response)

@vermissian.slash_command(name='changelog', description='Provides a changelog and version number.')
@command_logging_decorator
@error_responder_decorator
async def changelog_command(
    ctx: discord.ApplicationContext
):
    """
    Provides a changelog and version number.
    """

    changelog = get_changelog()

    await ctx.respond(changelog, ephemeral=True)

@vermissian.event
async def on_ready():
    logger.info(f'We have logged in as {vermissian.user}', stack_info=False)

    await vermissian.change_presence(activity=discord.Activity(type=discord.ActivityType.playing, name='Run /help to get started.'))

@vermissian.event
async def on_message(message: discord.Message):
    if message.author == vermissian.user:
        return

    if message.content.lower().strip().startswith('roll') and should_respond('Vermissian', message.channel.members):
        try:
            rolls, note = Roll.parse_roll(message.content)

            response = simple_roll(rolls, note)

            if len(response) > 2000:
                await message.reply("Cannot compute such a large roll expression.")
            else:
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
    with open('credentials_vermissian.json', 'r') as f:
        token = json.load(f)['token']

    dotenv.load_dotenv()

    atexit.register(send_email, message='Vermissian has stopped running.')

    for server_data_dir in glob.glob(os.path.join('servers', '*')):
        guild_id = int(server_data_dir.split(os.sep)[1])

        try:
            game = ResistanceGame.load(guild_id)

            vermissian.add_game(game=game)

            logger.info(f'Loaded {game}', stack_info=False)
        except FileNotFoundError as f:
            logger.error(f, exc_info=True)
            continue
        except UnknownSystemError as u:
            logger.debug(u)
            continue

    vermissian.run(token=token)

if __name__ == '__main__':
    main()