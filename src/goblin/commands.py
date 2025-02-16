import functools
import json
import random
from typing import Literal, Tuple, List

from src.goblin.Goblin import Goblin
from src.goblin.GoblinGame import GoblinGame
from src.utils.format import bold, code, bullet, no_embed, quote
from src.Roll import Roll

def get_changelog():
    """
    :help: Provides a version number and changelog.
    """

    message = f'''Version: 1.0.0
'''

    return message

def get_credits():
    """
    :help: Provides the credits for the dice bot - who helped bring it to life?
    """

    message = '''The Goblin Dice Bot is a project by jaffa6.

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

    message += f'\n\nGoblin\'s icon was done by Spooksiedoodle, whose work you can find here: {no_embed("https://www.tumblr.com/spooksiedoodle/744425660184936448/commissions-are-open-i-have-some-ttrpg-specials")}'

    # TODO Update for Goblin Quest
    # message += f'''\n\nGet Out, Run belongs to Junk Food Games. You can find out more and support the game at https://junkfoodgames.itch.io/come-back-now-get-out-run.'''
    
    return message

def get_about():
    # TODO Update for Goblin Quest
    message = f'''For legal info, see {code("/legal")}.

This is an unofficial card bot, designed for "Goblin Quest", by jaffa6. 

You can find a list of available commands by using {code("/help")}. 

The Goblin Quest card bot is an independent production by jaffa6 (me) and is not affiliated with Junk Food Games.'''
    
    return message

def get_legal():
    # TODO Update for Goblin Quest
    return '''The Ghost Detector card bot is an independent production by jaffa6 (me) and is not affiliated with Junk Food Games.'''

def log_suggestion(username: str, suggestion: str):
    with open('user_suggestions_Goblin.log', 'a', encoding='utf-8') as f:
        f.write(f'Suggestion from {username}: ' + suggestion[:5000] + '\n')

    return f'Thanks for the suggestion! Please note that not everything is feasible (especially for a free bot) and it can be difficult to predict what\'s easy or hard to do. <https://xkcd.com/1425/> That being said, I really do appreciate your interest, and I read every suggestion!'


def unlink(goblin: Goblin, guild_id: int):
    if guild_id in goblin.games:
        goblin.remove_game(guild_id)

        return f'Unlinked! You can use the servers for other games now. You can re-link by using {code("/link")}.'
    else:
        return 'No game to unlink.'

def link(goblin: Goblin, guild_id: int):
    if guild_id in goblin.games:
        return 'Game already linked.'

    goblin.create_game(guild_id=guild_id)

    return 'Game created! You can now start exploring.'

def roll(num_additional: int = 0, bonus: int = 0, malus: int = 0) -> List[int]:
    if num_additional < 0:
        raise ValueError(f'Cannot have negative additional dice')

    num_dice = 1 + num_additional

    roll = Roll(num_dice=num_dice, dice_size=6, bonus=bonus, penalty=malus)

    results = roll.roll(cut_highest_first=False)[0]

    return results


