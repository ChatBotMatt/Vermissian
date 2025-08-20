import discord
import json
import random
import functools
import re
from typing import List, Tuple, Dict, Optional, Set, Union, Literal

from src.Game import Game
from src.System import System
from src.bloodheist.BloodheistGame import BloodheistGame
from src.bloodheist.Batbot import Batbot
from src.bloodheist.BloodheistCharacterSheet import BloodheistCharacterSheet
from src.Roll import Roll, Cut
from src.utils.format import bold, underline, code, quote, bullet, no_embed
from src.utils.logger import get_logger
from src.utils.exceptions import WrongGameError

def get_changelog():
    """
    :help: Provides a version number and changelog.
    """

    message = f'''Version: 1.0.0

{underline("Changes")}
{bullet('Created')}
'''

    return message

def get_credits():
    """
    :help: Provides the credits for the dice bot - who helped bring it to life?
    """

    message = '''The Bloodheist dice bot is a project by jaffa6.

    The following people helped test the codebase, and are responsible for making it a lot nicer to work with!'''

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

    message += f'\n\nVermissian\'s icon was done by Spooksiedoodle, whose work you can find here: {no_embed("https://www.tumblr.com/spooksiedoodle/744425660184936448/commissions-are-open-i-have-some-ttrpg-specials")}'

    message += f'''\n\nSpire is copyright Rowan, Rook and Decard. You can find out more and support these games at rowanrookanddecard.com and you can find Spire at {no_embed("https://rowanrookanddecard.com/product/spire-rpg/")}

    Heart is copyright Rowan, Rook and Decard. You can find out more and support these games at rowanrookanddecard.com and you can find Heart at {no_embed("https://rowanrookanddecard.com/product/heart-the-city-beneath-rpg/")}

    ichor-drowned, which the Delve Draws mechanic is from, is a product of Sillion L and Brendan McLeod. It can be found at {no_embed("https://sillionl.itch.io/ichor-drowned.")}'''

    return message

def get_about():
    message = f'''For legal info, see {code("/legal")}.

This is an unofficial dice bot, designed for Spire and Heart, by jaffa6. 

You can find a list of available commands by using {code("/help")}. 

The dice bot pulls data from character trackers ([Spire](<https://docs.google.com/spreadsheets/d/1saogmy4eNNKng32Pf39b7K3Ko4uHEuWClm7UM-7Kd8I/edit?usp=sharing>) or [Heart](<https://docs.google.com/spreadsheets/d/1PzF3ZHQpXXaS0ci0Q0vbE9uHpC26GiUJ4ishIbbcpOY/edit?usp=sharing>)) which you can copy and add your own characters to.

It does require a fixed structure in the tracker, so please don't move stuff around in them or it might not work properly for you.

You can link to a character tracker via "{code("/link")}" and add characters via "{code("/add_character")}".

Outside of the trackers, you can also use it for freeform rolling by typing stuff like "{code("roll 3d6" or "roll 4d2 + 5 - 2, 3d7 + 21")}" 

The Vermissian dice bot is an independent production by jaffa6 (me) and is not affiliated with Rowan, Rook and Decard. It is published under the RR&D Community License.

Spire is copyright Rowan, Rook and Decard. You can find out more and support these games at rowanrookanddecard.com and you can find Spire at https://rowanrookanddecard.com/product/spire-rpg/.

Heart is copyright Rowan, Rook and Decard. You can find out more and support these games at rowanrookanddecard.com and you can find Heart at https://rowanrookanddecard.com/product/heart-the-city-beneath-rpg/.

ichor-drowned is a product by Sillion L and Brendan McLeod, with whom I'm not affiliated, but they've generously allowed me to include their content here. You can buy it here: https://sillionl.itch.io/ichor-drowned'''

    return message

def get_legal():
    return '''The Vermissian dice bot is an independent production by jaffa6 (me) and is not affiliated with Rowan, Rook and Decard. It is published under the RR&D Community License.

Spire is copyright Rowan, Rook and Decard. You can find out more and support these games at rowanrookanddecard.com and you can find Spire at https://rowanrookanddecard.com/product/spire-rpg/

Heart is copyright Rowan, Rook and Decard. You can find out more and support these games at rowanrookanddecard.com and you can find Heart at https://rowanrookanddecard.com/product/heart-the-city-beneath-rpg/

ichor-drowned is a product of Sillion L and Brandan McLeod, with whom I'm not affiliated, but they've generously allowed me to include their content here. You can buy it here: https://sillionl.itch.io/ichor-drowned'''

def log_suggestion(username: str, suggestion: str):
    with open('user_suggestions_vermissian.log', 'a', encoding='utf-8') as f:
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
        'Ensure that your character tracker\'s structure is identical to the master one located at [Spire](<https://docs.google.com/spreadsheets/d/1saogmy4eNNKng32Pf39b7K3Ko4uHEuWClm7UM-7Kd8I/edit?usp=sharing>) or [Heart](<https://docs.google.com/spreadsheets/d/1PzF3ZHQpXXaS0ci0Q0vbE9uHpC26GiUJ4ishIbbcpOY/edit?usp=sharing>) - if you move things around, or add new rows or columns that reposition stuff, it\'ll probably stop reading it correctly!',
        'Wait a minute or so, then try again.'
    ]

    debugging_message += '\n\n' + '\n'.join(bullet(step) for step in fix_steps)

    return 'Fixing Errors', debugging_message

@functools.lru_cache()
def get_full_card_name(card_value: Union[int, str], suit: str):
    return f'{card_value} of {suit}s'

def add_character(game: Game, discord_username: str, discord_display_name: str, character_sheet_url: str):
    character = game.add_character(spreadsheet_url=character_sheet_url, username=discord_username)

    response = f"Added character {character.character_name} and linked them to {discord_display_name}."

    response = response[:2000]

    return response

def roll_action(game: BloodheistGame, username: str, skill: bool, tool: bool, helped: bool, num_doom_dice: int = 0):
    num_dice = 1
    dice_size = 6

    if skill:
        num_dice += 1

    if tool:
        num_dice += 1

    if helped:
        num_dice += 1

    light_roll = Roll(num_dice=num_dice, dice_size=dice_size)
    doom_roll = Roll(num_dice=num_doom_dice, dice_size=dice_size)

    highest, results, outcome, total, had_skill, had_domain, used_difficult_actions_table = game.roll_check(
        username=username,
        initial_roll=light_roll,
        skill=skill_to_use,
        domain=domain_to_use
    )

    if used_difficult_actions_table:
        downgrade_expression = 'on the Difficult Actions table'

    skill_text = bold(skill_to_use.value) if had_skill else skill_to_use.value
    domain_text = bold(domain_to_use.value) if had_domain else domain_to_use.value

    modifier_expression = f'{skill_text}+{domain_text}'

    if mastery:
        modifier_expression += ', mastery'

    if num_helpers > 0:
        modifier_expression += f', {num_helpers} helpers'

    response = f'You rolled {len(results)}d{dice_size} ({modifier_expression}) {"" if difficulty == 0 else f" with a difficulty of {difficulty}"} {downgrade_expression}for a "**{outcome}**": {{{", ".join(results)}}}'

    if len(response) > 2000:
        response = 'Very long roll, some of it will be cut off.\n\n' + response

    response = response[:2000]

    return response

def unlink(batbot: Batbot, guild_id: int):
    if guild_id in batbot.games:
        batbot.remove_game(guild_id)

        return f'Unlinked! You can re-link by using {code("/link")}.'
    else:
        return 'No game to unlink.'

def link(batbot: Batbot, guild_id: int, spreadsheet_url: str):
    if guild_id in batbot.games:
        return 'Game already linked.'

    game = batbot.create_game(guild_id=guild_id, spreadsheet_url=spreadsheet_url)

    response = "Linked to character tracker."

    if len(game.character_sheets):
        for discord_username, character_sheet in game.character_sheets.items():
            response += f'\n* Linked "{discord_username}" to character "{character_sheet.character_name}"'
    else:
        response += f'\nNo characters linked yet, you can do so via the {code("/add_character")} command.'

    return response
