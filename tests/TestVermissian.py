import unittest
import itertools
from typing import List, Tuple

from utils.format import strikethrough, bold
from Vermissian import Vermissian

class TestVermissian(unittest.TestCase):

    def get_rolls(self) -> List[Tuple[int, ...]]:
        all_rolled = []

        thresholds = list(range(1, 10 + 1))

        for size in range(1, 5 + 1):
            for combination in itertools.combinations(thresholds, size):
                all_rolled.append(combination)

        return all_rolled

    def setUp(self) -> None:
        self.spire_vermissian = Vermissian(game_type='spire')

if __name__ == '__main__':
    unittest.main()
