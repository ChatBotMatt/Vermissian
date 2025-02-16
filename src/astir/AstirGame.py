import random
import functools
from typing import List, Dict, Tuple, Iterable, Optional, Any

from src.System import System
from src.astir.AstirCharacterSheet import AstirCharacter, AstirTrait
from src.Roll import Roll, Cut
from src.utils.format import strikethrough
from src.utils.logger import get_logger
from src.utils.exceptions import UnknownSystemError, BotError

from src.Game import CharacterKeeperGame

class AstirGame(CharacterKeeperGame):
    """
    Represents a Discord server using the bot to play an Armour Astir: Advent game.
    """

    TAGS = {
        -2: {
            'Cursed': 'You cannot wield anything else once you raise a cursed weapon, and it becomes bound to you until the curse is broken. When you die it will consume your essence, probably. ',
            'Dangerous': 'Volatile or difficult to use safely, dangerous objects invite dire consequences if not used carefully. Once per Sortie, the director may upgrade a risk you acquire while using something dangerous to a peril. ',
            'Dreaded': 'This weapon has a history and a reputation that stains it, and stains you as long as you\'re carrying it. People will treat you with fear and apprehension. ',
            'Huge': 'Basically impossible to move around without help. Absolutely not something you are ever going to hide, either. ',
            'Junk': 'In such a terrible condition it cannot be used. You may remove this tag with a 6-step longterm project. ',
            'One-Use': 'Can only be used a single time per Sortie - perhaps it needs time to recharge, or uses rare ammo, or explodes. ',
            'Treasure': 'Highly valuable - and a gold, glittering target on your back. Increases value by +4. ',
        },
        -1: {
            '2H': 'Takes both hands to use properly, though not necessarily just to carry. ',
            'Bulky': 'Large (relative to tier) and difficult or awkward to move around. ',
            'Drain': 'This object draws excessive power from an Astir, and reduces the Astir\'s Power by 1 while equipped. Objects can have this tag multiple times, increasing the reduction. ',
            'Distinct': 'Impressive, loud, or just particularly memorable, distinct equipment is hard to be subtle with. Might make you easy to track or follow, or ruin your attempts at stealth. ',
            'Slow': 'There is a delay involved in this objects use, like the travel time of a projectile, or the low speed of a construct. Might, for example, impose disadvantage where speed matters. ',
            'Limited': 'You have a particularly limited supply or use of this thing - it always seems to run out at the most perilous moments. ',
            'Messy': 'Something messy is imprecise (or indiscriminate), and could have excessive (or intimidating), unwanted results. ',
            'Intimate': 'Requires you to get to get up close and personal, making it hard to use against anyone wielding something with better reach - or anyone just trying to keep their distance. ',
            'Fragile': 'Easily broken, either by shoddy design or frail materials. ',
            'Forbidden': 'Forbidden objects are banned by the Authority, and possession of them or suspicion of such carries a heavy price. ',
            'Set-Up': 'Make moves using this item at disadvantage unless you spend time prepare or arm it in some way. In battle this might only be a few moments, but it can make all the difference. ',
            'Reload': 'After firing, this weapon requires you to manually reload it or perform some other action to ready it for use. ',
            'Unreliable': 'This object is prone to failure and breakdowns - make your first move with it each Scene in desperation. ',
            'Weak': 'Lacking in physical impact, and generally useless for piercing armour or cover. ',
            'Valuable': 'Expensive to acquire, and fairly sought-after. Increases value by +2. ',
        },

        1: {
            'Adapted': 'This object has been modified or designed to let it overcome the difficulties of certain environments - it might be an amphibious Astir with an air supply, an Ardent designed to keep it\'s occupants cool in searing-hot terrains, etc. ',
            'Arcane / Divine / Elemental / Mundane / Profane': 'This tag changes your approach to the listed one while you\'re actively using it.',
            'Area': 'This weapon affects a large area: while any melee weapon might hit multiple people stood right next to each-other, an area weapon might slice through an entire crowd or several spreadout foes. ',
            'Bane': 'You suffer no penalty against opponents one tier above you when attacking with bane. ',
            'Blitz': 'You may spend this tag once per Scene to make a move with confidence. ',
            'Concealable': 'Easily hidden - a casual inspection will rarely if ever find it. ',
            'Decisive': 'Decisive weaponry is precise and powerful, excellent for ending fights. Once per Scene, you may reroll a failed strike decisively when using it. ',
            'Defensive': 'Defensive weaponry is excellent for keeping foes at a distance, parrying their blows, or suppressing them. Once per Scene, you may reroll a failed exchange blows when using it. ',
            'Impact': 'This weapon packs a heavy physical punch, capable of knocking foes down or away easily, and will dent or break through surfaces. ',
            'Infinite': 'This thing either doesn\'t use ammo or power to function, or uses such small amounts relative to your supply that it is practically endless. You\'re never in danger of running out as a result of a roll. ',
            'Guided': 'This weapon has guided strikes or projectiles, allowing you to take a 7-9 result when you exchange blows and strike decisively rather than rolling if you wish. Guided projectiles are reliable, but leave little room for finesse. ',
            'Mounted': 'This weapon is mounted or worn in some way that frees up the hands of the user for other tasks. As a result, it\'s also difficult to disarm a target of without breaking it. ',
            'Restraining': 'Can restrict or slow targets down in some way, making it hard for them to escape or move without expending a lot of effort. ',
            'Refresh': 'Objects that refresh can only be used once per Scene, but automatically replenish or restore themselves even if they are destroyed or wasted (they cannot be taken away from you by a peril). ',
            'Ward': 'You may use this tag once per Sortie to reduce an incoming source of harm from a peril to a risk, or from a risk to nothing. ',
        },

        2: {
            'Ruin': 'As per bane, but up to two tiers higher rather than one. ',
            'Versatile': 'This tag combines the effects of decisive and defensive. ',
            'Vorpal': 'Vorpal weaponry is exceedingly lethal: you may use this tag once per Sortie to upgrade a risk you\'d inflict to a peril instead.',
        }
    }

    RESERVED_SHEET_NAMES = [
        'HOME',
        'Update Log',
        'Cause / Factions',
        'Moves & Rules',
        'Downtime',
        'Conflict Turn',
        'Authority / Divisions',
        'Base Factions',
        'Base Divisions',
        'Cantrips & Soldier Moves',
        'Math',
    ]

    def __init__(self, guild_id:  int, spreadsheet_id: str, characters: Optional[List[AstirCharacter]] = None):
        super().__init__(guild_id, spreadsheet_id, System.ASTIR, characters)

    @classmethod
    def load(cls, guild_id: int) -> 'AstirGame':
        game_data = cls.load_game_data(guild_id)

        if int(game_data['guild_id']) != guild_id:
            raise ValueError(f'Guild IDs do not match up, cannot load data.')

        if game_data['system'] == System.ASTIR.value:
            return AstirGame.from_data(game_data)
        else:
            raise UnknownSystemError(system=game_data['system'])

    @classmethod
    def format_roll(cls, rolled: Iterable[int], indices_to_remove: Iterable[int]) -> List[str]:
        formatted_results = []

        str_cast = lambda s: str(s)

        for index, roll in enumerate(rolled):
            if index in indices_to_remove:
                formatter = strikethrough
            else:
                formatter = str_cast

            formatted_results.append(formatter(roll))

        return formatted_results

    def get_character(self, username: str) -> AstirCharacter:
        return super().get_character(username)

    def roll_check(
        self,
        username: str,
        initial_roll: Roll,
        trait: Optional[AstirTrait] = None,
        num_advantages: int = 0,
        num_disadvantages: int = 0,
        confidence: bool = False,
        desperation: bool = False,
        modifier: int = 0
    ) -> Tuple[int, List[str], List[str], int, bool, bool, str]:
        roll = initial_roll

        if trait is None:
            trait_modifier = 0
            warning = ''
        else:
            trait_modifier, warning = self.get_character(username).get_trait(trait)

        overall_modifier = trait_modifier + modifier

        if overall_modifier > 0:
            roll.bonus += overall_modifier
        elif overall_modifier < 0:
            roll.penalty += abs(overall_modifier)

        total, formatted_results, formatted_confidence_desperation_results, had_advantage, had_disadvantage = self.roll(
            initial_roll=roll,
            num_advantages=num_advantages,
            num_disadvantages=num_disadvantages,
            confidence=confidence,
            desperation=desperation
        )

        return total, formatted_results, formatted_confidence_desperation_results, overall_modifier, had_advantage, had_disadvantage, warning

    @classmethod
    def apply_confidence(cls, results: List[int]) -> List[int]:
        confidence_results = []

        for result in results:
            if result == 1:
                confidence_results.append(6)
            else:
                confidence_results.append(result)

        return confidence_results

    @classmethod
    def apply_desperation(cls, results: List[int]) -> List[int]:
        desperation_results = []

        for result in results:
            if result == 6:
                desperation_results.append(1)
            else:
                desperation_results.append(result)

        return desperation_results

    @classmethod
    def roll(
        cls,
        initial_roll: Roll,
        num_advantages: int = 0,
        num_disadvantages: int = 0,
        confidence: bool = False,
        desperation: bool = False
    ) -> Tuple[int, List[str], List[str], bool, bool]:
        results = []

        if confidence and desperation:
            raise BotError(f'Cannot roll with both confidence *and* desperation.')

        new_num_dice = min(4, initial_roll.num_dice + abs(num_advantages - num_disadvantages))

        has_advantage = False
        has_disadvantage = False

        if num_advantages > num_disadvantages:
            has_advantage = True
            cut = Cut(num=num_advantages - num_disadvantages, threshold=0)
            cut_highest_first = False
        elif num_disadvantages > num_advantages:
            has_disadvantage = True
            cut = Cut(num=num_disadvantages - num_advantages, threshold=0)
            cut_highest_first = True
        else:
            cut_highest_first = False
            cut = None

        roll = Roll( # TODO Make a from_roll function
            num_dice=new_num_dice,
            dice_size=initial_roll.dice_size,
            cut=cut,
            drop=initial_roll.drop,
            bonus=initial_roll.bonus,
            penalty=initial_roll.penalty
        )

        for i in range(roll.num_dice):
            result = random.randint(1, roll.dice_size)

            results.append(result)

        if confidence:
            confidence_desperation_results = AstirGame.apply_confidence(results)
        elif desperation:
            confidence_desperation_results = AstirGame.apply_desperation(results)
        else:
            confidence_desperation_results = results

        indices_to_remove, kept_results = roll.cut_rolls(confidence_desperation_results, cut, highest_first=cut_highest_first)

        total = sum(kept_results) + roll.bonus - roll.penalty

        # TODO May be a little odd since the indices being removed may initially look wrong
        # Should be fine if I only print out the initial ones when not doing conf_desp though? Or at least better
        formatted_results = cls.format_roll(results, indices_to_remove)
        formatted_confidence_desperation_results = cls.format_roll(confidence_desperation_results, indices_to_remove)

        return total, formatted_results, formatted_confidence_desperation_results, has_advantage, has_disadvantage

    def create_character(self, spreadsheet_id: str, sheet_name: str) -> AstirCharacter:
        return AstirCharacter(spreadsheet_id, sheet_name)

    @staticmethod
    def from_data(game_data: Dict[str, Any]) -> 'AstirGame':
        required_fields = ['guild_id', 'system', 'spreadsheet_id']

        for required_field in required_fields:
            if required_field not in game_data:
                raise ValueError(f'Cannot load an Astir game without a "{required_field}" field.')

        if game_data['system'] != System.ASTIR.value:
            raise ValueError(f'Cannot load an Astir game from a non-Astir savedata file.')

        characters = []

        if 'characters' in game_data:
            for discord_username, character_data in game_data['characters'].items():
                try:
                    character = AstirCharacter.load(character_data)
                    characters.append(character)
                except ValueError as v:
                    get_logger().error(v)
                    continue

        game = AstirGame(
            guild_id=game_data['guild_id'],
            spreadsheet_id=game_data['spreadsheet_id'],
            characters=characters
        )

        return game

    def __str__(self):
        return f'An Astir Game with Guild ID "{self.guild_id}", Spreadsheet ID {self.spreadsheet_id}, and the following characters: {[str(character) for character in self.character_sheets.values()]}'
