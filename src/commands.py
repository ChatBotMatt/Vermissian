import discord
from typing import Iterable, List

from src.Game import CharacterKeeperGame
from src.utils.format import bold, underline, code, bullet, strikethrough

# TODO Add Hammertime stuff? There's no API or calendar input, so tricky.

# In order of preference in responding
BOT_USER_IDS = { # TODO Better place for this
    'Vermissian': 1218843847392493588,
    'Ghost Detector': 1253066078456909885,
    'Astir': 1299839991031140522
}

def should_respond(bot_name: str, members: List[discord.Member]):
    for current_bot, bot_uid in BOT_USER_IDS.items():
        is_in_channel = any(member.id == bot_uid for member in members)

        if is_in_channel:
            return current_bot == bot_name

    return True

def get_donate():
    return f'You can find my Ko-Fi here: https://ko-fi.com/jaffa674059. All donations are really appreciated, thank you!'

def get_privacy_policy():
    message = f'''Hi, welcome to the privacy policy! I'm a little (happily) surprised anyone is reading this.

When you use the bot, I keep a log of any commands you input (and the bot's responses), including ones in the format "roll 3d6 [...]" and any parameters to the commands, for debugging purposes. This logging includes your username, the name and ID of the server that the command was sent in, and a timestamp. 

What this means, practically: 

{bullet("No, I'm not reading all of your messages. The bot reads them and then immediately forgets them (except rolls). Your secrets are safe.")} 

{bullet("If you link the bot to a character keeper, that link (as with any command parameters) is logged which means that in theory, I can go and look at it. I have no real interest in doing so.")}

{bullet("No, I do not share this data with anyone.")} 

If you're wondering how I make money off of this, or if you're the product, then rest assured - I don't make any money off it and it's legitimately just a free, useful (I hope) service. It's pretty cheap to run and it was fun to make. 

That being said, if you'd like to {code("/donate")} to me, it's always appreciated - "cheap" isn't "free" and I did put a lot of time and effort into the bot. 

If you want to verify any of this, please check out the source code on GitHub: https://github.com/ChatBotMatt/Vermissian

The logging function is in utils/logger.py specifically, and you can look for anything using {code("get_logger()")}. 

If you have any other questions or concerns, and {code("/help")} doesn't cover them, feel free to message me on Discord.'''

    return message

def get_commands_page_content(all_commands: Iterable[discord.ApplicationCommand]):
    commands_message = ''

    command_tokens = []
    for command in all_commands:
        command_tokens.append(
            f'{code("/" + command.qualified_name)} - {command.description if hasattr(command, "description") else "[No description given]"}')

    commands_message += '* ' + '\n* '.join(command_tokens)

    commands_message += '\n\nYou can also do freeform rolls by typing "roll" followed by dice, each in the form "XdY [+-] Z" and separated by commas. E.g. "roll 5d6 + 2, 3d8 -1" will roll two sets of dice with different bonuses/penalties. Add "Difficulty Z" to the end of it, where Z is 1 or 2, to remove that many of the highest dice first.'

    return 'Available Commands', commands_message

def get_character_list(game: CharacterKeeperGame):
    if len(game.character_sheets) == 0:
        message = 'No characters linked. You can use /add_character to do this.'
    else:
        tokens = []

        for discord_username, character in game.character_sheets.items():
            character_name = '[Unnamed]' if character.character_name is None else character.character_name
            tokens.append(f'* {character_name} is linked to {character.discord_username} under sheet "{character.sheet_name if character.sheet_name else "no sheet"}"')

        message = '\n'.join(tokens)

    message = message[:2000]

    return message

def help_roll():
    four_d_ten_results = [4, 6, 7, 2]
    four_d_ten_results_cut = [4, 6, strikethrough(7), 2]
    four_d_ten_results_drop = four_d_ten_results[:-1]
    four_d_ten_results_drop_cut = four_d_ten_results_cut[:-1]

    four_d_ten_results_cut = str(four_d_ten_results_cut).replace("'", "")
    four_d_ten_results_drop_cut = str(four_d_ten_results_drop_cut).replace("'", "")

    three_d_six_results = [1, 5, 3]
    three_d_six_results_cut = [1, strikethrough(5), 3]
    three_d_six_results_drop = three_d_six_results[:-1]

    three_d_six_results_cut = str(three_d_six_results_cut).replace("'", "")

    help_components = f'''Individual roll expressions should be separated with {code("+")}, {code("-")}, {code(",")}, or a space.

All of the below is not case-sensitive - capitalisation {bold("doesn't")} matter. 

{underline("Individual roll components")}
These are applied on the level of an individual roll expression, e.g. to {code('3d6')} in {code('3d6 + 1, 1d8')}.

{bullet(code("3d8") + f" - The dice to roll. Should be in the form {code('XdY')} where X is the number of dice to roll and Y is how many sides they have. E.g. {code('3d8')} rolls three 8-sided dice.")}
{bullet(code("+X") + " or " + code("-X") + f" where X is an integer. Adds or subtracts that much from the previous roll. E.g. {code('3d6 + 2 - 3')}")}

{underline("Global roll components")}
These are applied on the level of {bold("all")} of the rolls, e.g. to both {code('3d6')} and {code('1d8')} in {code('3d6, 1d8 Cut 1')}. 

{bullet(code("Drop X") + f" where X is an integer. Removes X dice from each pool before rolling.E.g. {code('3d6, 2d8 drop 1')} will roll {bold('2')}d6 and {bold('1')}d8. Essentially, it's Spire Difficulty.")}
{bullet(code("Cut X") + f" where X is an integer. Rolls the dice, then removes X of the highest values from each set of rolled dice. E.g. {code('3d6, 2d8 cut 1')} will roll 3 dice and remove the highest from that pool, then do the same for the 2d8 pool. Essentially, it's Heart Difficulty.")}
{bullet(code("# Some Comment") + f" or {code('? Some Comment')} " + f" adds a note to the roll, e.g. to indicate what it's for. E.g. {code('3d6 ? Roll to kill the hydra')}")}

Each roll will have its highest value highlighted, and its total.'''

    help_examples = f'''{bullet(code("roll 4d10") + f"- Rolls 4d10. {bold('Example results:')} {{ {four_d_ten_results} }}")}
{bullet(code("roll 4d10, 3d6") + f"- Rolls 4d10 and 3d6. {bold('Example results:')} {{ {four_d_ten_results}, {three_d_six_results} }}")}
{bullet(code("roll 4d10, 3d6 Drop 1") + f"- Rolls {bold('3')}d10 and {bold('2')}d6, one dice dropped from each initial pool of dice. {bold('Example results:')} {{ {four_d_ten_results_drop}, {three_d_six_results_drop} }}.")}
{bullet(code("roll 4d10, 3d6 Cut 1") + f"- Rolls 4d10 and 3d6, removing the highest rolled result from each. {bold('Example results:')} {{ {four_d_ten_results_cut}, {three_d_six_results_cut} }}.")}
{bullet(code("roll 4d10 Drop 1 Cut 1") + f"- Rolls {bold('3')}d10 and removing the highest rolled result. {bold('Example results:')} {{ {four_d_ten_results_drop_cut} }}.")}
{bullet(code("roll 4d10 + 3") + f"- Rolls 4d10 and adds 3 to the {bold('total')} and {bold('highest')} value of the 4d10 rolled. {bold('Example results:')} {{ {four_d_ten_results} + 3 }}.")}
{bullet(code("roll 4d10 + 3, 3d6") + f"- Rolls 4d10 and adds 3 to the {bold('total')} and {bold('highest')} value of the 4d10 rolled, but {bold('not')} to the 3d6. {bold('Example results:')} {{ {four_d_ten_results} + 3, {three_d_six_results} }}.")}
{bullet(code("roll 4d10 - 3") + f"- Rolls 4d10 and subtracts 3 from the {bold('total')} and {bold('highest')} value rolled. {bold('Example results:')} {{ {four_d_ten_results} - 3 }}.")}
{bullet(code("roll 4d10 ? Seduce the Angel") + f"- Rolls 4d10 adds the given note (everything after {code('#')} or {code('?')}) to it")}. {bold('Example results:')} (Roll to compel the Angel not to murder us) {{ {four_d_ten_results} }}'''

    return [
        ('Components', help_components),
        ('Examples', help_examples)
    ]