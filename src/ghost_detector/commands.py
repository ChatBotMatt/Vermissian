import functools
import json
import random
from typing import Literal

from src.ghost_detector.GhostDetector import GhostDetector
from src.ghost_detector.GhostGame import GhostGame, Card
from src.utils.format import bold, code, bullet, no_embed, quote

def get_changelog():
    """
    :help: Provides a version number and changelog.
    """

    message = f'''Version: 1.0.1
* Ghost Detector will no longer try to respond to the same roll message as Vermissian if they're both in the same channel. 
'''

    return message

def get_credits():
    """
    :help: Provides the credits for the dice bot - who helped bring it to life?
    """

    message = '''The Ghost Detector dice bot is a project by jaffa6.

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

    message += f'\n\nGhost Detector\'s icon was done by Spooksiedoodle, whose work you can find here: {no_embed("https://www.tumblr.com/spooksiedoodle/744425660184936448/commissions-are-open-i-have-some-ttrpg-specials")}'

    message += f'''\n\nGet Out, Run belongs to Junk Food Games. You can find out more and support the game at https://junkfoodgames.itch.io/come-back-now-get-out-run.'''
    
    return message

def get_about():
    message = f'''For legal info, see {code("/legal")}.

This is an unofficial card bot, designed for "Get Out, Run", by jaffa6. 

You can find a list of available commands by using {code("/help")}. 

The Ghost Detector card bot is an independent production by jaffa6 (me) and is not affiliated with Junk Food Games.'''
    
    return message

def get_legal():
    return '''The Ghost Detector card bot is an independent production by jaffa6 (me) and is not affiliated with Junk Food Games.'''

def log_suggestion(username: str, suggestion: str):
    with open('user_suggestions_Ghost_Detector.log', 'a', encoding='utf-8') as f:
        f.write(f'Suggestion from {username}: ' + suggestion[:5000] + '\n')

    return f'Thanks for the suggestion! Please note that not everything is feasible (especially for a free bot) and it can be difficult to predict what\'s easy or hard to do. <https://xkcd.com/1425/> That being said, I really do appreciate your interest, and I read every suggestion!'

def get_cards(mode: Literal['questions', 'tools', 'fates']):
    if not hasattr(get_cards, 'cards'):
        with open('ghost_cards.json', 'r', encoding='utf-8') as f:
            get_cards.cards = json.load(f)

    return get_cards.cards[mode]

# TODO Test each card's length like we do with commands to make sure it won't be cutoff
def draw_question_card(game: GhostGame) -> str:
    card = game.draw_card()

    if card is None:
        return f'You have drawn all of the cards! Use {code("/shuffle")} to refresh the deck.'
    else:
        card_name = get_full_card_name(card)

        effect = get_cards('questions')[card.value]

        tool = get_cards('tools')[card.suit]

        return f'''## {card_name}
    
{bold("Answer the following")}: 
{quote(effect)}

The relevant tool is the {tool}'''

def draw_fate_card(game: GhostGame) -> str:
    card = game.draw_card()

    if card is None:
        return f'You have drawn all of the cards! Use {code("/shuffle")} to refresh the deck.'
    else:
        card_name = get_full_card_name(card)

        effect = get_cards('fates')[card.value]

        return f'''## {card_name}

{bold("This is your fate...")}\n\n{effect}'''

def draw_card() -> str:
    if not hasattr(draw_card, 'cards'):
        replacements = {
            1: 'Ace',
            11: 'Jack',
            12: 'Queen',
            13: 'King'
        }

        cards = []

        for idx in range(1, 13):
            for suit in ['Clubs', 'Hearts', 'Spades', 'Diamonds']:
                if idx in replacements:
                    value = replacements[idx]
                else:
                    value = idx

                cards.append(Card(value=str(value), suit=suit))

        draw_card.cards = cards

    card = random.choice(draw_card.cards)

    card_name = get_full_card_name(card)

    return f'You have drawn a {bold(card_name)}'

def shuffle(game: GhostGame) -> str:
    game.refresh_cards()

    return 'Cards refreshed!'

@functools.lru_cache()
def get_full_card_name(card: Card):
    return f'{card.value} of {card.suit}'

def unlink(ghost_detector: GhostDetector, guild_id: int):
    if guild_id in ghost_detector.games:
        ghost_detector.remove_game(guild_id)

        return f'Unlinked! You can use the servers for other games now. You can re-link by using {code("/link")}.'
    else:
        return 'No game to unlink.'

def link(ghost_detector: GhostDetector, guild_id: int):
    if guild_id in ghost_detector.games:
        return 'Game already linked.'

    ghost_detector.create_game(guild_id=guild_id)

    return 'Game created! You can now start exploring.'
