import random
from dataclasses import dataclass
from typing import List, Dict, Any, Literal, Iterable, Optional

from src.System import System
from src.utils.format import strikethrough, bold
from src.utils.exceptions import UnknownSystemError

from src.Game import Game

@dataclass
class Card:
    value: str
    suit: Literal['Clubs', 'Hearts', 'Spades', 'Diamonds']

    def to_json(self):
        return {
            'value': self.value,
            'suit': self.suit
        }

    def __hash__(self):
        return hash(self.value) + hash(self.suit)

class GhostGame(Game):
    """
    Represents a Discord server using the bot to play a "Get Out, Run!" game.
    """

    def __init__(self, guild_id: int, cards: Optional[List[Card]] = None):
        super().__init__(guild_id=guild_id, system=System.GHOST_GAME)

        if cards is None:
            self.refresh_cards()
        else:
            self.cards = cards

    def refresh_cards(self):
        replacements = {
            1: 'Ace',
            11: 'Jack',
            12: 'Queen',
            13: 'King'
        }

        self.cards = []

        for idx in range(1, 13):
            for suit in ['Clubs', 'Hearts', 'Spades', 'Diamonds']:
                if idx in replacements:
                    value = replacements[idx]
                else:
                    value = idx

                self.cards.append(Card(value=str(value), suit=suit))

    def draw_card(self) -> Optional[Card]:
        if len(self.cards):
            card_idx = random.randint(0, len(self.cards) - 1)

            card = self.cards.pop(card_idx)

            return card
        else:
            return None

    @classmethod
    def load(cls, guild_id: int) -> 'GhostGame':
        game_data = cls.load_game_data(guild_id)

        if int(game_data['guild_id']) != guild_id:
            raise ValueError(f'Guild IDs do not match up, cannot load data.')

        if game_data['system'] == System.GHOST_GAME.value:
            return GhostGame.from_data(game_data)
        else:
            raise UnknownSystemError(system=game_data['system'])

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

    @property
    def game_data(self):
        game_data = super().game_data

        game_data['cards'] = [card.to_json() for card in self.cards]

        return game_data

    @staticmethod
    def from_data(game_data: Dict[str, Any]) -> 'GhostGame':
        required_fields = ['guild_id']

        for required_field in required_fields:
            if required_field not in game_data:
                raise ValueError(f'Cannot load a "Get Out, Run!" game without a "{required_field}" field.')

        if game_data['system'] != System.GHOST_GAME.value:
            raise ValueError(f'Cannot load a "Get Out, Run!" game from a non-"Get Out, Run!" savedata file.')

        game = GhostGame(
            guild_id=game_data['guild_id'],
            cards=[Card(** card_data) for card_data in game_data['cards']]
        )

        return game
