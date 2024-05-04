import re
from typing import List, Tuple, Optional

from src.utils.exceptions import NotARollError, NoSidesError, NoDiceError, WrongDifficultyError

class Roll:
    """
    Represents a roll to make.
    """

    def __init__(self, num_dice: int, dice_size: int, difficulty: int = 0, bonus: int = 0, penalty: int = 0):
        self.num_dice = num_dice
        self.dice_size = dice_size
        self.difficulty = difficulty
        self.bonus = bonus
        self.penalty = penalty

    def str_no_difficulty(self) -> str:
        s = f'{self.num_dice}d{self.dice_size}'

        if self.bonus > 0:
            s += f' + {self.bonus}'

        if self.penalty > 0:
            s += f' - {self.penalty}'

        return s

    def __str__(self):
        s = self.str_no_difficulty()

        if self.difficulty > 0:
            s += f' Difficulty {self.difficulty}'

        return s

    @property
    def num_dice(self):
        return self._num_dice

    @num_dice.setter
    def num_dice(self, num_dice: int):
        if num_dice < 1:
            raise NoDiceError(num_dice=num_dice)

        self._num_dice = num_dice

    @property
    def dice_size(self):
        return self._dice_size

    @dice_size.setter
    def dice_size(self, dice_size: int):
        if dice_size < 1:
            raise NoSidesError(dice_size=dice_size)

        self._dice_size = dice_size

    @property
    def difficulty(self):
        return self._difficulty

    @difficulty.setter
    def difficulty(self, difficulty: int):
        if difficulty < 0 or difficulty > 2:
            raise WrongDifficultyError(difficulty=difficulty)

        self._difficulty = difficulty

    def __eq__(self, other: 'Roll') -> bool:
        return self.__dict__ == other.__dict__

    @classmethod
    def parse_roll(cls, roll_str: str) -> Tuple[List['Roll'], Optional[str]]:
        rolls = []
        difficulty = 0

        if not roll_str.lower().strip().startswith('roll'):
            raise NotARollError()

        try:
            note_index = roll_str.index('#')

            note = roll_str[note_index+1: ].strip()
            note_parsed_roll_str = roll_str[: note_index]
        except ValueError:
            note = None
            note_parsed_roll_str = roll_str

        note_parsed_roll_str = note_parsed_roll_str.strip().lower()

        regex_formatters = {
            ' +': ' ', # Normalise multiple spaces

            ' [Dd](\d)': r' 1d\1', # Normalise dX syntax to 1dX

            '(\d)D(\d)': r'\1d\2', # Normalise casing of the d for dice.

            '(?: *,? *)diff(?:iculty)? (\d+)': r', difficulty_\1', # Normalise difficulty marker and combine it with the value.

            ' ?\+ ?(\d+)d(\d)': r', \1d\2',  # Normalise "+"-delimited dice to be comma-delimited.

            ' ?\+ ?(\d+)': r' +_\1', # Combine + with its value.

            ' ?- ?(\d+)': r' -_\1', # Combne - with its value.

            ',? ?(\d+)?d(\d+)': r', \1d\2', # Normalise potentially-missing spaces and commas to properly separate dice

            'roll,': 'roll' # Remove extraneous commmas
        }

        formatted_roll_str = note_parsed_roll_str
        for regex, replacement in regex_formatters.items():
            formatted_roll_str = re.sub(
                regex,
                replacement,
                formatted_roll_str,
                flags=re.IGNORECASE
            )

        trimmed_roll_str = formatted_roll_str[4: ].strip()

        tokens = [token.strip().lower() for token in trimmed_roll_str.split(',')]

        for token in tokens:
            difficulty_match = re.fullmatch(
                'difficulty_(\d+)',
                token
            )

            if difficulty_match is None:
                subtokens = [subtoken.strip() for subtoken in token.split(' ')]

                roll_match = re.fullmatch(
                    '(\d+)?d(\d+)',
                    subtokens[0]
                )

                if roll_match is None:
                    invalid_roll_match = re.fullmatch(
                        '(\d+)?d([+\-]\d+)',
                        subtokens[0]
                    )

                    if invalid_roll_match is not None:
                        raise NoSidesError(dice_size=invalid_roll_match.group(2))
                    else:
                        raise ValueError(f'First token must be a roll. Roll str was "{roll_str}", formatted to "{formatted_roll_str}", and first token was "{subtokens[0]}" in "{subtokens}".')
                else:
                    if roll_match.group(1) is None:
                        num_dice = 1
                    else:
                        num_dice = int(roll_match.group(1))

                    dice_size = int(roll_match.group(2))

                    bonus = 0
                    penalty = 0

                    if len(subtokens) > 1:
                        for subtoken in subtokens[1:]:
                            bonus_match = re.fullmatch(
                                '\+_(\d+)',
                                subtoken.strip()
                            )

                            if bonus_match is None:
                                penalty_match = re.fullmatch(
                                    '-_(\d+)',
                                    subtoken.strip()
                                )

                                if penalty_match is not None:
                                    penalty += int(penalty_match.group(1))
                                else:
                                    raise ValueError(f'Invalid subtoken found: "{subtoken}" in "{roll_str}" that was formatted to "{formatted_roll_str}".')
                            else:
                                bonus += int(bonus_match.group(1))

                    roll = Roll(num_dice=num_dice, dice_size=dice_size, bonus=bonus, penalty=penalty)

                    rolls.append(roll)

            else:
                difficulty = difficulty_match.group(1)

        for roll in rolls:
            roll.difficulty = int(difficulty)

        return rolls, note
