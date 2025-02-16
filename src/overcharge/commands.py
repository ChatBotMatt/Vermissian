import json
import random
import functools
from dataclasses import dataclass
from typing import List, Dict, Optional, Literal

from src.overcharge.Overcharge import Overcharge
from src.overcharge.DieGame import DieGame
from src.Roll import Roll, Cut
from src.utils.format import bold, code, quote, bullet, no_embed

@dataclass
class DieAbility:
    die_class: str
    name: str
    description: str

    @staticmethod
    def from_json(json_data: Dict[Literal['die_class', 'name', 'description'], str]):
        return DieAbility(** json_data)

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

    message = '''The Overcharge dice bot is a project by jaffa6.

    The following people helped test it (or the shared code with Vermissian), or otherwise contributed, and are responsible for making it a lot nicer to work with!'''

    testers = [
        'yuriAza',
        f'SavvyWolf, who you can find at {no_embed("https://savvywolf.scot/")}',
        'spatialwarp',
        f'Ben K. Rosenbloom, {no_embed("https://benkrosenbloom.itch.io/")}',  # TODO Potentially need to update these
        'DayaLuna for being a great rubber duck'
    ]

    tester_components = []

    for tester in testers:
        tester_components.append(tester)

    message += f'\n' + '\n'.join(bullet(tester) for tester in testers)

    # TODO Get an icon
    # message += f'\n\nOvercharge\'s icon was done by Spooksiedoodle, whose work you can find here: {no_embed("https://www.tumblr.com/spooksiedoodle/744425660184936448/commissions-are-open-i-have-some-ttrpg-specials")}'

    message += f'''\n\nThe DIE RPG is copyright Rowan, Rook and Decard. You can find out more and support these games at rowanrookanddecard.com and you can find DIE at {no_embed("https://rowanrookanddecard.com/product-category/game-systems/die-rpg/")}'''

    return message


def get_about():
    message = f'''For legal info, see {code("/legal")}.

This is an unofficial dice bot, designed for DIE RPG, by jaffa6. 

You can find a list of available commands by using {code("/help")}. 

The dice bot pulls data from a [character tracker](<https://docs.google.com/spreadsheets/d/1YkRW3TuWe-ujv3xoTVvyMyJZsFWJoFe3E18hjIDZPmc/edit?usp=sharing>) which you can copy and add your own characters to.

It does require a fixed structure in the tracker, so please don't move stuff around in them or it might not work properly for you.

You can link to a character tracker via "{code("/link")}" and add characters via "{code("/add_character")}".

Outside of the trackers, you can also use it for freeform rolling by typing stuff like "{code("roll 3d6" or "roll 4d2 + 5 - 2, 3d7 + 21")}" 

The Overcharge dice bot is an independent production by jaffa6 (me) and is not affiliated with Rowan, Rook and Decard. It is published under the RR&D Community License.

DIE RPG is copyright Rowan, Rook and Decard. You can find out more and support these games at rowanrookanddecard.com and you can find DIE at {no_embed("https://rowanrookanddecard.com/product-category/game-systems/die-rpg/")}.'''

    return message

def get_legal():
    return f'''The Overcharge dice bot is an independent production by jaffa6 (me) and is not affiliated with Rowan, Rook and Decard. It is published under the RR&D Community License.

DIE RPG is copyright Rowan, Rook and Decard. You can find out more and support these games at rowanrookanddecard.com and you can find DIE at {no_embed("https://rowanrookanddecard.com/product-category/game-systems/die-rpg/")}.'''

def log_suggestion(username: str, suggestion: str):
    with open('user_suggestions_overcharge.log', 'a', encoding='utf-8') as f:
        f.write(f'Suggestion from {username}: ' + suggestion[:5000] + '\n')

    return f'Thanks for the suggestion! Please note that not everything is feasible (especially for a free bot) and it can be difficult to predict what\'s easy or hard to do. <https://xkcd.com/1425/> That being said, I really do appreciate your interest, and I read every suggestion!'

def get_getting_started_page_content():
    getting_started_message = f'''To get started, use {code("/link")} to link the bot to your character tracker. It will automatically try to link users to characters. 

You can find the DIE RPG Character Tracker Template [here]({no_embed("https://docs.google.com/spreadsheets/d/1YkRW3TuWe-ujv3xoTVvyMyJZsFWJoFe3E18hjIDZPmc/edit?usp=sharing")})

Copy the template and fill in your own information. Linking works best once characters have Discord Usernames associated with them because it will auto-link to those users, but otherwise you can use {code("/ add_character")}

This will work best if you have already filled characters in.

The bot does not currently support multiple games being run in the same server - {code("/link")}ing one character tracker will overwrite the previous one.

You can also run {code("/add_character")}, passing in the URL for your specific tab on the character tracker, to link your own character to yourself. You can only have one character per user at once.'''

    return 'Getting Started', getting_started_message

def get_debugging_page_content():
    debugging_message = f'If the bot doesn\'t appear to be working properly, please try these things in order, and **if** none of those fix it then message jaffa6 on Discord with a screenshot and a description of the problem ("What went wrong? What did you expect to happen?"):'

    fix_steps = [
        'Ensure that your character tracker is up-to-date enough for the bot to work with it. It should have the "Discord Username" field in the character sheets and if it doesn\'t, it\'s not compatible.',
        f'Ensure that your character tracker\'s structure is identical to the master one located [here]({no_embed("https://docs.google.com/spreadsheets/d/1YkRW3TuWe-ujv3xoTVvyMyJZsFWJoFe3E18hjIDZPmc/edit?usp=sharing")}) or [Heart](<https://docs.google.com/spreadsheets/d/1PzF3ZHQpXXaS0ci0Q0vbE9uHpC26GiUJ4ishIbbcpOY/edit?usp=sharing>) - if you move things around, or add new rows or columns that reposition stuff, it\'ll probably stop reading it correctly!',
        'Wait a minute or so, then try again.'
    ]

    debugging_message += '\n\n' + '\n'.join(bullet(step) for step in fix_steps)

    return 'Fixing Errors', debugging_message

def format_ability(ability_to_format: DieAbility) -> str:
    formatted = f'[{ability_to_format.die_class}] {bold(ability_to_format.name)}:\n\n{ability_to_format.description}'

    return formatted

@functools.lru_cache(maxsize=200)
def get_ability(ability: str):
    # TODO Check length of each in a test - like with commands

    if not hasattr(get_ability, 'abilities'):
        with open('all_abilities_die.json', 'r', encoding='utf-8') as f:
            abilities: Dict[str, DieAbility] = {
                name: DieAbility.from_json(raw_ability) for name, raw_ability in json.load(f).items()
            }

            get_ability.abilities = abilities

    ability_to_use = ability.lower()

    # TODO Double check there's no duplicate ability names
    # TODO Some kind of fuzzy matching or prefix matching would be nice
    if ability_to_use in get_ability.abilities:
        found_ability = get_ability.abilities[ability_to_use]

        message = format_ability(found_ability)
    else:
        message = f'Cannot find ability "{ability_to_use}"!'

    if len(message) > 2000:
        message = 'The ability is very long so some of it is cut off\n\n' + message # TODO Pagination?

    message = message[:2000]

    return message

def add_character(game: DieGame, discord_username: str, discord_display_name: str, character_sheet_url: str):
    character = game.add_character(spreadsheet_url=character_sheet_url, username=discord_username)

    response = f"Added character {character.character_name} and linked them to {discord_display_name}."

    response = response[:2000]

    return response

def apply_difficulty(results: List[int], difficulty: int):
    indices_to_remove = []

    sorted_results = sorted(enumerate(results), key=lambda r: r[1])

    for remove_index, roll_to_remove in sorted_results[- difficulty:]:
        indices_to_remove.append(remove_index)

    kept_results = [value for index, value in enumerate(results) if index not in indices_to_remove]

    return indices_to_remove, kept_results

def classless_roll(base_num_dice: int, advantages: int, disadvantages: int, difficulty: int):
    num_dice = max(base_num_dice + advantages - disadvantages, 0)

    if num_dice == 0:
        rolled_zero_pool = True
        roll = Roll(num_dice=2, dice_size=6, drop=0, cut=Cut(num=1, threshold=4)) # Roll 2, take lowest

        results, base_indices_to_remove, base_kept_results = roll.roll(cut_highest_first=True)

        indexed_kept_results = list( (idx, result) for idx, result in enumerate(results) if idx not in base_indices_to_remove)

        raw_post_difficulty_indices_to_remove, kept_results = Roll.cut_rolls(base_kept_results, cut=Cut(num=difficulty, threshold=4), highest_first=False)

        post_difficulty_indices_to_remove = [ indexed_kept_results[raw_post_difficulty_indice_to_remove][0] for raw_post_difficulty_indice_to_remove in raw_post_difficulty_indices_to_remove ]

        indices_to_remove = [
            * base_indices_to_remove,
            * post_difficulty_indices_to_remove
        ]
    else:
        rolled_zero_pool = False
        roll = Roll(num_dice=num_dice, dice_size=6, cut=Cut(difficulty, threshold=4))

        results, indices_to_remove, kept_results = roll.roll(cut_highest_first=False)

    return roll, results, indices_to_remove, kept_results, rolled_zero_pool

# TODO This ***incredibly*** needs testing, and ideally simplifying.
def class_die_roll(base_num_dice: int, class_die_size: int, advantages: int, disadvantages: int, difficulty: int):
    num_dice = max(base_num_dice + 1 + advantages - disadvantages, 0)

    class_roll = Roll(num_dice=1, dice_size=class_die_size)

    if num_dice == 0:
        rolled_zero_pool = True

        non_class_roll = Roll(num_dice=1, dice_size=6)

        non_class_results, non_class_indices_to_remove, non_class_kept_results = non_class_roll.roll(cut_highest_first=rolled_zero_pool)
        class_results, class_indices_to_remove, class_kept_results = class_roll.roll(cut_highest_first=rolled_zero_pool)

        if class_results[0] <= non_class_results[0]: # Prioritise keeping the class die if there's a draw
            initial_keep_class = True
        else:
            initial_keep_class = False

        if difficulty > 0:
            remove_class = True
            remove_non_class = True
        else:
            remove_class = not initial_keep_class
            remove_non_class = initial_keep_class

        if remove_class:
            class_post_difficulty_indices_to_remove = [0]
            class_post_difficulty_kept_results = []
        else:
            class_post_difficulty_indices_to_remove = class_indices_to_remove
            class_post_difficulty_kept_results = class_kept_results

        if remove_non_class:
            non_class_post_difficulty_indices_to_remove = [0]
            non_class_post_difficulty_kept_results = []
        else:
            non_class_post_difficulty_indices_to_remove = non_class_indices_to_remove
            non_class_post_difficulty_kept_results = non_class_kept_results

    else:
        rolled_zero_pool = False

        non_class_roll = Roll(num_dice=num_dice, dice_size=6)

        non_class_results, non_class_indices_to_remove, non_class_kept_results = non_class_roll.roll(cut_highest_first=rolled_zero_pool)

        class_results, class_indices_to_remove, class_kept_results = non_class_roll.roll(cut_highest_first=rolled_zero_pool)

        if difficulty > 0:
            non_class_post_difficulty_indices_to_remove, non_class_post_difficulty_kept_results = Roll.cut_rolls(non_class_results, Cut(num=difficulty, threshold=4), highest_first=rolled_zero_pool)

            remaining_difficulty = len(non_class_post_difficulty_indices_to_remove) - difficulty

            class_post_difficulty_indices_to_remove, class_post_difficulty_kept_results = Roll.cut_rolls(class_results, Cut(num=remaining_difficulty, threshold=4), highest_first=rolled_zero_pool)
        else:
            non_class_post_difficulty_indices_to_remove = non_class_indices_to_remove
            non_class_post_difficulty_kept_results = non_class_kept_results

            class_post_difficulty_indices_to_remove = class_indices_to_remove
            class_post_difficulty_kept_results = class_kept_results

    return class_roll, class_results, class_post_difficulty_indices_to_remove, class_post_difficulty_kept_results, \
           non_class_roll, non_class_results, non_class_post_difficulty_indices_to_remove, non_class_post_difficulty_kept_results, \
           rolled_zero_pool

# TODO Crit fail notes
def format_classless_action(roll: Roll, results: List[int],  indices_to_remove: List[int],  kept_results: List[int], rolled_zero_pool: bool):
    roll_expression = roll.str_no_cut_drop()

    if roll.cut.num > 0:
        roll_expression += f' Difficulty {roll.cut.num}'

    lines = [
        roll_expression
    ]

    if rolled_zero_pool:
        lines.append('\nWe would have rolled zero dice, so we instead rolled two and took the lower.')

    formatted_results = DieGame.format_roll(results, indices_to_remove)

    results_expression = '{' + ', '.join(formatted_results) + '}'

    if roll.bonus > 0:
        results_expression += f' + {roll.bonus}'

    if roll.penalty > 0:
        results_expression += f' - {roll.penalty}'

    num_successes = len([result for result in kept_results if result >= DieGame.success_threshold])
    num_specials = len([result for result in kept_results if result >= DieGame.special_threshold])
    total = sum(kept_results) + roll.bonus - roll.penalty

    success_specials_expression = f'{num_successes} success'

    if num_successes != 1:
        success_specials_expression += 'es'

    if num_specials > 0:
       success_specials_expression += f', including {num_specials} {bold("Specials")}'

    total_expression = f' ({success_specials_expression}, total: {total})'

    results_expression += total_expression

    lines.append('\n' + results_expression)

    return '\n'.join(lines)

# TODO Crit fail notes
def format_class_die_action(
    non_class_roll: Roll,
    non_class_results: List[int],
    non_class_indices_to_remove: List[int],
    non_class_kept_results: List[int],

    class_roll: Roll,
    class_results: List[int],
    class_indices_to_remove: List[int],
    class_kept_results: List[int],

    rolled_zero_pool: bool,
    difficulty: int 
):
    roll_expression = non_class_roll.str_no_cut_drop() + class_roll.str_no_cut_drop()

    if difficulty > 0:
        roll_expression += f' Difficulty {difficulty}'

    lines = [
        roll_expression
    ]

    if rolled_zero_pool:
        lines.append('\nWe would have rolled zero dice, so we instead rolled 1d6 and the class die and took the lower.')

    lines.append('')

    overall_total = 0
    overall_num_successes = 0 
    overall_num_specials = 0
    
    roll_data = [
        (non_class_roll, non_class_results, non_class_indices_to_remove, non_class_kept_results),
        (class_roll, class_results, class_indices_to_remove, class_kept_results)
    ]
    
    for roll, results, indices_to_remove, kept_results in roll_data:
        formatted_results = DieGame.format_roll(results, indices_to_remove)

        results_expression = '{' + ', '.join(formatted_results) + '}'

        if roll.bonus > 0:
            results_expression += f' + {roll.bonus}'

        if roll.penalty > 0:
            results_expression += f' - {roll.penalty}'

        num_successes = len([result for result in kept_results if result >= DieGame.success_threshold])
        num_specials = len([result for result in kept_results if result >= DieGame.special_threshold])
        total = sum(kept_results) + roll.bonus - roll.penalty

        overall_total += total
        overall_num_successes += num_successes
        overall_num_specials += num_specials

        success_specials_expression = f'{num_successes} success'

        if num_successes != 1:
            success_specials_expression += 'es'

        if num_specials > 0:
           success_specials_expression += f', including {num_specials} {bold("Specials")}'

        total_expression = f' ({success_specials_expression}, total: {total})'

        results_expression += total_expression

        lines.append(results_expression)

    overall_results_expression = f'''
Total # Successes: {overall_num_successes}
Total # Specials: {overall_num_specials}'''

    lines.append(overall_results_expression)

    return '\n'.join(lines)

def roll_action(
    game: DieGame,
    username: str,
    stat: Literal['str', 'dex', 'con', 'int', 'wis', 'cha'],
    include_class_die: bool,
    advantages: int = 0,
    disadvantages: int = 0,
    difficulty: int = 0,
):
    if not hasattr(roll_action, 'a_an_map'):
        roll_action.a_an_map = {
            1: 'a',
            2: 'a',
            3: 'a',
            4: 'a',
            5: 'a',
            6: 'a',
            7: 'a',
            8: 'an',
            9: 'a',
            10: 'a',
            11: 'an',
            12: 'a',
            13: 'a',
            14: 'a',
            15: 'a',
            16: 'a',
            17: 'a',
            18: 'an',
            19: 'a',
            20: 'a'
        }

    # TODO character = game.get_character(username)

    base_num_dice = 3 # TODO character.get_stat(stat)

    if include_class_die:
        class_die_size = 8 # TODO character.get_class_die_size()

        class_roll, class_results, class_post_difficulty_indices_to_remove, class_post_difficulty_kept_results, \
        non_class_roll, non_class_results, non_class_post_difficulty_indices_to_remove, non_class_post_difficulty_kept_results, \
        rolled_zero_pool = class_die_roll(base_num_dice, class_die_size, advantages=advantages, disadvantages=disadvantages, difficulty=difficulty)

        return format_class_die_action(
            non_class_roll=non_class_roll,
            non_class_results=non_class_results,
            non_class_kept_results=non_class_post_difficulty_kept_results,
            non_class_indices_to_remove=non_class_post_difficulty_indices_to_remove,

            class_roll=class_roll,
            class_results=class_results,
            class_kept_results=class_post_difficulty_kept_results,
            class_indices_to_remove=class_post_difficulty_indices_to_remove,
            
            rolled_zero_pool=rolled_zero_pool,
            difficulty=difficulty
        )
    else:
        roll_made, results, indices_to_remove, kept_results, rolled_zero_pool = classless_roll(base_num_dice, advantages, disadvantages, difficulty)

        return format_classless_action(
            roll_made,
            results,
            indices_to_remove,
            kept_results,
            rolled_zero_pool,
        )

def roll_action(
    game: DieGame,
    username: str,
    stat: Literal['str', 'dex', 'con', 'int', 'wis', 'cha'],
    include_class_die: bool,
    advantages: int = 0,
    disadvantages: int = 0,
    difficulty: int = 0,
):
    if not hasattr(roll_action, 'a_an_map'):
        roll_action.a_an_map = {
            1: 'a',
            2: 'a',
            3: 'a',
            4: 'a',
            5: 'a',
            6: 'a',
            7: 'a',
            8: 'an',
            9: 'a',
            10: 'a',
            11: 'an',
            12: 'a',
            13: 'a',
            14: 'a',
            15: 'a',
            16: 'a',
            17: 'a',
            18: 'an',
            19: 'a',
            20: 'a'
        }

    character = game.get_character(username)

    num_dice = character.get_stat(stat)

    dice_size = 6

    num_dice += advantages

    class_die_result = None

    zero_dice_roll = False
    if num_dice - disadvantages <= 0: # TODO Handle the edge case where we have an equal stat and disadvantages, but class die is included.
        zero_dice_roll = True

    if zero_dice_roll:
        # TODO Strictly, you might not want to add your class die here because there's e.g. the chance of a Fool X, but that overcomplicates this edge case a lot.
        # TODO And probably isn't worth me supporting picking it, to be honest.

        if include_class_die and character.class_die_size >= 6:

            zero_dice_d6_roll = random.randint(1, dice_size)

            zero_dice_class_die_roll = random.randint(1, character.class_die_size)

            class_die_result = zero_dice_class_die_roll

            other_results = [min(zero_dice_d6_roll, class_die_result)]
        else:
            other_results = [min(random.randint(1, dice_size) for _ in range(2))]
    else:
        other_results = [random.randint(1, dice_size) for _ in range(num_dice - disadvantages)]

        if include_class_die:
            class_die_result = random.randint(1, character.class_die_size)

    if include_class_die:
        pre_difficulty_results = [* other_results, class_die_result]
    else:
        pre_difficulty_results = other_results

    indices_to_remove, kept_results = apply_difficulty(pre_difficulty_results, difficulty)

    if include_class_die:
        class_die_index = len(other_results)

        if class_die_index in indices_to_remove:
            class_die_removed = True
            indices_to_remove.remove(class_die_index)
        else:
            kept_results.pop(class_die_index)
            class_die_removed = False
    else:
        class_die_removed = False

    if zero_dice_roll:
        response = f'You rolled {num_dice - disadvantages} which means you rolled with 0 dice. We thus rolled twice and took the lowest.'

        if include_class_die:
            response += '\nBecause your class die was included in the roll, one of the rolled d6 included in that double roll, '
    else:
        response = f'You rolled {num_dice - disadvantages}'

        if include_class_die:
            response += f' and your class die ({character.class_die_size}) '

        response += ' for the following results:\n'

        formatted_results = DieGame.format_roll(other_results, indices_to_remove)

        num_successes = len([roll for roll in kept_results if roll >= 4])
        num_specials = len([roll for roll in kept_results if roll >= 6])

        response += f'{{{", ".join(formatted_results)}}} ({num_successes}'

        if num_specials > 0:
            response += f', {num_specials} of which were {bold("Specials")}'

        response += ')'

        response = bullet(response)

        if include_class_die:
            class_die_indices_to_remove = [0] if class_die_removed else []
            formatted_class_die_result = DieGame.format_roll([class_die_result], class_die_indices_to_remove)

            response += '\n' + bullet(f'You rolled {roll_action.a_an_map[class_die_result]} {formatted_class_die_result[0]} on your class die.')

            # TODO Special response for Fool, checking their flukes and fumbles?

            total_successes = num_successes + 1 if class_die_result >= 4 else num_successes
            total_specials = num_specials + 1 if class_die_result >= 6 else num_specials

            response += f'\n\nTotal number of successes: {total_successes}'

            if total_specials >= 1:
                response += f', {total_specials} of which were Specials.'''

    return response

# TODO
"""
[Disadvantages] If the resulting dice pool would include no dice, roll two dice and pick the lowest. 
If the character is able to add a class dice to a pool, they may include their class dice instead of one of the two dice.

The player removes a number of successes from the rolled dice pool equal to the task’s difficulty. 
If there are more successes than the difficulty, they can choose which ones to remove.
"""

def get_simple_roll_results_old(rolls: List[Roll]):
    overall_total = 0
    all_results = []
    all_kept_results = []
    all_indices_to_remove = []

    for index, roll in enumerate(rolls):
        results = []
        kept_results = []
        indices_to_remove = []

        if (roll.num_dice - roll.drop) > 0:
            for i in range(roll.num_dice - roll.drop):
                result = random.randint(1, roll.dice_size)

                results.append(result)

            if roll.cut > 0:
                sorted_results = sorted(enumerate(results), key=lambda r: r[1])

                for remove_index, roll_to_remove in sorted_results[- roll.cut:]:
                    indices_to_remove.append(remove_index)

                kept_results = [value for index, value in enumerate(results) if index not in indices_to_remove]

                if len(kept_results):
                    num_successes = len([value for value in kept_results if value >= 4])
                else:
                    num_successes = 0
            else:
                kept_results = results

            total = sum(kept_results) + roll.bonus - roll.penalty
        else:
            total = 0

        overall_total += total
        all_results.append(results)
        all_kept_results.append(kept_results)
        all_indices_to_remove.append(indices_to_remove)

    return all_results, all_kept_results, all_indices_to_remove, num_successes, total

def simple_roll(rolls: List[Roll], note: Optional[str] = None):

    # TODO Finish this
    # TODO Maybe worth having specific commands for each Paragon die, as well as a simple action one?

    results, kept_results, indices_to_remove, num_successes, total = get_simple_roll_results(rolls)

    all_formatted = []
    overall_total = 0
    rolled_expression_tokens = []
    all_results_expressions = []

    total_num_dice_rolled = len(results)
    for index, roll in enumerate(rolls):

        formatted_rolls = DieGame.format_roll(results, indices_to_remove, effective_highest)

        total = sum(kept_results) + roll.bonus - roll.penalty

        expression = str(roll) if index == len(rolls) - 1 else roll.str_no_cut_drop()

        rolled_expression_tokens.append(expression)

        results_expression = '{' + ', '.join(formatted_rolls) + '}'

        if roll.bonus > 0:
            results_expression += f' + {roll.bonus}'

        if roll.penalty > 0:
            results_expression += f' - {roll.penalty}'

        total_expression = f' (Total: {total})' if total_num_dice_rolled > 1 else ''
        results_expression += f' = **{effective_highest + roll.bonus - roll.penalty}**{total_expression}'

        all_results_expressions.append(results_expression)

        all_formatted.append(formatted_rolls)
        overall_total += total

    rolled_expression = ', '.join(rolled_expression_tokens)

    note_expression = f'{quote(note)}\n\n' if note is not None and len(note.strip()) else ''

    response = f'''{note_expression}You rolled {rolled_expression}: '''

    if len(all_results_expressions) > 1:
        response += '\n'

    for results_expression in all_results_expressions:
        if len(all_results_expressions) > 1:
            response += '* '

        response += results_expression

        if len(all_results_expressions) > 1:
            response += '\n'

    if len(all_results_expressions) > 1:
        response += f'**Overall Total**: {overall_total}'

    return response

def unlink(overcharge: Overcharge, guild_id: int):
    if guild_id in overcharge.games:
        overcharge.remove_game(guild_id)

        return 'Unlinked! You can re-link by using /link.'
    else:
        return 'No game to unlink.'

def link(overcharge: Overcharge, guild_id: int, spreadsheet_url: str):
    if guild_id in overcharge.games:
        return 'Game already linked.'

    game = overcharge.create_game(
        guild_id=guild_id,
        spreadsheet_url=spreadsheet_url
    )

    response = "Linked to character tracker."

    if len(game.character_sheets):
        for discord_username, character_sheet in game.character_sheets.items():
            response += f'\n* Linked "{discord_username}" to character "{character_sheet.character_name}"'
    else:
        response += f'\nNo characters linked yet, you can do so via the {code("/add_character")} command.'

    return response
