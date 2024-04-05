import discord

import random
import abc
import functools
import os
import json
import shutil
from typing import List, Dict, Tuple, Union, Literal, Iterable, Optional, Any

from System import System
from SpireCharacterSheet import SpireCharacter, SpireSkill, SpireDomain
from HeartCharacterSheet import HeartCharacter, HeartSkill, HeartDomain
from Roll import Roll
from utils.google_sheets import get_spreadsheet_metadata
from utils.format import strikethrough, bold
from utils.logger import get_logger
from utils.exceptions import UnknownSystemError

class Game(abc.ABC):
    """
    Represents a Discord server using the bot.
    """

    def __init__(
        self,
        guild_id: int,
        spreadsheet_id: str,
        system: System,
    ):
        self.guild_id = guild_id
        self.spreadsheet_id = spreadsheet_id
        self.system = system

        self.spreadsheet_metadata = get_spreadsheet_metadata(self.spreadsheet_id)

        self.character_sheets: Dict[str, Union[SpireCharacter, HeartCharacter]] = {}

        self.server_info_dirpath = os.path.join('servers', str(guild_id))

        os.makedirs(self.server_info_dirpath, exist_ok=True)

        self.character_file_data = {}

        self.logger = get_logger()

    def get_character(self, user: discord.Member) -> Union[SpireCharacter, HeartCharacter]:
        if user.name in self.character_sheets:
            return self.character_sheets[user.name]

        raise ValueError(f'No character linked to {user.name}: Known user-characters are {list(self.character_sheets.keys())}')

    @classmethod
    def format_roll(cls, rolled: Iterable[int], indices_to_remove: Iterable[int], highest: int) -> List[str]:
        formatted_results = []

        str_cast = lambda s: str(s)

        for index, roll in enumerate(rolled):
            if index in indices_to_remove:
                formatter = strikethrough
            elif roll == highest:
                formatter = bold
            else:
                formatter = str_cast

            formatted_results.append(formatter(roll))

        return formatted_results

    @abc.abstractmethod
    def create_character(self, spreadsheet_id: str, sheet_name: str):
        raise NotImplementedError('Implement me!')

    @classmethod
    def load(cls, guild_id: int) -> Union['SpireGame', 'HeartGame']:
        game_data = cls.load_game_data(guild_id)

        if int(game_data['guild_id']) != guild_id:
            raise ValueError(f'Guild IDs do not match up, cannot load data.')

        if game_data['system'] == System.SPIRE.value:
            return SpireGame.from_data(game_data)
        elif game_data['system'] == System.HEART.value:
            return HeartGame.from_data(game_data)
        else:
            raise UnknownSystemError(system=game_data['system'])

    @staticmethod
    @abc.abstractmethod
    def from_data(game_data: Dict[str, Any]):
        raise NotImplementedError('Implement me!')

    @classmethod
    def get_server_dirpath(cls, guild_id: int) -> str:
        return os.path.join('servers', str(guild_id))

    @classmethod
    def get_game_data_filepath(cls, guild_id: int) -> str:
        return os.path.join(cls.get_server_dirpath(guild_id), 'game_data.json')

    @classmethod
    def load_game_data(cls, guild_id: int) -> Dict[str, Any]:
        game_data_filepath = cls.get_game_data_filepath(guild_id)

        if not os.path.exists(game_data_filepath):
            raise FileNotFoundError(f'No game data found for Guild ID "{guild_id}"')

        with open(game_data_filepath, 'r', encoding='utf-8') as f:
            game_data = json.load(f)

        return game_data

    def save(self):
        server_dir_path = self.get_server_dirpath(self.guild_id)

        os.makedirs(server_dir_path, exist_ok=True)

        with open(self.get_game_data_filepath(self.guild_id), 'w', encoding='utf-8') as f:
            json.dump(self.game_data, f, indent=4)

    def remove(self):
        server_dir_path = self.get_server_dirpath(self.guild_id)

        if os.path.isdir(server_dir_path):
            shutil.rmtree(server_dir_path)

    @property
    def game_data(self):
        game_data = {
            'guild_id': self.guild_id,
            'system': self.system.value,
            'spreadsheet_id': self.spreadsheet_id,
            'characters': {
                discord_username: character.info() for discord_username, character in self.character_sheets.items()
            },
        }

        return game_data

class SpireGame(Game):
    """
    Represents a Discord server using the bot for a Spire game.
    """

    TAGS = {
        'Accurate': 'If the user takes a minute or so to set up the shot as part of an ambush or surprise attack, they roll with mastery when attacking. This is not possible once combat has started. ',
        'Bloodbound': 'Mark D3 stress to Blood to roll with mastery when using this equipment for the rest of the situation. ',
        'Bound': 'You can use Bound class abilities through this weapon. ',
        'Brutal': 'When you roll for stress with this weapon, roll two dice and pick the highest. Multiple instances of the Brutal tag stack; if you managed to get Brutal three times, for example, then you’d roll four dice and pick the highest when inflicting stress. ',
        'Concealable': 'When you attempt to conceal this weapon / armour, roll with mastery. ',
        'Conduit': 'Mark D3 stress to Mind to roll with mastery when using this equipment for the rest of the situation. ',
        'Dangerous': 'If your highest D10 shows a 1 or a 2 when you use this weapon, it has exploded. Take D6 stress; the weapon is destroyed. ',
        'Defensive': 'While using this weapon, you gain an additional Armour resistance slot. ',
        'Devastating': 'You cannot allocate stress inflicted by this weapon to armour, even if it has the Implacable tag. Double-barrelled: You can use this weapon twice before reloading, or fire both barrels at once to give the attack the Brutal tag. Extreme ',
        'Range': 'This weapon can be used at extreme range. ',
        'Masterpiece': 'This weapon’s damage dice increases by 1 step when used by someone with mastery of the Fight skill. One-shot: You can only use this weapon once per situation; it takes a very long time to reload.',
        'Ongoing Dx': 'At the end of the situation, a character who took damage from this weapon must succeed on a Resist check or suffer an additional Dx stress. ',
        'Parrying': 'Once per situation, when an enemy inflicts stress to Blood with you in melee combat, force the GM to reroll the stress inflicted. ',
        'Piercing': 'You cannot allocate stress inflicted by this weapon to armour, unless the armour has the Implacable tag. Point-blank: When used at extremely close range, this weapon’s damage increases by 1 dice size; at anything over medium range, it decreases by 1. ',
        'Ranged': 'This weapon can be used at range. ',
        'Reload': 'Once you’ve used this weapon, it cannot be used again until you spend time reloading it. ',
        'Scarring': 'Causes savage, ugly wounds on targets.',
        'Spread Dx': 'If you succeed on an attack with this weapon, you inflict half the stress you dealt to the original target to a number of other targets standing nearby, equal to the result of your Dx roll. ',
        'Surprising': 'The first time you use this weapon in a situation, roll with mastery. ',
        'Stunning': 'If you succeed on an attack roll with this weapon, you may declare that any affected targets take no stress, but their difficulty is reduced to 0 until they gather their senses. ',
        'Tiring': 'When you fail an action using this item, its damage decreases in dice size by 1. ',
        'Unreliable': 'When you fail an action using this equipment, it cannot be used for the remainder of the situation.',

        # Armour Tags - Concealable is merged with the weapon one
        'Assault': 'You may choose to mark 1 stress against this armour; if you do so, you gain mastery to Fight on your next action.',
        'Camouflaged': 'The armour is designed to camouflage the wearer in specific terrain; when they use Sneak in that terrain, they do so with mastery.',
        'Implacable': 'Piercing weapons do not negate this armour, but Devastating weapons do.',
        'Heavy': 'When wearing your armour, you may not use the Pursue or Sneak skills to gain additional dice.',

        # From Strata
        'Unstable': 'Unless properly braced and aimed (preferably against something solid), attacks with this weapon increase their difficulty by 1.',
        'Keen': 'When you roll a 10 on an attack with this weapon, inflict +3 extra stress rather than +1.',
        'Poisoned': 'If this weapon inflicts stress to armour, it functions as normal; against Blood, all stress inflicted is doubled.'
    }

    ALL_DIFFICULTIES = {
        '1': 1,
        '2': 2
    }

    FALLOUT_LEVELS = {
        'Severe': {
            'threshold': 9,
            'clear': 5
        },
        'Moderate': {
            'threshold': 5,
            'clear': 5
        },
        'Minor': {
            'threshold': 2,
            'clear': 3
        },
        'no': {
            'threshold': 0,
            'clear': 0
        },
    }

    RESISTANCES = ['Blood', 'Mind', 'Silver', 'Shadow', 'Reputation']

    CORE_RESULTS = {
        10: 'Critical Success (+1 Stress outgoing per 10)',
        8: 'Success (no stress)',
        6: 'Success at a Cost (stress, one dice size lower if avoiding damage)',
        2: 'Failure (stress)',
        1: 'Critical Failure (double stress)',
    }

    RESERVED_SHEET_NAMES = [
        'Credits',
        'Changelog',
        'GM Tracker',
        'GM Tracker (Vertical)',
        'Lines and Veils',
        'Notes',
        # 'Example Character Sheet' # TODO Re-enable when done testing
        'Rules Engine'
    ]

    def __init__(self, guild_id:  int, spreadsheet_id: str, less_lethal: bool, characters: Optional[List[HeartCharacter]] = None):
        super().__init__(guild_id, spreadsheet_id, System.SPIRE)

        self.less_lethal = less_lethal

        if characters is None:
            characters = []

        characters = [character for character in characters if character.discord_username is not None]

        if len(characters) == 0:
            for sheet_id, sheet_name in self.spreadsheet_metadata.items():
                if sheet_name not in self.RESERVED_SHEET_NAMES:
                    self.logger.debug(sheet_name)

                    try:
                        character = SpireCharacter(
                            spreadsheet_id=spreadsheet_id,
                            sheet_name=sheet_name,
                        )

                        if character.discord_username is not None:
                            characters.append(character)

                    except ValueError as v:
                        self.logger.error(v, exc_info=True)
                        continue

        for character in characters:
            self.add_character(character)

        self.save()

    def roll_check(self, user: discord.Member, skill: SpireSkill, domain: SpireDomain, initial_roll: Roll) -> Tuple[int, List[str], str, int, bool, bool, bool]:
        roll = initial_roll

        has_skill, has_domain = self.get_character(user).check_skill_and_domain(skill, domain)

        if has_skill:
            roll.num_dice += 1

        if has_domain:
            roll.num_dice += 1

        highest, formatted_results, downgrade, total = self.simple_roll(roll)

        outcome = self.get_result(highest, downgrade)

        did_downgrade = ( downgrade > 0)

        return highest, formatted_results, outcome, total, has_skill, has_domain, did_downgrade

    def roll_fallout(self, user: discord.Member, resistance: Optional[Literal['Blood', 'Mind', 'Silver', 'Shadow', 'Reputation']]) -> Tuple[int, Literal['no', 'Minor', 'Moderate', 'Severe'], int, int]:

        character = self.get_character(user)

        stress = character.get_fallout_stress(self.less_lethal, resistance)

        rolled = random.randint(1, 10)

        fallout_level = 'no'
        stress_removed = self.FALLOUT_LEVELS['no']['clear']

        if rolled < stress:
            for fallout_level, fallout_level_data in self.FALLOUT_LEVELS.items():
                if stress >= fallout_level_data['threshold']:
                    stress_removed = fallout_level_data['clear']
                    break

        return rolled, fallout_level, stress_removed, stress

    @classmethod
    def pick_highest(cls, rolled: Iterable[int]) -> int:
        highest = max(rolled)

        return highest

    @classmethod
    @functools.lru_cache()
    def apply_downgrade(cls, highest: int, downgrade: int = 0):
        if downgrade < 0:
            raise ValueError(f'Cannot have negative downgrade.')

        if highest < 1:
            raise ValueError(f'Cannot have a value < 1')

        if highest > 10:
            raise ValueError(f'Cannot have a value > 10')

        current_downgrade = downgrade

        new_result = highest
        while current_downgrade > 0:
            new_result = cls.compute_downgrade_map()[new_result]
            current_downgrade -= 1

        return new_result

    @classmethod
    def compute_downgrade_difficulty(cls, num_dice: int, difficulty: int) -> Tuple[int, int]:
        if num_dice > difficulty:
            new_difficulty = difficulty
            downgrade = 0
        elif num_dice == 1:
            new_difficulty = 0
            downgrade = difficulty
        elif num_dice == difficulty:
            new_difficulty = 1
            downgrade = difficulty - 1
        else:
            new_difficulty = num_dice - 1
            downgrade = difficulty - new_difficulty

        return downgrade, new_difficulty

    def add_character(self, character: SpireCharacter):
         self.character_sheets[character.discord_username] = character

         self.character_file_data[character.discord_username] = {
             'spreadsheet_id': character.spreadsheet_id,
             'sheet_name': character.sheet_name
         }

    @classmethod
    def simple_roll(cls, roll: Roll) -> Tuple[int, List[str], int, int]:
        results = []

        downgrade, difficulty_to_use = cls.compute_downgrade_difficulty(roll.num_dice, roll.difficulty)

        num_dice = roll.num_dice - difficulty_to_use

        for i in range(num_dice):
            result = random.randint(1, roll.dice_size)

            results.append(result)

        effective_highest = max(results)

        total = sum(results)

        formatted_results = cls.format_roll(results, [], effective_highest, difficulty_to_use)

        return effective_highest, formatted_results, downgrade, total

    @classmethod
    def format_roll(cls, rolled: Iterable[int], indices_to_remove: Iterable[int], highest: int, difficulty_to_use: int = 0) -> List[str]:
        formatted = super().format_roll(rolled, indices_to_remove, highest)

        for i in range(difficulty_to_use):
            formatted.append('_')

        return formatted

    @functools.lru_cache()
    def get_result(self, highest: int, downgrade: int = 0) -> str:
        new_result = self.apply_downgrade(highest, downgrade)

        for threshold, outcome in self.CORE_RESULTS.items():
            if threshold <= new_result:
                return self.CORE_RESULTS[threshold]

        return self.CORE_RESULTS[1]

    @classmethod
    def compute_downgrade_map(cls):
        flat_results: List[Tuple[int, int]] = sorted(cls.CORE_RESULTS.items(), key=lambda i: i[0], reverse=True)

        downgrade_map = {}

        for index, (threshold, outcome) in enumerate(flat_results):
            if threshold == 1:
                downgrade_map[threshold] = threshold
                break
            else:
                next_threshold = flat_results[index + 1][0]

                downgrade_map[threshold] = next_threshold

                for value in range(next_threshold + 1, threshold + 1):
                    downgrade_map[value] = next_threshold

        return downgrade_map

    def create_character(self, spreadsheet_id: str, sheet_name: str) -> SpireCharacter:
        return SpireCharacter(spreadsheet_id, sheet_name)

    @staticmethod
    def from_data(game_data: Dict[str, Any]) -> 'SpireGame':
        required_fields = ['guild_id', 'system', 'spreadsheet_id', 'less_lethal']

        for required_field in required_fields:
            if required_field not in game_data:
                raise ValueError(f'Cannot load a Spire game without a "{required_field}" field.')

        if game_data['system'] != System.SPIRE.value:
            raise ValueError(f'Cannot load a Spire game from a non-Spire savedata file.')

        if not isinstance(game_data['less_lethal'], bool):
            raise ValueError(f'"less_lethal" must be a bool, not "{game_data["less_lethal"]}" ')

        characters = []

        if 'characters' in game_data:
            for discord_username, character_data in game_data['characters'].items():
                try:
                    character = HeartCharacter.load(character_data)
                    characters.append(character)
                except ValueError as v:
                    get_logger().error(v)
                    continue

        game = SpireGame(
            guild_id=game_data['guild_id'],
            spreadsheet_id=game_data['spreadsheet_id'],
            less_lethal=game_data['less_lethal'],
            characters=characters
        )

        return game

    @property
    def game_data(self):
        game_data = super().game_data

        game_data['less_lethal'] = self.less_lethal

        return game_data

    def __str__(self):
        return f'A {"less lethal " if self.less_lethal else ""}Spire Game with Guild ID "{self.guild_id}" and the following characters: {[character.character_name for character in self.character_sheets.values()]}'

class HeartGame(Game):
    """
    Represents a Discord server using the bot for a Heart game.
    """

    TAGS = {
        # Resource tags
        'Harmful': 'The resource has the capacity to harm those who carry it via black magic, illness or strange energies. ',
        'Fragile': 'The resource will be destroyed if dropped or damaged. ',
        'Awkward': 'The resource is heavy or hard to carry. ',
        'Deteriorating': 'The resource is breaking down, rotting or rusting and you’ll need to get it to a new owner quickly. ',
        'Taboo': 'The resource isn\'t accepted for barter in most haunts (e.g. organs from Heartsblooded people, gold teeth or certain narcotics). ',
        'Volatile': 'The resource may explode if mistreated. ',
        'Mobile': 'If left unattended, the resource will leave of its own accord.',
        'Beacon': 'The resource attracts something dangerous towards its position. ',
        'Niche': 'The resource is only valuable to a very select group of people.',
        'Block': '+1 Blood protection. ',

        # Equipment tags
        'Bloodbound': 'Mark D4 stress to Blood to roll with mastery when using this equipment for the rest of the situation. ',
        'Brutal': 'When you roll for stress against an adversary when using this item, roll two dice and pick the highest.Multiple instances of this tag stack: if you managed to get it three times, you’d roll four dice and pick the highest when calculating stress. ',
        'Conduit': 'Mark D4 stress to Mind to roll with mastery when using this equipment for the rest of the situation. ',
        'Dangerous': 'When you inflict stress with this item and roll the maximum amount, mark D6 stress to Blood. ',
        'Debilitating': 'Once per situation, when you inflict stress with this item to one or more targets, the next attack made against them is rolled with mastery. ',
        'Degenerating': 'If you take damage from a weapon with this tag, roll Endure+[Domain] at the end of the situation. On a failure, mark D6 stress; on a partial success, mark D4 stress; on a success, mark none. ',
        'Distressing': 'When you inflict stress with this item and roll the maximum amount, mark D6 stress to Mind.',
        'Double-Barreled': 'As Reload, but you can use the item twice before reloading. ',
        'Expensive': 'When you inflict stress with this item and roll the maximum amount, mark D6 stress to Supplies.',
        'Extreme Range': 'This item can be used at extreme range.',
        'Limited X': 'You can use this X times before it gives out. ',
        'Loud': 'When you inflict stress with this item and roll the maximum amount, mark D6 stress to Fortune. ',
        'Obscuring': 'The bearer and any nearby allies reduce the damage of incoming and outgoing ranged weapons by 1 step.',
        'One-Shot': 'This equipment takes a very long time to prepare, so you can only use it once per situation. ',
        'Piercing': 'You cannot reduce stress inflicted by this equipment by using Blood Protection, and adversaries do not benefit from their protection value. POINT-',
        'Blank': 'As Ranged, but at very close range it increases its stress dice by one step. If the shot travels far enough to spread out and dissipate, it lowers its stress dice by one step. ',
        'Potent': 'When you roll for stress removed from yourself or an ally with this item, roll two dice and pick the highest. Multiple instances of this tag stack as per the Brutal tag. ',
        'Ranged': 'This equipment can be used at range. ',
        'Reload': 'This equipment must be reloaded between uses, giving enemies a chance to close in or flee. ',
        'Smoke': 'As Obscuring, but only when the item is used, and only around the area it was used. ',
        'Spread': 'Anyone standing near the target on a successful use must roll Evade+Domain (or another applicable skill) to avoid marking stress as well. On a partial success, downgrade the stress dice by one size. NPCs caught in a blast simply take the stress. ',
        'Tiring': 'When you fail an action using this equipment, the size of its stress dice decreases by 1 for the remainder of the situation. ',
        'Trusty': 'When you roll for stress marked against a delve while using this item, roll two dice and pick the highest. Multiple instances of this tag stack as per the Brutal tag. ',
        'Unreliable': 'When you fail an action using this equipment, it cannot be used for the remainder of the situation if in a landmark or for the remainder of the journey if on a delve. ',
        'Wyrd': 'When you inflict stress with this item and roll the maximum amount, mark D6 stress to Echo.'
    }

    DIFFICULTIES = {
        'Risky': 1,
        'Dangerous': 2,
    }

    CORE_RESULTS = {
        10: 'Critical Success (Increase outgoing Stress dice by 1 step)',
        8: 'Success (no stress)',
        6: 'Success at a Cost (stress, one dice size lower if avoiding damage)',
        2: 'Failure (stress)',
        1: 'Critical Failure (double stress)'
    }

    DIFFICULT_ACTIONS_TABLE = {
        10: 'Success at a Cost (stress, one dice size lower if avoiding damage)',
        2: 'Failure (stress)',
        1: 'Critical Failure (double stress)'
    }

    FALLOUT_LEVELS = {
        'Moderate': {
            'threshold': 7,
            'clear': 'all stress'
        },
        'Minor': {
            'threshold': 2,
            'clear': 'all stress in the resistance'
        },
        'no': {
            'threshold': 0,
            'clear': None
        },
    }

    RESISTANCES = ['Blood', 'Echo', 'Mind', 'Fortune', 'Supplies']

    RESERVED_SHEET_NAMES = [
        'Credits',
        'Changelog',
        'Lines and Veils',
        'Notes',
        'GM Tracker',

        # 'Example Character Sheet' # TODO Re-enable when done testing
        'Rules Engine w/ Expanded Abilities',
        'Original Rules Engine'
    ]

    def __init__(self, guild_id: int, spreadsheet_id: str, characters: Optional[List[HeartCharacter]] = None):
        super().__init__(guild_id, spreadsheet_id, System.HEART)

        if characters is None:
            characters = []

        characters = [character for character in characters if character.discord_username is not None]

        if len(characters) == 0:
            for sheet_id, sheet_name in self.spreadsheet_metadata.items():
                if sheet_name not in self.RESERVED_SHEET_NAMES:
                    self.logger.debug(sheet_name)

                    try:
                        character = HeartCharacter(
                            spreadsheet_id=spreadsheet_id,
                            sheet_name=sheet_name,
                        )

                        if character.discord_username is not None:
                            characters.append(character)

                    except ValueError as v:
                        self.logger.error(v, exc_info=True)
                        continue

        for character in characters:
            self.add_character(character)

        self.save()

    def add_character(self, character: HeartCharacter):
         self.character_sheets[character.discord_username] = character

    @classmethod
    def simple_roll(cls, roll: Roll) -> Tuple[int, List[str], bool, int]:
        results = []

        use_difficult_actions_table, difficulty_to_use = cls.compute_downgrade_difficulty(roll.num_dice, roll.difficulty)

        num_dice = roll.num_dice - difficulty_to_use

        for i in range(num_dice):
            result = random.randint(1, roll.dice_size)

            results.append(result)

        highest = max(results)

        indices_to_remove = []
        if use_difficult_actions_table:
            effective_highest = highest
        elif difficulty_to_use > 0:
            sorted_results = sorted(enumerate(results), key=lambda i: i[1])

            indices_to_remove = [idx for idx, value in sorted_results[-difficulty_to_use : ]]

            effective_highest = max([value for index, value in results if index not in indices_to_remove])
        else:
            effective_highest = highest

        total = sum(results)

        formatted_results = cls.format_roll(results, indices_to_remove, effective_highest)

        return effective_highest, formatted_results, use_difficult_actions_table, total

    @classmethod
    def compute_downgrade_difficulty(cls, num_dice: int, difficulty: int) -> Tuple[bool, int]:
        if num_dice > difficulty:
            new_difficulty = difficulty
            use_difficult_actions_table = False
        else:
            new_difficulty = 0
            use_difficult_actions_table = True

        return use_difficult_actions_table, new_difficulty

    def roll_check(self, user: discord.Member, skill: HeartSkill, domain: HeartDomain, initial_roll: Roll) -> Tuple[int, List[str], str, int, bool, bool, bool]:
        roll = initial_roll

        has_skill, has_domain = self.get_character(user).check_skill_and_domain(skill, domain)

        if has_skill:
            roll.num_dice += 1

        if has_domain:
            roll.num_dice += 1

        highest, formatted_results, use_difficult_actions_table, total = self.simple_roll(roll)

        outcome = self.get_result(highest, use_difficult_actions_table)

        return highest, formatted_results, outcome, total, has_skill, has_domain, use_difficult_actions_table

    def roll_fallout(self, user: discord.Member) -> Tuple[int, Literal['no', 'Minor', 'Major'], Optional[str], int]:
        character = self.get_character(user)

        stress = character.get_fallout_stress()

        rolled = random.randint(1, 12)

        fallout_level = 'no'
        stress_removed = self.FALLOUT_LEVELS['no']['clear']

        if rolled < stress:
            for fallout_level, fallout_level_data in self.FALLOUT_LEVELS.items():
                if stress >= fallout_level_data['threshold']:
                    stress_removed = fallout_level_data['clear']
                    break

        return rolled, fallout_level, stress_removed, stress

    @functools.lru_cache()
    def get_result(self, highest: int, use_difficult_actions_table: bool = False) -> str:
        if use_difficult_actions_table:
            for threshold, outcome in self.DIFFICULT_ACTIONS_TABLE.items():
                if threshold <= highest:
                    return self.DIFFICULT_ACTIONS_TABLE[threshold]

            return self.DIFFICULT_ACTIONS_TABLE[1]
        else:
            for threshold, outcome in self.CORE_RESULTS.items():
                if threshold <= highest:
                    return self.CORE_RESULTS[threshold]

            return self.CORE_RESULTS[1]

    @classmethod
    def pick_highest(cls, rolled: Iterable[int], difficulty: int) -> int:
        if difficulty == 0:
            highest = max(rolled)
        else:
            sorted_results = sorted(rolled)

            highest = max(sorted_results[:-difficulty])

        return highest

    def get_character_names(self) -> List[str]:
        names = []

        for character_sheet in self.character_sheets.values():
            names.append(character_sheet.character_name)

        return names

    def create_character(self, spreadsheet_id: str, sheet_name: str) -> HeartCharacter:
        return HeartCharacter(spreadsheet_id, sheet_name)

    @staticmethod
    def from_data(game_data: Dict[str, Any]) -> 'HeartGame':
        required_fields = ['guild_id', 'system', 'spreadsheet_id']

        for required_field in required_fields:
            if required_field not in game_data:
                raise ValueError(f'Cannot load a Heart game without a "{required_field}" field.')

        if game_data['system'] != System.HEART.value:
            raise ValueError(f'Cannot load a Heart game from a non-Heart savedata file.')

        characters = []

        for discord_username, character_data in game_data['characters'].items():
            try:
                character = HeartCharacter.load(character_data)
                characters.append(character)
            except ValueError as v:
                get_logger().error(v)
                continue

        game = HeartGame(
            guild_id=game_data['guild_id'],
            spreadsheet_id=game_data['spreadsheet_id'],
            characters=characters
        )

        return game

    def __str__(self):
        return f'A Heart Game with Guild ID "{self.guild_id}" and the following characters: {[character.character_name for character in self.character_sheets.values()]}'
