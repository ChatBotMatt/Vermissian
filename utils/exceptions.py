import abc

from System import System

class VermissianError(Exception, abc.ABC):
    """
    Represents an expected error that we can safely print to the user.
    """

class NoGameError(VermissianError):

    def __init__(self, msg: str = 'You need to link to a character keeper before you can do that. Use /link', * args):
        super().__init__(msg, * args)

class NoCharacterError(VermissianError):

    def __init__(self, msg: str = 'You need to link yourself to a character before you can do that. Use /add_character', * args):
        super().__init__(msg, * args)

class BadCharacterKeeperError(VermissianError):
    def __init__(self, msg: str = 'The character keeper URL "{}" is not valid. It should look like "https://docs.google.com/spreadsheets/d/1saogmy4eNNKng32Pf39b7K3Ko4uHEuWClm7UM-7Kd8I/edit#gid=0" (potentially with different spreadsheet ID and gid)', * args, spreadsheet_url: str):
        super().__init__(msg.format(spreadsheet_url), * args)

class NoSpreadsheetGidError(VermissianError):
    def __init__(self, msg: str = 'Cannot parse character sheet URL "{}" - no gid found. It should look like "https://docs.google.com/spreadsheets/d/1saogmy4eNNKng32Pf39b7K3Ko4uHEuWClm7UM-7Kd8I/edit#gid=0" (potentially with different values)', * args, spreadsheet_url: str):
        super().__init__(msg.format(spreadsheet_url), * args)

class UnknownSystemError(VermissianError):
    def __init__(self, msg: str = 'Unknown system: "{}". Valid systems are {}', * args, system: str):
        super().__init__(msg.format(system, list([sys.value for sys in System])), * args)

class NoDiceError(VermissianError):
    """
    Represents someone trying to roll a non-positive number of dice.
    """

    def __init__(self, msg: str = 'Must roll at least 1 dice, not {}.', * args, num_dice: int):
        super().__init__(msg.format(num_dice), * args)

class NoSidesError(VermissianError):
    """
    Represents someone trying to roll dice with a non-positive number of sides.
    """

    def __init__(self, msg: str = 'Dice must have at least 1 side to physically exist, not {}.', * args, dice_size: int):
        super().__init__(msg.format(dice_size), * args)

class WrongDifficultyError(VermissianError):

    def __init__(self, msg: str = 'Difficulty must be between 0 and 2 inclusive, not {}', * args, difficulty: int):
        super().__init__(msg.format(difficulty), * args)

class NotARollError(VermissianError):
    def __init__(self, msg: str = 'This was not a roll.', * args):
        super().__init__(msg, * args)

class ForbiddenSpreadsheetError(VermissianError):
    def __init__(self, msg: str = 'Access to the spreadsheet is forbidden. Please make sure that you have given View access to anyone with the link.', * args, spreadsheet_id: str):
        super().__init__(msg.format(spreadsheet_id), * args)