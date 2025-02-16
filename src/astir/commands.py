import collections
import random
import functools
from typing import List, Optional, Tuple, Union

from discord.ext.pages import Page, Paginator

from src.astir.Astir import Astir
from src.astir.AstirGame import AstirGame
from src.astir.AstirCharacterSheet import AstirTrait
from src.astir.AstirMove import AstirMove
from src.astir.utils import load_moves
from src.Roll import Roll
from src.utils.format import bold, underline, code, quote, bullet, no_embed
from src.utils.logger import get_logger
from src.utils.exceptions import BotError


# TODO Add Hammertime stuff? There's no API or calendar input, so tricky.

def get_changelog():
    """
    :help: Provides a version number and changelog.
    """

    message = f'''Version: 1.0.0

{underline("Changes")}
{bullet('Nothing yet! This is the initial release and all.')}
'''

    return message

def get_credits():
    """
    :help: Provides the credits for the dice bot - who helped bring it to life?
    """

    message = '''The Astir dice bot is a project by jaffa6.

    The following people helped test it, and are responsible for making it a lot nicer to work with!'''

    testers = [
        'yuriAza',
        f'SavvyWolf, who you can find at {no_embed("https://savvywolf.scot/")}',
        'spatialwarp',
        f'Ben K. Rosenbloom, {no_embed("https://benkrosenbloom.itch.io/")}', # TODO Potentially need to update these
        'DayaLuna for being a great rubber duck'
    ]

    tester_components = []

    for tester in testers:
        tester_components.append(tester)

    message += f'\n' + '\n'.join(bullet(tester) for tester in testers)

    message += f'\n\nAstir\'s icon was done by Spooksiedoodle, whose work you can find here: {no_embed("https://www.tumblr.com/spooksiedoodle/744425660184936448/commissions-are-open-i-have-some-ttrpg-specials")}'

    message += f'''\n\nArmour Astir: Advent is copyright Briar Sovereign. You can find out more and support the game at {no_embed("https://weregazelle.itch.io/armour-astir")}'''

    return message

def get_about():
    message = f'''For legal info, see {code("/legal")}.

This is an unofficial dice bot, designed for Armour Astir: Advent, by jaffa6. 

You can find a list of available commands by using {code("/help")}. 

The dice bot pulls data from ([character trackers]({no_embed("http://tinyurl.com/aaasheets")}) made by Ida Ailes which you can copy and add your own characters to.

It does require a fixed structure in the tracker, so please don't move stuff around in them or it might not work properly for you.

You can link to a character tracker via "{code("/link")}" and add characters via "{code("/add_character")}".

Outside of the trackers, you can also use it for freeform rolling by typing stuff like "{code("roll 3d6" or "roll 4d2 + 5 - 2, 3d7 + 21")}" 

The Astir dice bot is an independent production by jaffa6 (me) and is not affiliated with Briar Sovereign. '''

    return message

def get_legal():
    return '''The Astir dice bot is an independent production by jaffa6 (me) and is not affiliated with Briar Sovereign.'''

def log_suggestion(username: str, suggestion: str):
    with open('user_suggestions_astir.log', 'a', encoding='utf-8') as f:
        f.write(f'Suggestion from {username}: ' + suggestion[:5000] + '\n')

    return f'Thanks for the suggestion! Please note that not everything is feasible (especially for a free bot) and it can be difficult to predict what\'s easy or hard to do. <https://xkcd.com/1425/> That being said, I really do appreciate your interest, and I read every suggestion!'

def get_getting_started_page_content():
    getting_started_message = f'''To get started, use {code("/link")} to link the bot to your character tracker. It will automatically try to link users to characters. 

* [Spire Character Tracker Template](<https://docs.google.com/spreadsheets/d/1saogmy4eNNKng32Pf39b7K3Ko4uHEuWClm7UM-7Kd8I/edit?usp=sharing>)
* [Heart Character Tracker Template](<https://docs.google.com/spreadsheets/d/1PzF3ZHQpXXaS0ci0Q0vbE9uHpC26GiUJ4ishIbbcpOY/edit?usp=sharing>)

Copy the template and fill in your own information. Linking works best once characters have Discord Usernames associated with them because it will auto-link to those users, but otherwise you can use {code("/ add_character")}

This will work best if you have already filled characters in.

The bot does not currently support multiple games being run in the same server - {code("/link")}ing one character tracker will overwrite the previous one.

You can also run {code("/add_character")}, passing in the URL for your specific tab on the character tracker, to link your own character to yourself. You can only have one character per user at once.'''

    return 'Getting Started', getting_started_message

def get_debugging_page_content():
    debugging_message = f'If the bot doesn\'t appear to be working properly, please try these things in order, and **if** none of those fix it then message jaffa6 on Discord with a screenshot and a description of the problem ("What went wrong? What did you expect to happen?"):'

    fix_steps = [
        'Ensure that your character tracker is up-to-date enough for the bot to work with it. It should have the "Discord Username" field in the character sheets and if it doesn\'t, it\'s not compatible.',
        f'Ensure that your character tracker\'s structure is identical to the latest master one listed [here]({no_embed("http://tinyurl.com/aaasheets")}) - if you move things around, or add new rows or columns that reposition stuff, it\'ll probably stop reading it correctly!',
        'Wait a minute or so, then try again.'
    ]

    debugging_message += '\n\n' + '\n'.join(bullet(step) for step in fix_steps)

    return 'Fixing Errors', debugging_message

@functools.lru_cache()
def get_tag(tag: str):
    if not hasattr(get_tag, 'lowercase_tags'):
        lowercase_tags = {}

        for group, group_tags in AstirGame.TAGS.items():
            for tag, description in group_tags.items():
                lowercase_tags[tag.lower()] = description

        get_tag.lowercase_tags = lowercase_tags

    logger = get_logger()

    lowercase_tag = tag.lower()

    if lowercase_tag in get_tag.lowercase_tags:
        message = f'{bold(tag)}: {get_tag.lowercase_tags[lowercase_tag]}'
    else:
        message = f'Cannot find tag "{tag}"'
        logger.warning(f'Unknown tag: "{tag}" searched for.')

    if len(message) > 2000:
        message = 'The tag description is very long so some of it is cut off.\n\n' + message

    message = message[:2000]

    return message

# By god these need testing with Discord output. Maybe have a diagnostic command just in the testing server that prints all of them in turn.
# Also an automated test that's similar ofc. They're complex in their structure and use string templates.

def format_move(move_to_format: AstirMove) -> str:
    quoted_description = '\n'.join(quote(line) for line in move_to_format.description.split('\n'))

    formatted = f'[{move_to_format.playbook.title()}] {bold(move_to_format.name)}:\n\n{quoted_description}'

    return formatted


@functools.lru_cache(maxsize=200)
def get_move(move: str) -> Union[str, Paginator]:
    if not hasattr(get_move, 'moves'):
            moves = load_moves()

            get_move.moves = moves

    logger = get_logger()

    lower_move = move.lower()

    playbook_searched = None
    if '_' in lower_move:
        playbook_searched, lower_move = lower_move.split('_')[0]

    candidates = collections.defaultdict(list)

    if playbook_searched is None:
        for playbook, playbook_moves in get_move.moves.items():
            if lower_move in playbook_moves:
                candidates[playbook].append(playbook_moves[lower_move])
    else:
        if playbook_searched not in get_move.moves:
            logger.warning(f'Searched for unknown playbook "{playbook_searched}".')

        if lower_move in get_move.moves[playbook_searched]:
            candidates[playbook_searched].append(get_move.moves[playbook_searched][lower_move])

    message = None
    paginator = None
    if len(candidates) == 0:
        logger.warning(f'Tried to find unknown move "{move}".')
        message = f'Cannot find ability "{move}"!'
    elif len(candidates) == 1:
        found_moves = candidates.popitem()[1]

        if len(found_moves) == 1:
            message = format_move(found_moves[0])

    if message is None:
        pages = []
        headers = []

        for playbook, playbook_moves in candidates.items():
            for move in playbook_moves:
                header = f'[{playbook.title()}] - {move.name}'

                headers.append(header)

        # TODO Make a Paginator factory that handles header/prev/next setup automatically
        for playbook, playbook_moves in candidates.items():
            for move in playbook_moves:
                header = headers[len(pages)]

                page_content = f'{bold(underline(header))}\n{move.description}'

                if len(headers) > 0:
                    prev_text = f'\n\nPrevious: {headers[len(headers) - 1]}'
                else:
                    prev_text = ''
                    page_content += f'\n\nPrevious: {headers[len(headers) - 1]}'

                if len(headers) < len(headers) - 1:
                    next_text = f'\n\nNext: {headers[len(headers) - 1]}'
                else:
                    next_text = ''

                limit = 2000 - len(prev_text) - len(next_text)

                if len(page_content) > limit:
                    page_content = 'The page is very long so some of it is cut off\n\n' + page_content

                page_content = page_content[: limit]

                page_content += prev_text
                page_content += next_text

                pages.append(Page(content=page_content, embeds=[]))

        paginator = Paginator(pages)

    if message is not None:
        if len(message) > 2000:
            message = 'The move description is very long so some of it is cut off\n\n' + message

        message = message[:2000]

        return message
    else:
        return paginator

def add_character(game: AstirGame, discord_username: str, discord_display_name: str, character_sheet_url: str):
    character = game.add_character(spreadsheet_url=character_sheet_url, username=discord_username)

    response = f"Added character {character.character_name} and linked them to {discord_display_name}."

    response = response[:2000]

    return response

def build_response(
    roll: Roll,
    total: int,
    formatted_results: List[str],
    formatted_confidence_desperation_results: List[str],
    confidence: bool = False,
    desperation: bool = False,
    warning: str = ''
):
    # TODO Colour coding?
    #  https://gist.github.com/kkrypt0nn/a02506f3712ff2d1c8ca7c9e0aed7c06
    #  https://rebane2001.com/discord-colored-text-generator/

    if confidence:
        confidence_desperation_expression = ' with confidence'
    elif desperation:
        confidence_desperation_expression = ' in desperation'
    else:
        confidence_desperation_expression = ''

    modifier_expression = ''

    if roll.bonus > 0:
        modifier_expression += f' + {roll.bonus}'

    if roll.penalty > 0:
        modifier_expression += f' - {roll.penalty}'

    warning_expression = f'\n\n{warning}' if warning else ''

    if formatted_results != formatted_confidence_desperation_results:
        response = f'''You rolled {len(formatted_results)}d{roll.dice_size}{modifier_expression}{confidence_desperation_expression} -> {formatted_results}
which was modified{confidence_desperation_expression} to produce
{formatted_confidence_desperation_results}{modifier_expression} for a total of {bold(total)}'''
    else:
        response = f'You rolled {len(formatted_confidence_desperation_results)}d{roll.dice_size}{confidence_desperation_expression}{modifier_expression} for a total of **{total}**: {{{", ".join(formatted_confidence_desperation_results)}}}{modifier_expression}'

    response += warning_expression

    return response

# TODO "Help or Hinder" is a bastard that wants a numeric modifier instead
# Fuck knows how I'll handle that
# Optional trait? Ugh.
# Just make it its own move? Honestly easier... Maybe one command per move.
# Most of which are just thin wrappers around a unified one, but still. Handles edge cases well.
def roll_action(
    game: AstirGame,
    username: str,
    trait: Optional[str] = None,
    confidence: bool = False,
    desperation: bool = False,
    num_advantages: int = 0,
    num_disadvantages: int = 0,
    modifier: int = 0,
    base_num_dice: int =2
) -> Tuple[str, int]:

    if num_advantages < 0:
        raise BotError(f'Cannot have a negative number of advantages.')

    if num_disadvantages < 0:
        raise BotError(f'Cannot have a negative number of disadvantages.')

    roll = Roll(num_dice=base_num_dice, dice_size=6)

    if trait is not None:
        trait_to_use = AstirTrait.get(trait)
    else:
        trait_to_use = None

    total, formatted_results, formatted_confidence_desperation_results, trait_modifier, had_advantage, had_disadvantage, warning = game.roll_check(
        username=username,
        initial_roll=roll,
        trait=trait_to_use,
        num_advantages=num_advantages,
        num_disadvantages=num_disadvantages,
        confidence=confidence,
        desperation=desperation,
        modifier=modifier,
    )

    response = build_response(
        roll=roll,
        total=total,
        formatted_results=formatted_results,
        formatted_confidence_desperation_results=formatted_confidence_desperation_results,
        confidence=confidence,
        desperation=desperation,
        warning=warning
    )

    if len(response) > 2000:
        response = 'Very long roll, some of it will be cut off.\n\n' + response

    response = response[:2000]

    return response, total

def simple_roll(rolls: List[Roll], note: Optional[str] = None):
    all_formatted = []
    overall_total = 0
    rolled_expression_tokens = []
    all_results_expressions = []
    all_total_expressions = []

    for index, roll in enumerate(rolls):
        results = []

        if (roll.num_dice - roll.drop) > 0:
            for i in range(roll.num_dice - roll.drop):
                result = random.randint(1, roll.dice_size)

                results.append(result)

            indices_to_remove = []

            if roll.cut.num > 0:
                sorted_results = sorted(enumerate(results), key=lambda r: r[1])

                for remove_index, roll_to_remove in sorted_results[- roll.cut.num: ]:
                    indices_to_remove.append(remove_index)

                kept_results = [value for index, value in enumerate(results) if index not in indices_to_remove]
            else:
                kept_results = results

            formatted_rolls = AstirGame.format_roll(results, indices_to_remove)

            total = sum(kept_results) + roll.bonus - roll.penalty
        else:
            formatted_rolls = ['']
            total = 0

        expression = str(roll) if index == len(rolls) - 1 else roll.str_no_cut_drop()

        rolled_expression_tokens.append(expression)

        results_expression = '{' + ', '.join(formatted_rolls) + '}'

        if roll.bonus > 0:
            results_expression += f' + {roll.bonus}'

        if roll.penalty > 0:
            results_expression += f' - {roll.penalty}'

        total_expression = f' {bold("Total: " + str(total))} '

        all_results_expressions.append(results_expression)
        all_total_expressions.append(total_expression)

        all_formatted.append(formatted_rolls)
        overall_total += total

    rolled_expression = ', '.join(rolled_expression_tokens)

    note_expression = f'{quote(note)}\n\n' if note is not None and len(note.strip()) else ''

    if len(all_results_expressions) > 1:
        response_results_expression = '\n' + '\n'.join([bullet(res) + all_total_expressions[index] for index, res in enumerate(all_results_expressions)])
    else:
        response_results_expression = all_results_expressions[0] + all_total_expressions[0]

    response = f'''{note_expression}You rolled {rolled_expression} for: {response_results_expression}'''

    if len(all_results_expressions) > 1:
        response += '\n'

    if len(all_results_expressions) > 1:
        response += f'**Overall Total**: {overall_total}'

    return response

def unlink(astir: Astir, guild_id: int):
    if guild_id in astir.games:
        astir.remove_game(guild_id)

        return f'Unlinked! You can re-link by using {code("/link")}.'
    else:
        return 'No game to unlink.'

def link(astir: Astir, guild_id: int, spreadsheet_url: str):
    if guild_id in astir.games:
        return 'Game already linked.'

    game = astir.create_game(
        guild_id=guild_id,
        spreadsheet_url=spreadsheet_url,
    )

    response = "Linked to character tracker."

    if len(game.character_sheets):
        for discord_username, character_sheet in game.character_sheets.items():
            response += f'\n* Linked "{discord_username}" to character "{character_sheet.character_name}"'
    else:
        response += f'\nNo characters linked yet, you can do so via the {code("/add_character")} command.'

    return response
