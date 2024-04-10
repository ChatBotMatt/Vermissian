import discord
from discord.ext.pages import Page, Paginator

import json
import random
import os
import glob
import functools
import re
from typing import List, Tuple, Dict, Optional, Callable, Set, Union, Literal

from Vermissian import Vermissian
from Game import Game, SpireGame, HeartGame
from System import System
from CharacterSheet import SpireCharacter, SpireSkill, SpireDomain, HeartCharacter, HeartSkill, HeartDomain
from Roll import Roll
from utils.format import bold, underline, code, quote, bullet, spoiler
from utils.logger import get_logger
from utils.exceptions import VermissianError, NoCharacterError, NoGameError, WrongGameError
from extract_abilities import Ability

intents = discord.Intents.default()
intents.message_content = True

vermissian = Vermissian(intents=intents)

random.seed(42) # TODO Temporary for testing purposes

logger = get_logger()

spire_skills = [skill.value for skill in SpireSkill]
spire_domains = [domain.value for domain in SpireDomain]

heart_skills = [skill.value for skill in HeartSkill]
heart_domains = [domain.value for domain in HeartDomain]

heart_difficulties = list(HeartGame.DIFFICULTIES.keys())

def error_responder_decorator(command: Callable):
    @functools.wraps(command)
    async def wrapper(ctx: discord.ApplicationContext, *args, **kwargs):
        try:
            return await command(* args, ctx=ctx, ** kwargs)
        except VermissianError as e:
            logger.error(e, exc_info=True)
            await ctx.respond(f'Error: {str(e)}')
        except Exception as e:
            logger.error(e, exc_info=True)
            await ctx.respond(f'An error was encountered. Please try the debugging steps in /help. Sorry!')

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
        if not ctx.user.name in vermissian.games[ctx.guild_id].character_sheets:
            raise NoCharacterError()

        return await command(*args, ctx=ctx, **kwargs)

    return wrapper

def get_credits():
    message = '''The Vermissian dice bot is a project by jaffa6.

    The following people helped test it, and are responsible for making it a lot nicer to work with!'''

    testers = [
        'yuriAza',
        'SavvyWolf, who you can find at https://savvywolf.scot/'
    ]

    tester_components = []

    for tester in testers:
        tester_components.append(tester)

    message += f'\n{bullet("")}' + '\n'.join(bullet(tester) for tester in testers)

    message += '''\n\nSpire is copyright Rowan, Rook and Decard. You can find out more and support these games at rowanrookanddecard.com and you can find Spire at https://rowanrookanddecard.com/product/spire-rpg/

    Heart is copyright Rowan, Rook and Decard. You can find out more and support these games at rowanrookanddecard.com and you can find Heart at https://rowanrookanddecard.com/product/heart-the-city-beneath-rpg/

    ichor-drowned, which the Delve Draws mechanic is from, is a product of Sillion L and Brendan McLeod. It can be found at https://sillionl.itch.io/ichor-drowned.'''

    return message

@vermissian.slash_command(name='credits', description='Get the credits', guilds=[discord.Object(1218845257899446364), discord.Object(1193578278175375432)])
@command_logging_decorator
@error_responder_decorator
async def credits_command(
    ctx: discord.ApplicationContext,
):
    message = get_credits()

    await ctx.respond(message, ephemeral=True)

def get_about():
    message = f'''For legal info, see {code("/legal")}.

This is an unofficial dice bot, designed for Spire and Heart, by jaffa6. 

You can find a list of available commands by using {code("/help")}. 

The dice bot pulls data from character trackers (Spire) <https://docs.google.com/spreadsheets/d/1saogmy4eNNKng32Pf39b7K3Ko4uHEuWClm7UM-7Kd8I/edit?usp=sharing> or (Heart) <https://docs.google.com/spreadsheets/d/1PzF3ZHQpXXaS0ci0Q0vbE9uHpC26GiUJ4ishIbbcpOY/edit?usp=sharing> which you can copy and add your own characters to.

It does require a fixed structure in the tracker, so please don't move stuff around in them or it might not work properly for you.

You can link to a character tracker via "{code("/link")}" and add characters via "{code("/add_character")}".

Outside of the trackers, you can also use it for freeform rolling by typing stuff like "{code("roll 3d6" or "roll 4d2 + 5 - 2, 3d7 + 21")}" 

The Vermissian dice bot is an independent production by jaffa6 (me) and is not affiliated with Rowan, Rook and Decard. It is published under the RR&D Community License.

Spire is copyright Rowan, Rook and Decard. You can find out more and support these games at rowanrookanddecard.com and you can find Spire at https://rowanrookanddecard.com/product/spire-rpg/.

Heart is copyright Rowan, Rook and Decard. You can find out more and support these games at rowanrookanddecard.com and you can find Heart at https://rowanrookanddecard.com/product/heart-the-city-beneath-rpg/.

ichor-drowned is a product by Sillion L and Brendan McLeod, with whom I'm not affiliated, but they've generously allowed me to include their content here. You can buy it here: https://sillionl.itch.io/ichor-drowned'''

    return message

@vermissian.slash_command(name='about', description='Get info about the bot.', guilds=[discord.Object(1218845257899446364), discord.Object(1193578278175375432)])
@command_logging_decorator
@error_responder_decorator
async def about_command(
    ctx: discord.ApplicationContext,
):
    message = get_about()

    await ctx.respond(message, ephemeral=True)

def get_legal():
    return '''The Vermissian dice bot is an independent production by jaffa6 (me) and is not affiliated with Rowan, Rook and Decard. It is published under the RR&D Community License.
    
Spire is copyright Rowan, Rook and Decard. You can find out more and support these games at rowanrookanddecard.com and you can find Spire at https://rowanrookanddecard.com/product/spire-rpg/

Heart is copyright Rowan, Rook and Decard. You can find out more and support these games at rowanrookanddecard.com and you can find Heart at https://rowanrookanddecard.com/product/heart-the-city-beneath-rpg/

ichor-drowned is a product of Sillion L and Brandan McLeod, with whom I'm not affiliated, but they've generously allowed me to include their content here. You can buy it here: https://sillionl.itch.io/ichor-drowned'''

@vermissian.slash_command(name='legal', description='Get the legal information.', guilds=[discord.Object(1218845257899446364), discord.Object(1193578278175375432)])
@command_logging_decorator
@error_responder_decorator
async def legal_command(
    ctx: discord.ApplicationContext,
):
    message = get_legal()

    await ctx.respond(message)

def get_donate():
    return f'You can find my Ko-Fi here: https://ko-fi.com/jaffa674059. All donations are really appreciated, thank you!'

@vermissian.slash_command(name='donate', description='Get a link to donate to me as a thank you.', guilds=[discord.Object(1218845257899446364), discord.Object(1193578278175375432)])
# This command isn't logged because that would feel creepy
@error_responder_decorator
async def donate_command(
    ctx: discord.ApplicationContext,
):
    message = get_donate()

    await ctx.respond(message)

def log_suggestion(username: str, suggestion: str):
    with open('user_suggestions.log', 'a', encoding='utf-8') as f:
        f.write(f'Suggestion from {username}: ' + suggestion[:5000] + '\n')

    return f'Thanks for the suggestion! Please note that not everything is feasible (especially for a free bot) and it can be difficult to predict what\'s easy or hard to do. <https://xkcd.com/1425/> That being said, I really do appreciate your interest, and I read every suggestion!'

@vermissian.slash_command(name='suggest', description='Have a suggestion to improve the bot? Let me know!', guilds=[discord.Object(1218845257899446364), discord.Object(1193578278175375432)])
@command_logging_decorator
@error_responder_decorator
async def suggest_command(
    ctx: discord.ApplicationContext,
    suggestion: str,
):
    response = log_suggestion(ctx.user.name, suggestion)

    await ctx.respond(response)

def get_privacy_policy():
    message = f'''Hi, welcome to the privacy policy! I'm a little (happily) surprised anyone is reading this.

When you use the bot, I keep a log of any commands you input (and the bot's responses), including ones in the format "roll 3d6 [...]" and any parameters to the commands, for debugging purposes. 

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

@vermissian.slash_command(name='privacy', description='Describes what happens to your data when using the bot (nothing bad).', guilds=[discord.Object(1218845257899446364), discord.Object(1193578278175375432)])
@command_logging_decorator
@error_responder_decorator
async def privacy_policy_command(
    ctx: discord.ApplicationContext,
):
    message = get_privacy_policy()

    await ctx.respond(message)

def get_getting_started_page_content():
    getting_started_message = f'''To get started, use {code("/link")} to link the bot to your character tracker. It will automatically try to link users to characters. 

This will work best if you have already filled characters in.

The bot does not currently support multiple games being run in the same server - {code("/link")}ing one character tracker will overwrite the previous one.

You can also run {code("/add_character")}, passing in the URL for your specific tab on the character tracker, to link your own character to yourself. You can only have one character per user at once.'''

    return 'Getting Started', getting_started_message

def get_commands_page_content():
    commands_message = ''

    command_tokens = []
    for command in vermissian.walk_application_commands():
        command_tokens.append(
            f'{code("/" + command.qualified_name)} - {command.description if hasattr(command, "description") else "[No description given]"}')

    commands_message += '* ' + '\n* '.join(command_tokens)

    commands_message += '\n\nYou can also do freeform rolls by typing "roll" followed by dice, each in the form "XdY [+-] Z" and separated by commas. E.g. "roll 5d6 + 2, 3d8 -1" will roll two sets of dice with different bonuses/penalties. Add "Difficulty Z" to the end of it, where Z is 1 or 2, to remove that many of the highest dice first.'

    return 'Available Commands', commands_message

def get_debugging_page_content():
    debugging_message = f'If the bot doesn\'t appear to be working properly, please try these things in order, and **if** none of those fix it then message jaffa6 on Discord with a screenshot and a description of the problem ("What went wrong? What did you expect to happen?"):'

    fix_steps = [
        'Ensure that your character tracker is up-to-date enough for the bot to work with it. It should have the "Discord Username" field in the character sheets and if it doesn\'t, it\'s not compatible.',
        'Ensure that your character tracker\'s structure is identical to the master one located at (Spire) <https://docs.google.com/spreadsheets/d/1saogmy4eNNKng32Pf39b7K3Ko4uHEuWClm7UM-7Kd8I/edit?usp=sharing> or (Heart) <https://docs.google.com/spreadsheets/d/1PzF3ZHQpXXaS0ci0Q0vbE9uHpC26GiUJ4ishIbbcpOY/edit?usp=sharing> - if you move things around, or add new rows or columns that reposition stuff, it\'ll probably stop reading it correctly!',
        'Wait a minute or so, then try again.'
    ]

    debugging_message += '\n\n' + '\n'.join(bullet(step) for step in fix_steps)

    return 'Fixing Errors', debugging_message

@vermissian.slash_command(name='help', description='Provides help text.', guilds=[discord.Object(1218845257899446364), discord.Object(1193578278175375432)])
@command_logging_decorator
@error_responder_decorator
async def help_command(
    ctx: discord.ApplicationContext,
):

    raw_pages = [
        get_getting_started_page_content(),
        get_commands_page_content(),
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
            page_content += f'\n\nNext: {headers[page_index + 1]}'

        pages.append(Page(content=page_content, embeds=[]))

    paginator = Paginator(pages)

    await paginator.respond(ctx.interaction, ephemeral=True)

def get_character_list(guild_id: int):
    game = vermissian.games[guild_id]

    if len(game.character_sheets) == 0:
        message = 'No characters linked. You can use /add_character to do this.'
    else:
        tokens = []

        for discord_username, character in game.character_sheets.items():
            character_name = '[Unnamed]' if character.character_name is None else character.character_name
            tokens.append(f'* {character_name} is linked to {character.discord_username} under {character.sheet_name}')

        message = '\n'.join(tokens)

    message = message[:2000]

    return message

@vermissian.slash_command(name='list', description='Lists existing characters and the character tracker they\'re connected to.', guilds=[discord.Object(1218845257899446364), discord.Object(1193578278175375432)])
@command_logging_decorator
@error_responder_decorator
@guild_required_decorator
async def list_characters_command(
    ctx: discord.ApplicationContext,
):
    message = get_character_list(ctx.guild_id)

    await ctx.respond(message)

@functools.lru_cache()
def get_tag(guild_id: int, tag: str):
    if not hasattr(get_tag, 'lowercase_spire_tags'):
        get_tag.lowercase_spire_tags = {name.lower(): value for name, value in SpireGame.TAGS.items()}

    if not hasattr(get_tag, 'lowercase_heart_tags'):
        get_tag.lowercase_heart_tags = {name.lower(): value for name, value in HeartGame.TAGS.items()}

    lowercase_tag = tag.lower()

    matches = {}

    if lowercase_tag in get_tag.lowercase_spire_tags:
        matches[System.SPIRE.value] = get_tag.lowercase_spire_tags[lowercase_tag]

    if lowercase_tag in get_tag.lowercase_heart_tags:
        matches[System.HEART.value] = get_tag.lowercase_heart_tags[lowercase_tag]

    if guild_id in vermissian.games:
        game = vermissian.games[guild_id]

        if game.system.value in matches:
            message = f'{bold(tag)}: {matches[game.system.value]}'
        else:
            message = f'Cannot find tag "{tag}" for {game.system.value.title()}!'
    elif len(matches):
        message = ''

        for system, description in matches.items():
            message += f'* [{system.title()}] {bold(tag)}: {description}\n'
    else:
        message = f'Cannot find tag "{tag}"'
        logger.warning(f'Unknown tag: "{tag}" searched for.')

    if len(message) > 2000:
        message = 'The tag description is very long so some of it is cut off.\n\n' + message

    message = message[:2000]

    return message

@vermissian.slash_command(name='tag', description='Describes a given resource or equipment tag', guilds=[discord.Object(1218845257899446364), discord.Object(1193578278175375432)])
@command_logging_decorator
@error_responder_decorator
async def tag_command(
    ctx: discord.ApplicationContext,
    tag: discord.Option(str, "The tag to describe"),
):
    message = get_tag(ctx.guild_id, tag)

    await ctx.respond(message)

def format_ability(ability_to_format: Ability, system: Optional[str] = None) -> str:
    system_str = f'{system.title()}, ' if system else ''

    quoted_description = '\n'.join(quote(line) for line in ability_to_format.description.split('\n'))

    formatted = f'[{system_str}{ability_to_format.class_calling}] {bold(ability_to_format.name)}:\n\n{quoted_description}\n\n[{ability_to_format.tier} advance, {ability_to_format.source}]'

    return formatted

@functools.lru_cache(maxsize=200)
def get_ability(guild_id: int, ability: str):
    if not hasattr(ability_command, 'abilities'):
        with open('all_abilities.json', 'r', encoding='utf-8') as f:
            abilities: Dict[str, Dict[str, Ability]] = {
                system: {
                    name: Ability.from_json(raw_ability) for name, raw_ability in ability_data.items()
                } for system, ability_data in json.load(f).items()
            }

            ability_command.abilities = abilities

    ability_to_use = ability.replace('(base)', '').strip()

    ability_to_use = re.sub(' - .+', '', ability_to_use)

    lower_ability_to_use = ability_to_use.lower()

    if guild_id in vermissian.games:
        game = vermissian.games[guild_id]

        system_abilities: Dict[str, Ability] = ability_command.abilities[game.system.value]

        if lower_ability_to_use in system_abilities:
            found_ability = system_abilities[lower_ability_to_use]

            message = format_ability(found_ability, system=None)
        else:
            message = f'Cannot find ability "{ability_to_use}" for {game.system.value.title()}!'
    else:
        message = ''

        found_abilities = {}

        for system, system_abilities in ability_command.abilities.items():
            if lower_ability_to_use in system_abilities:
                found_ability = system_abilities[lower_ability_to_use]

                found_abilities[system] = found_ability

        if len(found_abilities):
            for system_index, (system, found_ability) in enumerate(found_abilities.items()):
                divider_text = '\n------------\n' if len(found_abilities) > 1 and system_index < len(
                    found_abilities) - 1 else ''

                message += f'{format_ability(found_ability, system)}{divider_text}'
        else:
            message = f'Cannot find ability "{ability_to_use}"'
            logger.warning(f'Unknown ability: "{ability}" searched for.')

    if len(message) > 2000:
        message = 'The abilities are very long so some of it is cut off\n\n' + message

    message = message[:2000]

    return message

@vermissian.slash_command(name='ability', description='Describes a given ability', guilds=[discord.Object(1218845257899446364), discord.Object(1193578278175375432)])
@command_logging_decorator
@error_responder_decorator
async def ability_command(
    ctx: discord.ApplicationContext,
    ability: discord.Option(str, "The ability to describe"),
):
    message = get_ability(ctx.guild_id, ability)

    await ctx.respond(message)

@functools.lru_cache()
def get_full_card_name(card_value: Union[int, str], suit: str):
    return f'{card_value} of {suit}s'

def pick_delve_draw_card(already_picked: Set[str]) -> Tuple[str, Dict[str, Union[str, List[str]]]]:
    if not hasattr(pick_delve_draw_card, 'cards'):
        pick_delve_draw_card.cards = {
            'Heart': {
                'Ace': {
                    'name': 'Flesh',
                    'values': [
                        'Caverns like blood vessels, threatening to flood.',
                        'A great kraken of flesh, overeager for friends.',
                        'An old battlefield; the bodies blooming with strange life.',
                        'Cages of sharp bones, picked clean.',
                        'Roving Hungry Deep disciples search for sacrifices.',
                        'A great device scours the tunnels, keeping things clean.'
                    ]
                },
                2: {
                    'name': 'A familiar Demon, resurfaced',
                    'values': [
                        'A sprawling lake, haunted by an uncouth Rabisu.',
                        'A jaunty Incarnadine or three with an interest in your debt.',
                        'Your old nemesis, back from the grave.',
                        'A squad of Hounds, convinced of your crimes.',
                        'A Gnoll incursion team, desperate not to be found.',
                        'An occultist’s burnt-out shrine, still smoldering.'
                    ],
                },
                3: {
                    'name': 'A Gutterkin\'s folly',
                    'values': [
                        'A wretched marketplace with even more wretched deals.',
                        'A throne of rust in a kingdom of trash.',
                        'A caravan of Gutterkin pirates, eager for riches.',
                        'Slave-drovers armed with barbed whips.',
                        'A princely estate, overgrown with green.',
                        'A font of spireblack, free-flowing.'
                    ],
                },
                4: {
                    'name': 'A cosmic lovers\' Quarrel slips in from beyond the veil',
                    'values': [
                        'Two differently-Domained passageways vie for the same place in reality',
                        'Rips in space carry infectious arguing; all who hear it begin bickering',
                        'A pair of dragons, fighting, threaten to bring the catacombs down',
                        'A river-barge of traveling Elsewhere nobles, voices polite, dripping with hatred',
                        'Witch-thralls hunt for a neutral party to judge a deeply esoteric disagreement',
                        'A rain of arrows, shooting from the sky itself, as you cross the meadow.'
                    ]
                },
                5: {
                    'name': 'A dead Foundry of a dead world, untouched',
                    'values': [
                        'An inscrutable factory, its workers alive but frozen in a single moment',
                        'The massive hammer of an old god, still red-hot from its last use',
                        'A graveyard of gears and sprockets, all turning listlessly, producing nothing',
                        'Bees, building an new enclave of wyrd and wax, intent on protecting it from you',
                        'The Labyrinth sickness spreads, with new walls and alleys taking shape',
                        'Haven-exiles on the search for a home and a leader.'
                    ]
                },
                6: {
                    'name': 'A Rot',
                    'values': [
                        'Warrens, heady with corruption and decay',
                        'Pilgrims returning from the God of Corpses, their garments filthy',
                        'A marsh of Ichor; sinkholes filled with mad dreams',
                        'A meticulous Doctor insists on analyzing your humours',
                        'A hot spring, occupied by a territorial Heartsblood hippopotamus',
                        'Clinically-bare walls filled with the hum of machines.'
                    ]
                },
                7: {
                    'name': 'A deeply, deeply entangled Pair',
                    'values': [
                        'Enormous eels, enmeshed, electrified, tumbling right towards you',
                        'A swarm of Harpies in the middle of ravenous mating',
                        'A sleepless Deadwalker and her visible, joyous death, following behind',
                        'A fae warden of the wilds, intent on playing pranks',
                        'A mated pair of Heartsblood mustangs, on the prowl',
                        'Signal-box cultists welded together, speaking as one (if you can call that speaking).'
                    ]
                },
                8: {
                    'name': 'An Engine Room to an unseen machine',
                    'values': [
                        'Leftover Vermissian mechanisms',
                        'Are they fleeing, or invading? An Aelfir-sponsored prototakos device, long abandoned',
                        'Is it dangerous? A single Apiarist guards this listening post',
                        'What do they hear? A junkyard, filled with junk, and hungry junkyard dogs',
                        'This train crashed long, long ago—and it is still crashing',
                        'The Works, as seen in Spire. What’s it doing down here?'
                    ]
                },
                9: {
                    'name': 'The Abyss',
                    'values': [
                        'The ichor is up to your chest, here. Up to your chin. You can taste it',
                        'An unlit passage, carved in rock, and without clear steps',
                        'The only path ahead lies into the maw of this sleeping godwhale',
                        'The river’s not that deep. We can ford across no problem. Right?',
                        'A towering hill. You could go around, but... someone is up there, waving.',
                        'An elevator. The doors open for you. It only goes down.'
                    ]
                },
                10: {
                    'name': 'The Chamber Awakes: Intelligence in the Walls',
                    'values': [
                        'You’ve entered a device; its gears and walls and devices activate all around you.',
                        'A valley of miners, digging technology from out of the rock.',
                        'Bees. Bees. Bees. Bees. Bees.',
                        'A Signal-Box cultist parade.',
                        'An Automaton-of-Burden, aware and desperate for a purpose.',
                        'BEES BEES BEES BEES BEES'
                    ]
                },
                'Jack': {
                    'name': 'A Vermissian Incursion',
                    'values': [
                        'Someone you know, but from another reality, is on the run. Who?',
                        'You, but from another reality, looking for you. Why?',
                        'Vermissian Sages, looking for you, with innumerable (seemingly inane) questions.',
                        'Someone you know from another reality appears, on the run. Who?',
                        'You, from another reality, looking for you. Why?',
                        'A perfectly-working train crossing that signals the passage of the Grail Road.'
                    ]
                },
                'Queen': {
                    'name': 'The Moon\'s Light peeks through the cracks',
                    'values': [
                        'From the Depths, a funeral: The smell of kelp and the sounds of eulogies.',
                        'From the aetherships, a fight club: The glint of ship-steel and the crunch of Pugilists’ bones.',
                        'From the Red Moon, a ritual: the smell of copper and the screams of saints.',
                        'A Paladin from the City Above, come to cleanse this wicked realm.',
                        'A broken-down shrine to the Moon Beneath, laid waste by her enemies.',
                        'The corpse of a Drow, face frozen in fear. In their hand, a note with your name on it.'
                    ]
                },
                'King': {
                    'name': 'The Angel Comes',
                    'values': [
                        'A haven in turmoil. A shriek of red. It is already too late.',
                        'A beast that should not be. A warrior of iron. A battle of titans.',
                        'A mighty egg of viscera; the angel will emerge presently.',
                        'The Hounds, ready for a desperate last stand.',
                        'A Cleaver, intent on ascension to their most holy form.',
                        'A great, gaping hole. It leads two Tiers down. It does not lead back up.'
                    ]
                }
            },
            'Club': {
                'Ace': {
                    'name': 'Soul',
                    'values': [
                        'A forest with trees dipping in ichor: Each puddle whispers a curse.',
                        'A Godsbeast’s grave, and its manic attendants.',
                        'A trio of Deadwalkers, bound by a singular, mighty death.',
                        'An entire settlement is dead— but still hustling and bustling, in ghostly fashion.',
                        'Ghost wardens search for prey with wands of electrical power.',
                        'A loved one returns from the grave to issue a dire warning.'
                    ]
                },
                2: {
                    'name': 'A pleasant Grove, closely guarded',
                    'values': [
                        'Druids, looking for greener pastures, not keen on competition.',
                        'Seven deep-goats stare silently, waiting for tribute.',
                        'A Cleaver Lord has marked this as her private hunting ground.',
                        'An intoxicating species of flora lives here; wandering through causes stumbling and stupor.',
                        'Every rock here gets bigger and angrier each time you look at it.',
                        'An offshoot of the Carotid Forest, eager to consume.'
                    ],
                },
                3: {
                    'name': 'The Grey leaks in',
                    'values': [
                        'The ground desaturates and disappears into a sandy bank along an ichoric river.',
                        'A connection begins to rot, fragment, and crumble.',
                        'An important guide given over to apathy and inertia.',
                        'A Deadwalker bounty-hunter, ready to ambush their target, plunging them into the Grey.',
                        'One of your most valuable items has become haunted.',
                        'One of your most valuable friends has become haunted.'
                    ],
                },
                4: {
                    'name': 'A Spectre, baffled and fixated',
                    'values': [
                        'A Deadwalker’s death that’s lost its partner. It wails and writhes in its search.',
                        'A Hound, scared literally to death, rooted to the spot its body fell.',
                        'An enormous cavern of calcified ghosts, softly moaning.',
                        'A skeleton toll-keeper, monitoring and cataloging all who pass.',
                        'Morticians from the City Above, searching for a runaway phantom.',
                        'A ferocious hyena with a taste for ghosts.'
                    ]
                },
                5: {
                    'name': 'A Psychopomp and its protesting captive',
                    'values': [
                        'An Incarnadine and their indentured servant, making a pilgrimage to the market.',
                        'An Aelfir Skald, hauling imprisoned souls back to Spire for interrogation.',
                        'A blooded Witch, taking the spirit of her sister to be buried at Hallow.',
                        'A ferryman with a surprisingly comprehensive menu of destinations.',
                        'A gregarious mage with a sinister demon to sell you.',
                        'A Hound and a thief, handcuffed together and weaponless.'
                    ]
                },
                6: {
                    'name': 'A Revelation of the self-serving variety',
                    'values': [
                        'A technologist has activated an Angel of their own creation.',
                        'A demagogue and their cult, intent on dragging everyone to heaven.',
                        'A gaping, whispering pit, offering salvation for sacrifice.',
                        'Two guards: one that always lies, and another that always screams.',
                        'A frantic prophetess, unable to give voice to her visions.',
                        'A mirrored maze that offers power, but contains only spiders.'
                    ]
                },
                7: {
                    'name': 'An old Flame, rekindled against nature',
                    'values': [
                        'An ever-smoldering Cleaver, intent on devouring everything in their path.',
                        'A simulacrum of a long-lost love; nearby, and in-danger.',
                        'A lake of flaming ichor, filled with carnivorous fish.',
                        'Desert sands, endless light, and no water for miles.',
                        'A simulacrum of a long-lost love: armed, and dangerous.',
                        'Ash falls from the sky like snow; take cover before the fire pours down.'
                    ]
                },
                8: {
                    'name': 'Elsewhere calls: A door to its avenues swings open',
                    'values': [
                        'The Cartographers, desperately trying to map the local area.',
                        'A crowbar gang, using a portal to secure valuable weapons and resources for their crew.',
                        'Market illusions spill out, bewildering the local wildlife.',
                        'The lights of this path begin to snuff out as the Interstitial creep forward.',
                        'Hounds intend this door to be theirs and theirs alone; by discovering it, you’ve forfeited your liberty.',
                        'An Aelfir-led squadron of Spire militiamen came through a portal, and they’re spoiling for a fight.'
                    ]
                },
                9: {
                    'name': 'An Oracle reluctant to part with their portents',
                    'values': [
                        'A priestess from the Moon Beneath who’s lost her escort.',
                        'Devotees of the Swanfall cult looking for someone to throw off a cliff.',
                        'A laconic Hellionite who claims his gun can tell the future.',
                        'An ancient shrine, abandoned by its congregation, but still producing miracles.',
                        'A set of standing-stones, and a enormous godsbeast frozen at the center.',
                        'A Vermissian Sage searching for the Last Train.'
                    ]
                },
                10: {
                    'name': 'A Wedding in an old, sickly way',
                    'values': [
                        'Stolz-cultists getting married in Heart to prove their love.',
                        'An ancient gazebo, still Witch-blessed and patrolled by Bloodbound beasts.',
                        'Hunted by a newly wed pair of Aelfir on their big-game honeymoon safari.',
                        'An intersection of old train lines, lined with poachers’ traps.',
                        'Statues of petrified Aelfir couples, embraced in desolate union.',
                        'Two marauder gangs, newly united, celebrating with a rampage.'
                    ]
                },
                'Jack': {
                    'name': 'A Jester of a long-dead court',
                    'values': [
                        'A Heretic honor-bound to deliver the mail.',
                        'A Gibberwright with a chaotic new act to put on.',
                        'A skeleton courtier, on their way to find - or create - incredible stories.',
                        'A deadly carrion-pig which ate its whole Haven.',
                        'An emaciated Drow languishes from Mummer’s Pox.',
                        'Ancient animatronics spring to life, intent on entertaining you — or else.'
                    ]
                },
                'Queen': {
                    'name': 'The Regent of a guarded oasis',
                    'values': [
                        'A spacious mansion, home to an Idol and her admirers.',
                        'A powerful exile from the Home Nations, intent on rebuilding their power.',
                        'A Heartsblood stag, faster than any arrow.',
                        'A Somnajac lurking in a hillside of garbage.',
                        'Cannibal-kings and their emergency bunker.',
                        'A hermit in a log cabin, held prisoner by a cult of knives.'
                    ]
                },
                'King': {
                    'name': 'The Cathedral, beautiful and horrible',
                    'values': [
                        'A shrouded enclave, ruled by foul blood-Witches.',
                        'A dreadful shrine to Our Hidden Mistress.',
                        'A sprawling pyramid linked to the Source.',
                        'A network of catacombs, buzzing with Apiatic activity.',
                        'A great machine, worshiped by all who pass through its systems.',
                        'A Lekolean battlefield, covered with chattering skulls.'
                    ]
                }
            },
            'Spade': {
                'Ace': {
                    'name': 'Light',
                    'values': [
                        'An oasis of kind individuals, huddled for safety.',
                        'A barely guarded treasure, pushed out of the walls of the Heart.',
                        'A repository of ancient knowledge, seeking learners.',
                        'A broken fragment of your past, filled with dark secrets.',
                        'A half-dead god, desperate for a single bearer of their liturgy.',
                        'A dead delver, hands clenched around a secret-rife journal.'
                    ]
                },
                2: {
                    'name': 'New Lovers, fresh & ravenous',
                    'values': [
                        'A pair of ‘friendly’ Cleavers, hungry for prey.',
                        'Two Heartsblood beasts, fleeing a much larger predator.',
                        'Mermaids in love, chased by the consequences of eloping.',
                        'Incarnadines drunk on their latest reaping.',
                        'An pair of angels fleeing from the Heart itself.',
                        'Half-transformed Delvers craving blood to fuel their metamorphoses.'
                    ],
                },
                3: {
                    'name': 'A silent Gathering, waiting for its last arrival',
                    'values': [
                        'A sacrificial ritual that still requires a soul.',
                        'A Vermissian Conclave, hungry for the Rail Liturgy.',
                        'A budding Apiary, hunting for an agent of chaos.',
                        'A bloodthirsty Heart-Cult seeking a quart of fresh blood.',
                        'A summoning of a dark god, it’s awaited head-priest dead.',
                        'A Masquerade with need for an unmasked sacrifice.'
                    ],
                },
                4: {
                    'name': 'A Herder with his gibbering flock',
                    'values': [
                        'A shepherd of dimension-hopping reptilian beasts.',
                        'A grand servant of the Red King and a wriggling mass of Wyrmlings.',
                        'A Cleaver and a pack of Bloodbound wolves.',
                        'A blind seer and a raving mad cluster of acolytes.',
                        'A priest of Brother Hellion and his bandoleer of semi-sentient firearms.',
                        'A pastoral scene of shepherds and the bloodthirsty sheep who run the operation.'
                    ]
                },
                5: {
                    'name': 'An Inn, quiet & secret',
                    'values': [
                        'A pristine cottage with a puffing chimney, its residents immolated in-place.',
                        'A bustling hive of piratical vacationers preparing for a hunt.',
                        'A lodge nestled in a wall, its owner darkly fixated on destroying a nearby rival lodge.',
                        'A warm campfire with kindly fellow travelers tending the flames.',
                        'A decrepit tower, its top floor pristine and maintained by automatons.',
                        'An occupied and stocked bunker, open for a price.'
                    ]
                },
                6: {
                    'name': 'The Hive attempts to fix what has been broken',
                    'values': [
                        'An Angel mid-combat with a pack of hunting Deep Apiarists.',
                        'A Heartseed being pruned by heavily armed gardeners.',
                        'A Deep Apiarist sect righting the wrongs of a Heart-changed haven.',
                        'A Heartsblood beast fleeing from hunters who’ll pay a handsome reward.',
                        'A group of jailers descended from the Hive in pursuit of an escaped legendary convict.',
                        'A ragged rip in reality with a cadre attempting to stitch it up.'
                    ]
                },
                7: {
                    'name': 'An ancient Lodge with signs of rebirth',
                    'values': [
                        'A seemingly safe hunting lodge, haunted (and kept tidy) by previous owners.',
                        'A precious, protected cabin, tucked away from danger.',
                        'A marina with a single unharmed boat moored to its planks.',
                        'A cult sacrificial altar chamber with freshly spilled blood adorning the walls.',
                        'A House Gryndel hunting blind with guns still hot on racks.',
                        'An Gnoll Incursion Team outpost.'
                    ]
                },
                8: {
                    'name': 'The Tradesmen, on break at a bloodied project-site',
                    'values': [
                        'A group of masons rebuilding a temple grounds for a mysterious benefactor.',
                        'Loggers bloodied and fresh from the Carotid Forest.',
                        'Plumbers from the Tunnels of Wet Filth, hardened like war veterans.',
                        'A Tradesguild excursion of punished members seeking redemption.',
                        'Jewelers extracting a enormous gem, corpses of their fellows littering the dig-site.',
                        'Miners fresh from the skull of titanic beast, mining its dreams and nightmares.'
                    ]
                },
                9: {
                    'name': 'A Butcher, fresh from the harvest',
                    'values': [
                        'A Hound with a pack covered in strange skins for sale, each with a story and a curse.',
                        'An ex-Cannibal trying to perfect a new craft, a mediocre kill just before him.',
                        'A beast surrounded by the fresh corpses of the last delvers to challenge it.',
                        'A blood-streaked Incarnadine, guns smoking and money pouches full.',
                        'A Sourceborn Construct dragging Vermissian machinery back to the Source.',
                        'A kraken, its tentacles pulling apart a once-sturdy vessel.'
                    ]
                },
                10: {
                    'name': 'A Guide attuned to the land, unwillingly',
                    'values': [
                        'A Cleaver bound to a Heartsblood stag guiding for a fee.',
                        'A Druid melded into a fungal forest who can sense everything in their roots.',
                        'A child with a preternatural bond to an Angel.',
                        'A thrall to an Incarnadine trying to deliver a message and failing to interpret directions.',
                        'A Haruspex Albatross apostate, willing to guide you to the ichor’s places of power.',
                        'A sentient blade crying out for blood, offering the path to its master’s treasure in trade.'
                    ]
                },
                'Jack': {
                    'name': 'A Bailiff hot in pursuit of a prized bounty',
                    'values': [
                        'An escaped servant with their master’s treasure in tow.',
                        'A huntsman with a corpse on his back in hot pursuit of the corpse’s ghost.',
                        'A golem stomping after the owner of its control-poem.',
                        'A Hound hunting down a haven burning arsonist.',
                        'A Damnic Inquisitor hunting down heretical higher-ups in the Moon Beneath.',
                        'A personified Death in pursuit of their escaping Deadwalker.'
                    ]
                },
                'Queen': {
                    'name': 'The Seamstress, who can tailor beyond fabric',
                    'values': [
                        'A Witch with a penchant for warping flesh into new forms.',
                        'Madame, an arachnid master of many who can makes ties of many kinds that truly bind.',
                        'A outfit tailor with exceptional abilities woven in the threads.',
                        'A Ministry spymaster with connections across Destera.',
                        'A god of old, making her will known by her scissors and thread wielding devotees.',
                        'An Aelfir matchmaker looking for a lover for very, very particular client.'
                    ]
                },
                'King': {
                    'name': 'A Master with  high price for what they know',
                    'values': [
                        'A Magister with secrets on the Ministry’s next moves into the Heart.',
                        'An Elsewhere Cartographer with intel on gateways to other worlds.',
                        'A retired psychopomp who knows the way to the Heavens and Hells.',
                        'An Angel hunter who has tagged one of the mythic creatures.',
                        'An delver with a lead on an untapped trove of Prokatakos treasure.',
                        '‘One’ of L’Enfer Noir’s Gentlemen, offering to spirit you away.'
                    ]
                }
            },
            'Diamond': {
                'Ace': {
                    'name': 'Gold',
                    'values': [
                        'A sliver of the Red King’s hoard.',
                        'A gilded automaton, a single key piece missing.',
                        'An emperor’s halberd embedded in the skull of a living beast.',
                        'A piece of Prokatakos technology, half redesigned with galvanics.',
                        'A palanquin borne by Paladins.',
                        'The helm of a fallen hero, wisps of their soul still clinging on.'
                    ]
                },
                2: {
                    'name': 'A Paltry Sum, the bare minimum... barely',
                    'values': [
                        'A threatened Gutterkin with knowledge of a secret passage.',
                        'A half-rusted blade with an inlaid hilt.',
                        'A dying delver begging for the safety of his lost party.',
                        'An errant Druid with a depleted reserve of narcotics.',
                        'Carrion Pigs escaped from their handler, and a reward for their recapture.',
                        'A broken Aelfir, hands clutched on the remnants of his family’s name.'
                    ],
                },
                3: {
                    'name': 'Fool\'s Gold, a false treasure',
                    'values': [
                        'A treasure-chest mimic, not particularly violent and a possible friend.',
                        'A pile of gold that dissolves into ash when grasped.',
                        'A gilded suit of armor with a Heartsblood hermit crab cluster within its many pieces.',
                        'A beautiful grove, a ring of Seelie stones waiting to trap those who enter.',
                        'A false king begging for someone to help him find his lost ‘kingdom.’',
                        'An isolated tree, body warping poison coursing through its fruit.'
                    ],
                },
                4: {
                    'name': 'A Lender with a taste for strange debt',
                    'values': [
                        'A body-shaping Witch with a hunger for new and strange blood.',
                        'A dimension hopping arms dealer with weapons for loan.',
                        'A vehicle-borne tradesman with a shifting stock of edible oddities.',
                        'A forgotten god plying for a single acolyte more.',
                        'An ancient sorcerer with a spell to offer in exchange for something intangible: a sliver of soul, a dream, a wish.',
                        'A usurer with an automaton army of debt-collectors.'
                    ]
                },
                5: {
                    'name': 'A Meal, strange in taste and attendance',
                    'values': [
                        'A slain hundred-foot Wyrm, and a feasting hunting party roasting it over hellfire.',
                        'A masked soiree with inexplicable foods being offered intensely.',
                        'A Druid festival around a rare, blooming crop.',
                        'An Undead feast upon the flesh of an bound, infinitely regenerating giant.',
                        'A flock of megacorvidae feasting on a swarm of Heartsblood locusts.',
                        'The crew of an ichor-borne vessel selling a haul of ‘mystical’ crustaceans.'
                    ]
                },
                6: {
                    'name': 'A Cache, just out of reach',
                    'values': [
                        'A collection of mummified delvers, all clutching the same artifact.',
                        'A glistening amulet of meat, whispering in the mind of those who touch it.',
                        'A trove of coins, all minted in languages no one has ever read.',
                        'An armory of cursed weapons designed to harm the user as well as the target.',
                        'A crumbling temple complex, with both the final tithings and a watchful spirit within.',
                        'A jewel encrusted skeleton, the anatomy of which is of no obvious ancestry.'
                    ]
                },
                7: {
                    'name': 'A Troupe with a wretched performance to give',
                    'values': [
                        'Gibberwrights performing a dress rehearsal of a reality warping tragedy.',
                        'A torture opera’s aftermath.',
                        'A Skald and their apprentices searching for targets to practice their craft on.',
                        'A Gutterkin puppet show performed for a pack of little ones.',
                        'A Damnic religious pageant performed by Moon Beneath heretics.',
                        'A Gnollish Djinn Querent who will perform incredible feats for a price.'
                    ]
                },
                8: {
                    'name': 'A Soirée: forbidden smoke and song fill the air',
                    'values': [
                        'An Aelfir rager that has popped through a very, very unfortunate cursed doorway.',
                        'A Gnollish rescue team celebrating a successful recovery.',
                        'A masquerade in an ambulatory hotel.',
                        'A Vermissian summoning ritual in desperate plea for a train along the tracks.',
                        'A Seelie intrusion of Sky Court air fae seeking hedonistic pleasure.',
                        'A pack of Butchers reveling in a finished hunt.'
                    ]
                },
                9: {
                    'name': 'A Caravan in terrified flight',
                    'values': [
                        'A sect of SWitch-Box cultists fleeing a train-construct they’ve accidentally enraged.',
                        'Incarnadines rushing from those they’ve ripped off.',
                        'A procession of adherents carrying a half-transformed believer to the Moon Grove.',
                        'Swanfall Cultists with new, ‘coerced’ believers, fragments of their old lives in pursuit.',
                        'A water caravan heading to a haven, pursued hotly by desiccated husks.',
                        'Heart-warped thieves laden with treasure from Cairnmor, courtiers hot on their heels.'
                    ]
                },
                10: {
                    'name': 'A pleasant, wordless Merchant, recently scorned',
                    'values': [
                        'An Aelfir haberdasher with poor direction to their client.',
                        'A headhunter with a particularly slippery mark.',
                        'A Drow relic-hawker recently robbed.',
                        'A traveling surgeon sick with a patient’s illness seeking retribution or a cure.',
                        'A money-lender seeking revenge for a bounced bill.',
                        'A chef-errant lost after a failed ingredient hunting venture.'
                    ]
                },
                'Jack': {
                    'name': 'A cursed Thief-Band, laden with new riches',
                    'values': [
                        'Blood-thirsty cannibals with an untouched crop.',
                        'Burglars fresh from one of the heavens, psychopomps in pursuit.',
                        'Fugitives from up-Spire, carrying materials sensitive to the Aelfir ruling class.',
                        'Gutterkin laden with treasure the magnitude of which they have no idea.',
                        'A pack of Sodden, broken away from their Haruspex Albatross master, a relic of the god of the ichor closely held.',
                        'The escaped thralls of a Wyrm, a fraction of its hoard in tow.'
                    ]
                },
                'Queen': {
                    'name': 'The Vault, sealed and jealously guarded',
                    'values': [
                        'A legendary brigand brigade’s bounty.',
                        'A dead god’s sealed temple, surrounded by undying servants.',
                        'A shattered heaven with a crumbling gateway, held aloft by a zealous order.',
                        'A gilded prison with inmates running the show.',
                        'An ancient engine, its caretakers meticulously keeping its innards.',
                        'A suspended aethership, crashed through the boundaries between worlds.'
                    ]
                },
                'King': {
                    'name': 'A broken Dragon atop an alien hoard',
                    'values': [
                        'A half-living Wyrm on a hoard of thralls.',
                        'A serpentine creature defending a prokatakos mystery.',
                        'A lion’s pride, warped beyond recognition, prey in tow.',
                        'A warlord and their defeated vassals.',
                        'A treasure-laden Incarnadine caravanning to ‘safety.’',
                        'A gardening Angel, busy replanting a crop of Heartseeds.'
                    ]
                }
            },
        }

    keep_picking = True

    candidate_cards = {
        suit: {
            card_value: card_data for card_value, card_data in suit_card_data.items() if get_full_card_name(card_value, suit) not in already_picked
        } for suit, suit_card_data in pick_delve_draw_card.cards.items()
    }

    filtered_candidate_cards = {
        suit: suit_card_data for suit, suit_card_data in candidate_cards if len(suit_card_data)
    }

    if len(filtered_candidate_cards) == 0:
        raise ValueError('No more cards available - you\'ve picked them all.')

    while keep_picking:
        suit: str = random.choice(list(filtered_candidate_cards.keys()))

        card_value, card = random.choice(list(filtered_candidate_cards[suit].items()))

        card_name = f'{card_value} of {suit}s'

        if card_name in already_picked:
            continue

        return card_name, card

def get_delve_draw(expand_draws: bool = False, five_card_draw: bool = False, allow_duplicates: bool = False):
    picked_cards = set()
    draws = []

    for i in range(3):
        picked_name, picked_card = pick_delve_draw_card(picked_cards)

        if not allow_duplicates:
            picked_cards.add(picked_name)

        draws.append((picked_name, picked_card))

    response = f'{bold(underline("Drawn Cards"))}\n\n'
    steps = ['Start', 'Middle', 'End']

    for step, (picked_name, picked_card) in zip(steps, draws):
        if expand_draws:
            description = random.choice(picked_card['values'])
        else:
            description = picked_card['name']

        response += f'* {bold(step)}: {description} ({picked_name})\n'

    if five_card_draw:
        positive_flavour_name, positive_flavour_card = pick_delve_draw_card(picked_cards)

        if not allow_duplicates:
            picked_cards.add(positive_flavour_name)

        negative_flavour_name, negative_flavour_card = pick_delve_draw_card(picked_cards)

        if not allow_duplicates:
            picked_cards.add(negative_flavour_name)

        if expand_draws:
            positive_description = random.choice(positive_flavour_card['values'])
            negative_description = random.choice(negative_flavour_card['values'])
        else:
            positive_description = positive_flavour_card['name']
            negative_description = negative_flavour_card['name']

        response += f'''\n* {bold("Blessed by")}: {positive_description} ({positive_flavour_name})
* {bold("Cursed By")}: {negative_description} ({negative_flavour_name})'''

    return response

@vermissian.slash_command(name='delve_draw', description='Does an ichor-drowned delve-draw', guilds=[discord.Object(1218845257899446364), discord.Object(1193578278175375432)])
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

def add_character(guild_id: int, discord_username: str, discord_display_name: str, character_sheet_url: str):
    game = vermissian.games[guild_id]

    character = game.add_character(spreadsheet_url=character_sheet_url, username=discord_username)

    response = f"Added character {character.character_name} and linked them to {discord_display_name}."

    response = response[:2000]

    return response

@vermissian.slash_command(name='add_character', description='Adds a character.', guilds=[discord.Object(1218845257899446364), discord.Object(1193578278175375432)])
@command_logging_decorator
@error_responder_decorator
@guild_required_decorator
async def add_character_command(
    ctx: discord.ApplicationContext,
    character_sheet_url: discord.Option(str, "The URL for your character sheet in the character tracker.")
):
    interaction = await ctx.respond('Adding character...')

    response = add_character(
        guild_id=ctx.guild_id,
        discord_username=ctx.user.name,
        discord_display_name=ctx.user.display_name,
        character_sheet_url=character_sheet_url
    )

    await interaction.edit(content=response)

def roll_spire_action(
    guild_id: int,
    username: str,
    skill: str,
    domain: str,
    mastery: bool = False,
    num_helpers: int = 0,
    difficulty: int = 0
):
    game = vermissian.games[guild_id]

    if game.system != System.SPIRE:
        raise WrongGameError(expected_system=System.SPIRE, used_system=game.system)

    num_dice = 1
    dice_size = 10

    if mastery:
        num_dice += 1

    num_dice += num_helpers

    roll = Roll(num_dice=num_dice, dice_size=dice_size, difficulty=difficulty)

    downgrade_expression = ''

    skill_to_use = SpireSkill.get(skill)
    domain_to_use = SpireDomain.get(domain)

    highest, results, outcome, total, had_skill, had_domain, did_downgrade = game.roll_check(
        username=username,
        initial_roll=roll,
        skill=skill_to_use,
        domain=domain_to_use
    )

    if did_downgrade:
        downgrade_expression = 'which was downgraded '

    skill_text = bold(skill_to_use.value) if had_skill else skill_to_use.value
    domain_text = bold(domain_to_use.value) if had_domain else domain_to_use.value

    modifier_expression = f'{skill_text}+{domain_text}'

    if mastery:
        modifier_expression += ', mastery'

    if num_helpers > 0:
        modifier_expression += f', {num_helpers} helpers'

    response = f'You rolled {len(results)}d{dice_size} ({modifier_expression}) {"" if difficulty == 0 else f" with a difficulty of {difficulty}"} {downgrade_expression}for a "**{outcome}**": {{{", ".join(results)}}}'

    # TODO Make this an interactive button thing to roll one

    if outcome in [game.CRIT_FAILURE, game.FAILURE, game.SUCCESS_AT_A_COST]:
        stress = {
            'd3': random.randint(1, 3),
            'd6': random.randint(1, 6),
            'd8': random.randint(1, 8)
        }

        response += '\nStress values: '
        stress_tokens = []

        for stress_die, rolled_stress in stress.items():
            if outcome == game.CRIT_FAILURE:
                stress_die = f'{stress_die} * 2'
                rolled_stress *= 2

            stress_tokens.append(f'{stress_die}: {spoiler(code(rolled_stress))}')

        response += ', '.join(stress_tokens)

    if len(response) > 2000:
        response = 'Very long roll, some of it will be cut off.\n\n' + response

    response = response[:2000]

    return response

@vermissian.slash_command(name='spire_action', description='Rolls dice for taking an action in Spire', guilds=[discord.Object(1218845257899446364), discord.Object(1193578278175375432)])
@command_logging_decorator
@error_responder_decorator
@character_required_decorator
async def roll_spire_action_command(
    ctx: discord.ApplicationContext,
    skill: discord.Option(str, 'Relevant Skill', options=spire_skills),
    domain: discord.Option(str, 'Relevant Domain', options=spire_domains),
    mastery: discord.Option(bool, 'Has mastery?', default=False),
    num_helpers: discord.Option(int, 'How many other players are helping? (Requires relevant skill or domain, shares stress)', default=0, min=0),
    difficulty: discord.Option(int, "Difficulty of the action", default=0, min_value=0, max_value=2)
):
    response = roll_spire_action(
        guild_id=ctx.guild_id,
        username=ctx.user.name,
        skill=skill,
        domain=domain,
        mastery=mastery,
        num_helpers=num_helpers,
        difficulty=difficulty
    )

    await ctx.respond(response)

def roll_heart_action(guild_id: int, username: str, skill: str, domain: str, mastery: bool = False, num_helpers: int = 0, difficulty: int = 0):
    game = vermissian.games[guild_id]

    if game.system != System.HEART:
        raise WrongGameError(expected_system=System.HEART, used_system=game.system)

    num_dice = 1
    dice_size = 10

    if mastery:
        num_dice += 1

    num_dice += num_helpers

    roll = Roll(num_dice=num_dice, dice_size=dice_size, difficulty=difficulty)

    downgrade_expression = ''

    skill_to_use = HeartSkill.get(skill)
    domain_to_use = HeartDomain.get(domain)

    highest, results, outcome, total, had_skill, had_domain, used_difficult_actions_table = game.roll_check(
        username=username,
        initial_roll=roll,
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

    # TODO Make this an interactive button thing to roll one

    if outcome in [game.CRIT_FAILURE, game.FAILURE, game.SUCCESS_AT_A_COST]:
        stress = {
            'd3': random.randint(1, 3),
            'd6': random.randint(1, 6),
            'd8': random.randint(1, 8)
        }

        response += '\nStress values: '
        stress_tokens = []

        for stress_die, rolled_stress in stress.items():
            if outcome == game.CRIT_FAILURE:
                stress_die = f'{stress_die} * 2'
                rolled_stress *= 2

            stress_tokens.append(f'{stress_die}: {spoiler(code(rolled_stress))}')

        response += ', '.join(stress_tokens)

    if len(response) > 2000:
        response = 'Very long roll, some of it will be cut off.\n\n' + response

    response = response[:2000]

    return response

@vermissian.slash_command(name='heart_action', description='Rolls dice for taking an action in Heart', guilds=[discord.Object(1218845257899446364), discord.Object(1193578278175375432)])
@command_logging_decorator
@error_responder_decorator
@character_required_decorator
async def roll_heart_action_command(
    ctx: discord.ApplicationContext,
    skill: discord.Option(str, 'Relevant Skill', options=heart_skills),
    domain: discord.Option(str, 'Relevant Domain', options=heart_domains),
    mastery: discord.Option(bool, 'Has mastery?', default=False),
    num_helpers: discord.Option(int, 'How many other players are helping? (Requires relevant skill or domain, shares stress)', default=0, min=0),
    difficulty: discord.Option(int, "Difficulty of the action", default=0, min_value=0, max_value=2)
):
    response = roll_heart_action(
        guild_id=ctx.guild_id,
        username=ctx.user.name,
        skill=skill,
        domain=domain,
        mastery=mastery,
        num_helpers=num_helpers,
        difficulty=difficulty
    )

    await ctx.respond(response)

if False:
    @vermissian.slash_command(name='roll_action', description='Rolls dice for taking an action', guilds=[discord.Object(1218845257899446364), discord.Object(1193578278175375432)])
    @command_logging_decorator
    @error_responder_decorator
    @character_required_decorator
    async def roll_action_command(
        ctx: discord.ApplicationContext,
        skill: discord.Option(str, 'Relevant Skill', autocomplete=get_skills),
        domain: discord.Option(str, 'Relevant Domain', autocomplete=get_domains),
        mastery: discord.Option(bool, 'Has mastery?', default=False),
        num_helpers: discord.Option(int, 'How many other players are helping?', default=0, min=0),
        difficulty: discord.Option(int, "Difficulty of the action", default=0, min_value=0, max_value=2)
    ):
        game = vermissian.games[ctx.guild_id]

        num_dice = 1
        dice_size = 10

        if mastery:
            num_dice += 1

        num_dice += num_helpers

        roll = Roll(num_dice=num_dice, dice_size=dice_size, difficulty=difficulty)

        downgrade_expression = ''

        if game.system == System.SPIRE:
            skill_to_use = SpireSkill.get(skill)
            domain_to_use = SpireDomain.get(domain)

            highest, results, outcome, total, had_skill, had_domain, did_downgrade = game.roll_check(
                username=ctx.user.name,
                initial_roll=roll,
                skill=skill_to_use,
                domain=domain_to_use
            )

            if did_downgrade:
                downgrade_expression = 'which was downgraded '

        elif game.system == System.HEART:
            skill_to_use = HeartSkill.get(skill)
            domain_to_use = HeartDomain.get(domain)

            highest, results, outcome, total, had_skill, had_domain, used_difficult_actions_table = game.roll_check(
                username=ctx.user.name,
                initial_roll=roll,
                skill=skill_to_use,
                domain=domain_to_use
            )

            if used_difficult_actions_table:
                downgrade_expression = 'on the Difficult Actions table'
        else:
            raise ValueError(f'Unknown game type: {game.system}')

        skill_text = bold(skill_to_use.value) if had_skill else skill_to_use.value
        domain_text = bold(domain_to_use.value) if had_domain else domain_to_use.value

        modifier_expression = f'{skill_text}+{domain_text}'

        if mastery:
            modifier_expression += ', mastery'

        response = f'You rolled {len(results)}d{dice_size} ({modifier_expression}) {"" if difficulty == 0 else f" with a difficulty of {difficulty}"} {downgrade_expression}for a "**{outcome}**": {{{", ".join(results)}}}'

        # TODO Make this an interactive button thing to roll one

        if outcome in [ game.CRIT_FAILURE, game.FAILURE, game.SUCCESS_AT_A_COST ]:
            stress = {
                'd3': random.randint(1, 3),
                'd6': random.randint(1, 6),
                'd8': random.randint(1, 8)
            }

            response += '\nStress values: '
            stress_tokens = []

            for stress_die, rolled_stress in stress.items():
                if outcome == game.CRIT_FAILURE:
                    stress_die = f'{stress_die} * 2'
                    rolled_stress *= 2

                stress_tokens.append(f'{stress_die}: {spoiler(code(rolled_stress))}')

            response += ', '.join(stress_tokens)

        # TODO Roll Fallout at the same time, if taking stress?

        if len(response) > 2000:
            response = 'Very long roll, some of it will be cut off.\n\n' + response

        response = response[:2000]

        await ctx.respond(response)

def heart_fallout(guild_id: int, username: str):
    game: HeartGame = vermissian.games[guild_id]

    if not isinstance(game, HeartGame):
        raise WrongGameError(expected_system=System.HEART, used_system=game.system)

    rolled, level, stress_removed, original_stress = game.roll_fallout(username)

    response = f'You rolled a {rolled} for fallout, against {original_stress} stress '

    if level == 'no':
        response += f'so you {bold("avoid")} any fallout!'
    elif level == 'Minor':
        response += f'so you take {bold(level)} fallout. You can remove all stress from the resistance that triggered this.'
    else:
        response += f'so you take {bold(level)} fallout. You can remove all stress from {bold("all")} of your resistances.'

    return response

@vermissian.slash_command(name='heart_fallout', description='Rolls dice for a Heart fallout check', guilds=[discord.Object(1218845257899446364), discord.Object(1193578278175375432)])
@command_logging_decorator
@error_responder_decorator
@character_required_decorator
async def heart_fallout_command(
    ctx: discord.ApplicationContext
):
    response = heart_fallout(ctx.guild_id, ctx.user.name)

    await ctx.respond(response)

def spire_fallout(guild_id: int, username: str, resistance: Literal['Blood', 'Mind', 'Silver', 'Shadow', 'Reputation']):
    game: SpireGame = vermissian.games[guild_id]

    if not isinstance(game, SpireGame):
        raise WrongGameError(expected_system=System.HEART, used_system=game.system)

    rolled, level, stress_removed, original_stress = game.roll_fallout(username, resistance)

    response = f'You rolled a {rolled} for fallout, against {original_stress} stress '

    if level == 'no':
        response += f'so you {bold("avoid")} any fallout!'
    else:
        response += f'so you take {bold(level)} fallout. You can remove {stress_removed} stress from your resistances.'

    return response

@vermissian.slash_command(name='spire_fallout', description='Rolls dice for a Spire fallout check', guilds=[discord.Object(1218845257899446364), discord.Object(1193578278175375432)])
@command_logging_decorator
@error_responder_decorator
@character_required_decorator
async def spire_fallout_command( # TODO Nice to not always have to specify resistance track, but less lethal interferes there
    ctx: discord.ApplicationContext,
    resistance: discord.Option(str, 'Resistance track that triggered this', options=SpireCharacter.RESISTANCES, default=None)
):
    response = spire_fallout(ctx.guild_id, ctx.user.name, resistance)

    await ctx.respond(response)

if False:
    @vermissian.slash_command(name='roll_fallout', description='Rolls dice for a fallout check', guilds=[discord.Object(1218845257899446364), discord.Object(1193578278175375432)])
    @command_logging_decorator
    @error_responder_decorator
    @character_required_decorator
    async def roll_fallout_command( # TODO Nice to not always have to specify resistance track, but less lethal interferes there
        ctx: discord.ApplicationContext,
        resistance: discord.Option(str, 'Resistance track that triggered this', autocomplete=get_resistance_tracks)
    ):
        game = vermissian.games[ctx.guild_id]

        if game.system == System.SPIRE:
            resistance_options = SpireCharacter.RESISTANCES
        elif game.system == System.HEART:
            resistance_options = HeartCharacter.RESISTANCES

        if resistance not in resistance_options:
            await ctx.respond(f'Invalid resistance: Must be one of {resistance_options}')
            return

        if game.system == System.SPIRE:
            rolled, level, stress_removed, original_stress = game.roll_fallout(ctx.user, resistance)

            response = f'You rolled a {rolled} for fallout, against {original_stress} stress '

            if level == 'no':
                response += f'so you {bold("avoid")} any fallout!'
            else:
                response += f'so you take {bold(level)} fallout. You can remove {stress_removed} stress from your resistances.'

        elif game.system == System.HEART:
            rolled, level, stress_removed, original_stress = game.roll_fallout(ctx.user)

            response = f'You rolled a {rolled} for fallout, against {original_stress} stress '

            if level == 'no':
                response += f'so you {bold("avoid")} any fallout!'
            elif level == 'Minor':
                response += f'so you take {bold(level)} fallout. You can remove all stress from the resistance that triggered this.'
            else:
                response += f'so you take {bold(level)} fallout. You can remove all stress from {bold("all")} of your resistances.'

        await ctx.respond(response)

@vermissian.slash_command(name='roll', description='Rolls dice', guilds=[discord.Object(1218845257899446364), discord.Object(1193578278175375432)])
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
    except VermissianError as e:
        await ctx.respond(str(e))
    except ValueError as v:
        logger.warning(v, exc_info=True)
        await ctx.respond('Cannot understand that roll. Please define each roll as XdY +A -B, and separate them with "+" or ",". You can specify a "Difficulty" of 0-2 to remove that many of the highest dice, and use # to add a note.', ephemeral=True)

def simple_roll(rolls: List[Roll], note: Optional[str] = None):
    all_results = []
    overall_highest = 0
    overall_total = 0
    rolled_expression_tokens = []
    all_results_tokens = []

    # TODO Shouldn't be hardcoded Spire, but need to figure out how I want Difficulty to work outside of game rolls.
    for index, roll in enumerate(rolls):
        highest, results, _, total = SpireGame.simple_roll(roll)

        all_results.append(results)
        overall_highest = max(highest, overall_highest)

        expression = str(roll) if index == len(rolls) - 1 else roll.str_no_difficulty()

        rolled_expression_tokens.append(expression)

        results_expression = '{' + ', '.join(results) + '}'

        if roll.bonus > 0:
            results_expression += f' + {roll.bonus}'

        if roll.penalty > 0:
            results_expression += f' - {roll.penalty}'

        modified_total = total + roll.bonus - roll.penalty
        results_expression += f' = **{highest + roll.bonus - roll.penalty}** (Total: {modified_total})'

        all_results_tokens.append(
            results_expression
        )

        overall_total += modified_total

    rolled_expression = ', '.join(rolled_expression_tokens)

    response = f'You rolled {rolled_expression}{f" ({note})" if note is not None else ""}: '

    if len(all_results_tokens) > 1:
        response += '\n'

    for results_expression in all_results_tokens:
        if len(all_results_tokens) > 1:
            response += '* '

        response += results_expression

        if len(all_results_tokens) > 1:
            response += '\n'

    if len(all_results_tokens) > 1:
        response += f'**Overall Total**: {overall_total}'

    return response

def unlink(guild_id: int):
    if guild_id in vermissian.games:
        vermissian.remove_game(guild_id)

        return 'Unlinked! You can re-link by using /link.'
    else:
        return 'No game to unlink.'

@vermissian.slash_command(name='unlink', description='Unlinks game information from the current server, undoing the last /link', guilds=[discord.Object(1218845257899446364), discord.Object(1193578278175375432)])
@command_logging_decorator
@error_responder_decorator
async def unlink_command(
    ctx: discord.ApplicationContext,
):
    response = unlink(ctx.guild_id)

    await ctx.respond(response)

def link(guild_id: int, system: System, spreadsheet_url: str, less_lethal: bool):
    if system == System.SPIRE.value:
        game = vermissian.create_game(
            guild_id=guild_id,
            spreadsheet_url=spreadsheet_url,
            system=system,
            less_lethal=less_lethal
        )
    else:
        game = vermissian.create_game(
            guild_id=guild_id,
            spreadsheet_url=spreadsheet_url,
            system=system
        )

    response = "Linked to character tracker."

    if len(game.character_sheets):
        for discord_username, character_sheet in game.character_sheets.items():
            response += f'\n* Linked {discord_username} to character {character_sheet.character_name}'
    else:
        response += f'\nNo characters linked yet, you can do so via the {code("/add_character")} command.'

    return response

@vermissian.slash_command(name='link', description='Links the bot to a specified game and character tracker. Adds characters it finds.', guilds=[discord.Object(1218845257899446364), discord.Object(1193578278175375432)])
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

    response = link(ctx.guild_id, system, spreadsheet_url, less_lethal)

    await interaction.edit(content=response)

@vermissian.event
async def on_ready():
    logger.info(f'We have logged in as {vermissian.user}', stack_info=False)

    await vermissian.change_presence(activity=discord.Activity(type=discord.ActivityType.playing, name='Run /help to get started.'))

@vermissian.event
async def on_message(message: discord.Message):
    if message.author == vermissian.user:
        return

    if message.content.lower().strip().startswith('roll'):
        try:
            rolls, note = Roll.parse_roll(message.content)

            response = simple_roll(rolls, note)

            await message.reply(response)
        except VermissianError as v:
            logger.error(v)
            await message.reply(str(v))
        except Exception as e:
            logger.error(e)

def main():
    with open('credentials.json', 'r') as f:
        token = json.load(f)['token']

    for server_data_dir in glob.glob(os.path.join('servers', '*')):
        guild_id = int(server_data_dir.split(os.sep)[1])

        try:
            game = Game.load(guild_id)

            vermissian.add_game(game=game)

            logger.info(f'Loaded {game}', stack_info=False)
        except FileNotFoundError as f:
            logger.error(f, exc_info=True)
            continue

    vermissian.run(token=token)

if __name__ == '__main__':
    main()