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

from src.Roll import Roll
from src.utils.format import bold, underline, code
from src.utils.logger import get_logger
from src.utils.exceptions import BotError, NoCharacterError, NoGameError, UnknownSystemError
from src.astir.Astir import Astir
from src.astir.AstirGame import AstirGame
from src.astir.AstirCharacterSheet import AstirTrait
from src.astir.AstirMove import AstirMove
from src.commands import get_privacy_policy, get_donate, get_commands_page_content, get_character_list, help_roll, should_respond
from src.astir.commands import (
    get_credits, get_legal, get_about, get_getting_started_page_content, get_move, get_tag, get_debugging_page_content,
    roll_action, link, unlink, add_character, log_suggestion, simple_roll, get_changelog
)
from src.astir.utils import load_moves

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

astir = Astir(intents=intents)

random.seed(11) # TODO Temporary for testing purposes

logger = get_logger()

armour_astir_moves = load_moves()

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
        if not ctx.guild_id in astir.games:
            raise NoGameError()

        return await command(*args, ctx=ctx, **kwargs)

    return wrapper

def character_required_decorator(command: Callable):

    @functools.wraps(command)
    @guild_required_decorator
    async def wrapper(ctx: discord.ApplicationContext, * args, ** kwargs):
        if not ctx.user.name.lower() in astir.games[ctx.guild_id].character_sheets:
            raise NoCharacterError(username=ctx.user.name)

        return await command(*args, ctx=ctx, **kwargs)

    return wrapper

@astir.slash_command(name='credits', description='Get the credits')
@command_logging_decorator
@error_responder_decorator
async def credits_command(
    ctx: discord.ApplicationContext,
):
    message = get_credits()

    await ctx.respond(message, ephemeral=True)

@astir.slash_command(name='about', description='Get info about the bot.')
@command_logging_decorator
@error_responder_decorator
async def about_command(
    ctx: discord.ApplicationContext,
):
    message = get_about()

    await ctx.respond(message, ephemeral=True)

@astir.slash_command(name='legal', description='Get the legal information.')
@command_logging_decorator
@error_responder_decorator
async def legal_command(
    ctx: discord.ApplicationContext,
):
    message = get_legal()

    await ctx.respond(message)

@astir.slash_command(name='donate', description='Get a link to donate to me as a thank you.')
# This command isn't logged because that would feel creepy
@error_responder_decorator
async def donate_command(
    ctx: discord.ApplicationContext,
):
    message = get_donate()

    await ctx.respond(message)

@astir.slash_command(name='suggest', description='Have a suggestion to improve the bot? Let me know!')
@command_logging_decorator
@error_responder_decorator
async def suggest_command(
    ctx: discord.ApplicationContext,
    suggestion: str,
):
    response = log_suggestion(ctx.user.name, suggestion)

    await ctx.respond(response, ephemeral=True)

@astir.slash_command(name='privacy', description='Describes what happens to your data when using the bot (nothing bad).')
@command_logging_decorator
@error_responder_decorator
async def privacy_policy_command(
    ctx: discord.ApplicationContext,
):
    message = get_privacy_policy()

    await ctx.respond(message)

@astir.slash_command(name='help', description='Provides help text.')
@command_logging_decorator
@error_responder_decorator
async def help_command(
    ctx: discord.ApplicationContext
):
    raw_pages = [
        get_getting_started_page_content(),
        get_commands_page_content(astir.walk_application_commands()),
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

@astir.slash_command(name='list', description='Lists existing characters and the character tracker they\'re connected to.')
@command_logging_decorator
@error_responder_decorator
@guild_required_decorator
async def list_characters_command(
    ctx: discord.ApplicationContext,
):
    game = astir.games[ctx.guild_id]

    message = get_character_list(game)

    await ctx.respond(message)

@astir.slash_command(name='tag', description='Describes a given resource or equipment tag')
@command_logging_decorator
@error_responder_decorator
async def get_tag_command(
    ctx: discord.ApplicationContext,
    tag: discord.Option(str, "The tag to describe"),
):
    message = get_tag(tag)

    await ctx.respond(message)

@astir.slash_command(name='describe_move', description='Describes a given move')
@command_logging_decorator
@error_responder_decorator
async def describe_move_command(
    ctx: discord.ApplicationContext,
    move: discord.Option(str, "The move to describe"),
):

    message = get_move(move)

    if isinstance(message, Paginator):
        await message.respond(ctx.interaction)
    else:
        await ctx.respond(message)

@astir.slash_command(name='add_character', description='Adds a character.')
@command_logging_decorator
@error_responder_decorator
@guild_required_decorator
async def add_character_command(
    ctx: discord.ApplicationContext,
    character_sheet_url: discord.Option(str, "The URL for your character sheet in the character tracker.")
):
    interaction = await ctx.respond('Adding character...')

    response = add_character(
        game=astir.games[ctx.guild_id],
        discord_username=ctx.user.name,
        discord_display_name=ctx.user.display_name,
        character_sheet_url=character_sheet_url
    )

    await interaction.edit(content=response)

@astir.slash_command(name='action', description='Rolls dice for taking an action outside of moves')
@command_logging_decorator
@error_responder_decorator
@character_required_decorator
async def roll_action_command(
    ctx: discord.ApplicationContext,
    skill: discord.Option(str, 'Relevant Skill', choices=[trait.value for trait in AstirTrait if trait != AstirTrait.GRAVITY], required=True),
    confidence_desperation: discord.Option(str, choices=['Confidence', 'Desperation'], required=False), # TODO Enums
    num_advantages: discord.Option(int, 'How many advantages do you have?', required=True, default=0),
    num_disadvantages: discord.Option(int, 'How many disadvantages do you have?', required=True, default=0)
):
    confidence = False
    desperation = False

    if confidence_desperation:
        if confidence_desperation.title() == 'Confidence':
            confidence = True
        elif confidence_desperation.title() == 'Desperation':
            desperation = True

    response = roll_action(
        game=astir.games[ctx.guild_id],
        username=ctx.user.name,
        trait=skill,
        confidence=confidence,
        desperation=desperation,
        num_advantages=num_advantages,
        num_disadvantages=num_disadvantages
    )

    await ctx.respond(response)

# TODO Add move-specific ones, at least for the basics

@astir.slash_command(name='roll', description='Rolls dice, using the same syntax as the non-command rolling')
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

@astir.slash_command(name='weather_the_storm', description='Weather the Storm to do something safely under pressure')
@command_logging_decorator
@error_responder_decorator
@character_required_decorator
async def weather_the_storm_command(
    ctx: Union[discord.ApplicationContext, discord.Message],
    trait: discord.Option(str, choices=list(armour_astir_moves['basic']['weather the storm'].traits.keys()), description='Which trait are you using?'),
    num_advantages: discord.Option(int, description="How many advantages do you have?", default=0, required=False),
    num_disadvantages: discord.Option(int, description="How many disadvantages do you have?", default=0, required=False),
    confidence_desperation: discord.Option(str, choices=['Confidence', 'Desperation'], required=False) # TODO Enums
):
    confidence = False
    desperation = False

    if confidence_desperation:
        if confidence_desperation.title() == 'Confidence':
            confidence = True
        elif confidence_desperation.title() == 'Desperation':
            desperation = True

    response, total = roll_action(
        game=astir.games[ctx.guild_id],
        username=ctx.user.name,
        trait=trait,
        confidence=confidence,
        desperation=desperation,
        num_advantages=num_advantages,
        num_disadvantages=num_disadvantages
    )

    outcome = armour_astir_moves['basic']['weather the storm'].get_outcome(total)

    response += f'\n\n{bold(outcome)}'

    await ctx.respond(response)

@astir.slash_command(name='read_the_room', description=f'Read the Room with {AstirTrait.SENSE.value} to get insight on your situation')
@command_logging_decorator
@error_responder_decorator
@character_required_decorator
async def read_the_room_command(
    ctx: Union[discord.ApplicationContext, discord.Message],
    num_advantages: discord.Option(int, description="How many advantages do you have?", default=0, required=False),
    num_disadvantages: discord.Option(int, description="How many disadvantages do you have?", default=0, required=False),
    confidence_desperation: discord.Option(str, choices=['Confidence', 'Desperation'], required=False) # TODO Enums
):
    confidence = False
    desperation = False

    game = astir.games[ctx.guild_id]
    character = game.get_character(ctx.user.name)

    # TODO Eventually just check all their moves
    # TODO I think this is slowing things enough that interactions fail?
    #  Make it properly async maybe, to allow longer delays? Or ideally just more efficient.
    if 'field scout' in [move.lower() for move in character.get_all_moves() if isinstance(move, str)]:
        confidence_desperation = 'Confidence'

    if confidence_desperation:
        if confidence_desperation.title() == 'Confidence':
            confidence = True
        elif confidence_desperation.title() == 'Desperation':
            desperation = True

    response, total = roll_action(
        game=astir.games[ctx.guild_id],
        username=ctx.user.name,
        trait=AstirTrait.SENSE.value,
        confidence=confidence,
        desperation=desperation,
        num_advantages=num_advantages,
        num_disadvantages=num_disadvantages
    )

    outcome = armour_astir_moves['basic']['read the room'].get_outcome(total)

    response += f'\n\n{bold(outcome)}'

    await ctx.respond(response)

@astir.slash_command(name='dispel_uncertainties', description=f'Dispel Uncertainties with {AstirTrait.KNOW.value} by clarifying the unknown or answering a question')
@command_logging_decorator
@error_responder_decorator
@character_required_decorator
async def dispel_uncertainties_command(
    ctx: Union[discord.ApplicationContext, discord.Message],
    num_advantages: discord.Option(int, description="How many advantages do you have?", default=0, required=False),
    num_disadvantages: discord.Option(int, description="How many disadvantages do you have?", default=0, required=False),
    confidence_desperation: discord.Option(str, choices=['Confidence', 'Desperation'], required=False) # TODO Enums
):
    confidence = False
    desperation = False

    if confidence_desperation:
        if confidence_desperation.title() == 'Confidence':
            confidence = True
        elif confidence_desperation.title() == 'Desperation':
            desperation = True

    response, total = roll_action(
        game=astir.games[ctx.guild_id],
        username=ctx.user.name,
        trait=AstirTrait.KNOW.value,
        confidence=confidence,
        desperation=desperation,
        num_advantages=num_advantages,
        num_disadvantages=num_disadvantages
    )

    outcome = armour_astir_moves['basic']['dispel uncertainties'].get_outcome(total)

    response += f'\n\n{bold(outcome)}'

    await ctx.respond(response)

@astir.slash_command(name='help_or_hinder', description=f'Help or Hinder someone to influence their attempts to do something.')
@command_logging_decorator
@error_responder_decorator
@character_required_decorator
async def help_or_hinder_command(
    ctx: Union[discord.ApplicationContext, discord.Message],
    bonus: discord.Option(int, description='Add up to +3 based on circumstances (see move).', default=0, required=False),
    num_advantages: discord.Option(int, description="How many advantages do you have?", default=0, required=False),
    num_disadvantages: discord.Option(int, description="How many disadvantages do you have?", default=0, required=False),
    confidence_desperation: discord.Option(str, choices=['Confidence', 'Desperation'], required=False) # TODO Enums
):
    confidence = False
    desperation = False

    if confidence_desperation:
        if confidence_desperation.title() == 'Confidence':
            confidence = True
        elif confidence_desperation.title() == 'Desperation':
            desperation = True

    response, total = roll_action(
        game=astir.games[ctx.guild_id],
        username=ctx.user.name,
        trait=None,
        confidence=confidence,
        desperation=desperation,
        num_advantages=num_advantages,
        num_disadvantages=num_disadvantages,
        modifier=bonus
    )

    outcome = armour_astir_moves['basic']['help or hinder'].get_outcome(total)

    response += f'\n\n{bold(outcome)}'

    await ctx.respond(response)

@astir.slash_command(name='weave_magic', description=f'Weave Magic with {AstirTrait.CHANNEL.value} to do something taxing with your power')
@command_logging_decorator
@error_responder_decorator
@character_required_decorator
async def weave_magic_command(
    ctx: Union[discord.ApplicationContext, discord.Message],
    num_advantages: discord.Option(int, description="How many advantages do you have?", default=0, required=False),
    num_disadvantages: discord.Option(int, description="How many disadvantages do you have?", default=0, required=False),
    confidence_desperation: discord.Option(str, choices=['Confidence', 'Desperation'], required=False) # TODO Enums
):
    confidence = False
    desperation = False

    if confidence_desperation:
        if confidence_desperation.title() == 'Confidence':
            confidence = True
        elif confidence_desperation.title() == 'Desperation':
            desperation = True

    response, total = roll_action(
        game=astir.games[ctx.guild_id],
        username=ctx.user.name,
        trait=AstirTrait.CHANNEL.value, # This was +3 for Simon for some reason? Should be +2
        confidence=confidence,
        desperation=desperation,
        num_advantages=num_advantages,
        num_disadvantages=num_disadvantages
    )

    outcome = armour_astir_moves['basic']['weave magic'].get_outcome(total)

    response += f'\n\n{bold(outcome)}'

    await ctx.respond(response)

@astir.slash_command(name='cool_off', description=f'Cool Off to take a moment in safety / help someone else do so. Declare a risk you want to get rid of')
@command_logging_decorator
@error_responder_decorator
@character_required_decorator
async def cool_off_command(
    ctx: Union[discord.ApplicationContext, discord.Message],
    trait: discord.Option(str, choices=[trait.value for trait in AstirTrait if trait != AstirTrait.GRAVITY], description='Which trait are you using?'),
    num_advantages: discord.Option(int, description="How many advantages do you have?", default=0, required=False),
    num_disadvantages: discord.Option(int, description="How many disadvantages do you have?", default=0, required=False),
    confidence_desperation: discord.Option(str, choices=['Confidence', 'Desperation'], required=False) # TODO Enums
):
    confidence = False
    desperation = False

    if confidence_desperation:
        if confidence_desperation.title() == 'Confidence':
            confidence = True
        elif confidence_desperation.title() == 'Desperation':
            desperation = True

    response, total = roll_action(
        game=astir.games[ctx.guild_id],
        username=ctx.user.name,
        trait=trait,
        confidence=confidence,
        desperation=desperation,
        num_advantages=num_advantages,
        num_disadvantages=num_disadvantages
    )

    outcome = armour_astir_moves['basic']['cool off'].get_outcome(total)

    response += f'\n\n{bold(outcome)}'

    await ctx.respond(response)

@astir.slash_command(name='exchange_blows', description=f'Exchange Blows with a foe who can defend themselves, and advance a GRAVITY clock if you have one.')
@command_logging_decorator
@error_responder_decorator
@character_required_decorator
async def exchange_blows_command(
    ctx: Union[discord.ApplicationContext, discord.Message],
    trait: discord.Option(str, choices=[trait for trait in armour_astir_moves['basic']['exchange blows'].traits], description='Which trait are you using?'),
    num_advantages: discord.Option(int, description="How many advantages do you have?", default=0, required=False),
    num_disadvantages: discord.Option(int, description="How many disadvantages do you have?", default=0, required=False),
    confidence_desperation: discord.Option(str, choices=['Confidence', 'Desperation'], required=False) # TODO Enums
):
    confidence = False
    desperation = False

    if confidence_desperation:
        if confidence_desperation.title() == 'Confidence':
            confidence = True
        elif confidence_desperation.title() == 'Desperation':
            desperation = True

    response, total = roll_action(
        game=astir.games[ctx.guild_id],
        username=ctx.user.name,
        trait=trait,
        confidence=confidence,
        desperation=desperation,
        num_advantages=num_advantages,
        num_disadvantages=num_disadvantages
    )

    outcome = armour_astir_moves['basic']['exchange blows'].get_outcome(total)

    response += f'\n\n{bold(outcome)}'

    await ctx.respond(response)

@astir.slash_command(name='strike_decisively', description=f'Strike Decisively against someone defenceless.')
@command_logging_decorator
@error_responder_decorator
@character_required_decorator
async def strike_decisively_command(
    ctx: Union[discord.ApplicationContext, discord.Message],
    trait: discord.Option(str, choices=[trait for trait in armour_astir_moves['basic']['strike decisively'].traits], description='Which trait are you using?'),
    num_advantages: discord.Option(int, description="How many advantages do you have?", default=0, required=False),
    num_disadvantages: discord.Option(int, description="How many disadvantages do you have?", default=0, required=False),
    confidence_desperation: discord.Option(str, choices=['Confidence', 'Desperation'], required=False) # TODO Enums
):
    confidence = False
    desperation = False

    if confidence_desperation:
        if confidence_desperation.title() == 'Confidence':
            confidence = True
        elif confidence_desperation.title() == 'Desperation':
            desperation = True

    response, total = roll_action(
        game=astir.games[ctx.guild_id],
        username=ctx.user.name,
        trait=trait,
        confidence=confidence,
        desperation=desperation,
        num_advantages=num_advantages,
        num_disadvantages=num_disadvantages
    )

    outcome = armour_astir_moves['basic']['strike decisively'].get_outcome(total)

    response += f'\n\n{bold(outcome)}'

    response = response.replace('You succeed as above', 'You strike true. Director characters are killed, forced to retreat or otherwise removed as a threat as per the fiction. Player characters should Bite the Dust')

    await ctx.respond(response)

@astir.slash_command(name='bite_the_dust', description=f'Bite the Dust when caught defenceless or risking severe harm.')
@command_logging_decorator
@error_responder_decorator
@character_required_decorator
async def bite_the_dust_command(
    ctx: Union[discord.ApplicationContext, discord.Message],
    num_advantages: discord.Option(int, description="How many advantages do you have?", default=0, required=False),
    num_disadvantages: discord.Option(int, description="How many disadvantages do you have?", default=0, required=False),
    confidence_desperation: discord.Option(str, choices=['Confidence', 'Desperation'], required=False) # TODO Enums
):
    confidence = False
    desperation = False

    if confidence_desperation:
        if confidence_desperation.title() == 'Confidence':
            confidence = True
        elif confidence_desperation.title() == 'Desperation':
            desperation = True

    response, total = roll_action(
        game=astir.games[ctx.guild_id],
        username=ctx.user.name,
        trait=AstirTrait.DEFY.value,
        confidence=confidence,
        desperation=desperation,
        num_advantages=num_advantages,
        num_disadvantages=num_disadvantages
    )

    outcome = armour_astir_moves['basic']['bite the dust'].get_outcome(total)

    response += f'\n\n{bold(outcome)}'

    await ctx.respond(response)

@astir.slash_command(name='heat_up', description=f'Push your Astir to its limits to retry a roll.')
@command_logging_decorator
@error_responder_decorator
@character_required_decorator
async def heat_up_command(
    ctx: Union[discord.ApplicationContext, discord.Message],
):
    await describe_move_command(ctx=ctx, move='Heat Up')


@astir.slash_command(name='arcanist_prepare_rituals', description=f'Before every Sortie, you prepare a set of complex rituals to bolster your magical potential.')
@command_logging_decorator
@error_responder_decorator
@character_required_decorator
async def arcanist_prepare_rituals_command(
    ctx: Union[discord.ApplicationContext, discord.Message],
):
    await describe_move_command(ctx=ctx, move='Prepare Rituals')

@astir.slash_command(name='arcanist_tactical_illusions', description=f'Distract foes with magic')
@command_logging_decorator
@error_responder_decorator
@character_required_decorator
async def bite_the_dust_command(
    ctx: Union[discord.ApplicationContext, discord.Message],
    num_advantages: discord.Option(int, description="How many advantages do you have?", default=0, required=False),
    num_disadvantages: discord.Option(int, description="How many disadvantages do you have?", default=0, required=False),
    confidence_desperation: discord.Option(str, choices=['Confidence', 'Desperation'], required=False) # TODO Enums
):
    confidence = False
    desperation = False

    if confidence_desperation:
        if confidence_desperation.title() == 'Confidence':
            confidence = True
        elif confidence_desperation.title() == 'Desperation':
            desperation = True

    response, total = roll_action(
        game=astir.games[ctx.guild_id],
        username=ctx.user.name,
        trait=AstirTrait.CHANNEL.value,
        confidence=confidence,
        desperation=desperation,
        num_advantages=num_advantages,
        num_disadvantages=num_disadvantages
    )

    outcome = armour_astir_moves['arcanist']['tactical illusions'].get_outcome(total)

    response += f'\n\n{bold(outcome)}'

    await ctx.respond(response)


@astir.slash_command(name='scout_giant_slayer', description=f'You can do Attack on Titan moves.')
@command_logging_decorator
@error_responder_decorator
@character_required_decorator
async def scout_giant_slayer_command(
    ctx: Union[discord.ApplicationContext, discord.Message],
):
    await describe_move_command(ctx=ctx, move='Giant Slayer')

@astir.slash_command(name='scout_mobility', description=f'Fight somewhere with room to be agile')
@command_logging_decorator
@error_responder_decorator
@character_required_decorator
async def scout_mobility_command(
    ctx: Union[discord.ApplicationContext, discord.Message],
    num_advantages: discord.Option(int, description="How many advantages do you have?", default=0, required=False),
    num_disadvantages: discord.Option(int, description="How many disadvantages do you have?", default=0, required=False),
    confidence_desperation: discord.Option(str, choices=['Confidence', 'Desperation'], required=False) # TODO Enums
):
    confidence = False
    desperation = False

    if confidence_desperation:
        if confidence_desperation.title() == 'Confidence':
            confidence = True
        elif confidence_desperation.title() == 'Desperation':
            desperation = True

    response, total = roll_action(
        game=astir.games[ctx.guild_id],
        username=ctx.user.name,
        trait=AstirTrait.DEFY.value, # TODO These should come from the move itself. A lot of these can honestly just be thin wrappers passing in a move.
        confidence=confidence,
        desperation=desperation,
        num_advantages=num_advantages,
        num_disadvantages=num_disadvantages
    )

    outcome = armour_astir_moves['scout']['mobility'].get_outcome(total)

    response += f'\n\n{bold(outcome)}'

    await ctx.respond(response)

@astir.slash_command(name='scout_path_finding', description=f'Lead groups on long journeys')
@command_logging_decorator
@error_responder_decorator
@character_required_decorator
async def scout_path_finding_command(
    ctx: Union[discord.ApplicationContext, discord.Message],
):
    await describe_move_command(ctx=ctx, move='Path-Finding')

@astir.slash_command(name='revenant_never_quite_free', description=f'Someone\'s trying to kill you')
@command_logging_decorator
@error_responder_decorator
@character_required_decorator
async def revenant_never_quite_free_command(
    ctx: Union[discord.ApplicationContext, discord.Message],
    num_advantages: discord.Option(int, description="How many advantages do you have?", default=0, required=False),
    num_disadvantages: discord.Option(int, description="How many disadvantages do you have?", default=0, required=False),
    confidence_desperation: discord.Option(str, choices=['Confidence', 'Desperation'], required=False) # TODO Enums
):
    confidence = False
    desperation = False

    if confidence_desperation:
        if confidence_desperation.title() == 'Confidence':
            confidence = True
        elif confidence_desperation.title() == 'Desperation':
            desperation = True

    response, total = roll_action(
        game=astir.games[ctx.guild_id],
        username=ctx.user.name,
        trait=AstirTrait.CHANNEL.value,
        confidence=confidence,
        desperation=desperation,
        num_advantages=num_advantages,
        num_disadvantages=num_disadvantages
    )

    outcome = armour_astir_moves['revenant']['never quite free'].get_outcome(total)

    response += f'\n\n{bold(outcome)}'

    await ctx.respond(response)

@astir.slash_command(name='revenant_unfettered', description=f'Be immune to stuff related to be being alive')
@command_logging_decorator
@error_responder_decorator
@character_required_decorator
async def revenant_unfettered_command(
    ctx: Union[discord.ApplicationContext, discord.Message],
):
    await describe_move_command(ctx=ctx, move='Unfettered')

@astir.slash_command(name='commander_ace_crew', description=f'Stronger than the sum of your parts')
@command_logging_decorator
@error_responder_decorator
@character_required_decorator
async def commander_ace_crew_command(
    ctx: Union[discord.ApplicationContext, discord.Message],
):
    await describe_move_command(ctx=ctx, move='Ace Crew')

@astir.slash_command(name='commander_debrief', description=f'Handle the paperwork')
@command_logging_decorator
@error_responder_decorator
@character_required_decorator
async def commander_debrief_command(
    ctx: Union[discord.ApplicationContext, discord.Message],
):
    await describe_move_command(ctx=ctx, move='Debrief')

@astir.slash_command(name='commander_tactical_entry', description=f'Fly through buildings with your custom ardent')
@command_logging_decorator
@error_responder_decorator
@character_required_decorator
async def commander_tactical_entry_command(
    ctx: Union[discord.ApplicationContext, discord.Message],
):
    await describe_move_command(ctx=ctx, move='Tactical Entry')

@astir.slash_command(name='lead_a_sortie', description=f'Someone\'s trying to kill you')
@command_logging_decorator
@error_responder_decorator
@character_required_decorator
async def lead_a_sortie_command(
    ctx: Union[discord.ApplicationContext, discord.Message],
    skill: discord.Option(str, choices=list(armour_astir_moves['special']['lead a sortie'].traits.keys()), description='Which trait are you using?'),
    num_advantages: discord.Option(int, description="How many advantages do you have?", default=0, required=False),
    num_disadvantages: discord.Option(int, description="How many disadvantages do you have?", default=0, required=False),
    confidence_desperation: discord.Option(str, choices=['Confidence', 'Desperation'], required=False) # TODO Enums
):
    confidence = False
    desperation = False

    if confidence_desperation:
        if confidence_desperation.title() == 'Confidence':
            confidence = True
        elif confidence_desperation.title() == 'Desperation':
            desperation = True

    response, total = roll_action(
        game=astir.games[ctx.guild_id],
        username=ctx.user.name,
        trait=skill,
        confidence=confidence,
        desperation=desperation,
        num_advantages=num_advantages,
        num_disadvantages=num_disadvantages
    )

    outcome = armour_astir_moves['special']['lead a sortie'].get_outcome(total)

    response += f'\n\n{bold(outcome)}'

    await ctx.respond(response)

@astir.slash_command(name='subsystems', description=f'Activate Subsystems by spending power to re-activate an active module')
@command_logging_decorator
@error_responder_decorator
@character_required_decorator
async def subsystems_command(
    ctx: Union[discord.ApplicationContext, discord.Message],
):
    await describe_move_command(ctx=ctx, move='Subsystems')

@astir.slash_command(name='b_plot', description=f'B in the B-Plot rather than a Sortie')
@command_logging_decorator
@error_responder_decorator
@character_required_decorator
async def commander_tactical_entry_command(
    ctx: Union[discord.ApplicationContext, discord.Message],
):
    await describe_move_command(ctx=ctx, move='B-Plot')

@astir.slash_command(name='cause_conflict_roll', description='Do a conflict roll on behalf of the Cause')
@command_logging_decorator
@error_responder_decorator
async def cause_conflict_roll_command(
    ctx: Union[discord.ApplicationContext, discord.Message],
    opponent_faction_strength: discord.Option(str, choices=['Major', 'Minor'], description='How strong is the Authority faction?'),
):

    response, total = roll_action(
        game=astir.games[ctx.guild_id],
        username=ctx.user.name,
        trait=None,
        confidence=False,
        desperation=False,
        num_advantages=0,
        num_disadvantages=0,
        base_num_dice=1
    )

    success = False
    if opponent_faction_strength == 'Major':
        if total >= 5:
            success = True
    else:
        if total >= 4:
            success = True

    success_text = 'succeed' if success else 'fail'

    response += f'\n\nRolled {total} against a {opponent_faction_strength} faction so you {success_text}'

    await ctx.respond(response)

@astir.slash_command(name='authority_conflict_roll', description='Do a conflict roll on behalf of the Authority')
@command_logging_decorator
@error_responder_decorator
async def authority_conflict_roll_command(
    ctx: Union[discord.ApplicationContext, discord.Message],
    faction_strength: discord.Option(str, choices=['Major', 'Minor'], description='How strong is the Authority faction?'),
):

    response, total = roll_action(
        game=astir.games[ctx.guild_id],
        username=ctx.user.name,
        trait=None,
        confidence=False,
        desperation=False,
        num_advantages=0,
        num_disadvantages=0,
        base_num_dice=1
    )

    success = False
    if faction_strength == 'Major':
        if total < 5:
            success = True
    else:
        if total < 4:
            success = True

    success_text = 'succeed' if success else 'fail'

    response += f'\n\nRolled {total} as a {faction_strength} faction so you {success_text}'

    await ctx.respond(response)

@astir.slash_command(name='help_roll', description='Provides help text for rolling.')
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

@astir.slash_command(name='unlink', description='Unlinks game information from the current server, undoing the last /link')
@command_logging_decorator
@error_responder_decorator
async def unlink_command(
    ctx: discord.ApplicationContext,
):
    response = unlink(astir, ctx.guild_id)

    await ctx.respond(response)

@astir.slash_command(name='link', description='Links the bot to a specified game and character tracker. Adds characters it finds.')
@command_logging_decorator
@error_responder_decorator
async def link_command(
    ctx: discord.ApplicationContext,
    spreadsheet_url: str,
):
    """
    Adds a guild to the bot and links it to a character tracker and game. Also links users to any characters it finds with matching usernames.

    :param ctx: The Discord application context to work within.

    :param spreadsheet_url: The spreadsheet URL for the character tracker.
    """

    interaction = await ctx.respond('Linking...')

    response = link(astir, ctx.guild_id, spreadsheet_url)

    await interaction.edit(content=response)

@astir.slash_command(name='changelog', description='Provides a changelog and version number.')
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

@astir.event
async def on_ready():
    logger.info(f'We have logged in as {astir.user}', stack_info=False)

    await astir.change_presence(activity=discord.Activity(type=discord.ActivityType.playing, name='Run /help to get started.'))

@astir.event
async def on_message(message: discord.Message):
    if message.author == astir.user:
        return

    # TODO Didn't trigger?
    if message.content.lower().strip().startswith('roll') and should_respond('astir', message.channel.members):
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
            'from': f'Astir <mailgun@{os.environ["MAILGUN_SANDBOX_DOMAIN_NAME"]}>',
            'to': os.environ['DEBUG_EMAIL'],
            'subject': 'Astir Error',
            'text': message
        }
    )

    response.raise_for_status()

    return response.json()

def main():
    with open('credentials_astir.json', 'r') as f:
        token = json.load(f)['token']

    dotenv.load_dotenv()

    atexit.register(send_email, message='Astir has stopped running.')

    for server_data_dir in glob.glob(os.path.join('servers', '*')):
        guild_id = int(server_data_dir.split(os.sep)[1])

        try:
            game = AstirGame.load(guild_id)

            astir.add_game(game=game)

            logger.info(f'Loaded {game}', stack_info=False)
        except FileNotFoundError as fe:
            logger.error(fe, exc_info=True)
            continue
        except UnknownSystemError as u:
            logger.debug(u)
            continue

    astir.run(token=token)

if __name__ == '__main__':
    main()