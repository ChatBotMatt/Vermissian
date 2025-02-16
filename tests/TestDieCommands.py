import unittest
import unittest.mock

import logging

from vermissian.Vermissian import Vermissian
from src.overcharge.commands import classless_roll
from src.Roll import Roll, Cut

@unittest.skip("Temporary")
class TestDieCommands(unittest.TestCase):

    @unittest.mock.patch('src.Roll.random.randint')
    def test_classless_roll(self, mock_roll):
        for base_num_dice in range(0, 5):
            for difficulty in range(0, 3):
                for advantages in range(0, 4):
                    for disadvantages in range(0, 4):
                        roll_values = [4, 5, 2, 1, 6, 3, 4]

                        mock_roll.side_effect = roll_values

                        expected_num_dice = max(base_num_dice + advantages - disadvantages, 0)

                        zero_dice_pool = False
                        if expected_num_dice <= 0:
                            expected_num_dice = 2 # Roll 2, take lower
                            zero_dice_pool = True

                        expected_results = roll_values[: expected_num_dice]

                        if zero_dice_pool:
                            indexed_expected_results = list(enumerate(expected_results))

                            expected_kept_results = [ min(indexed_expected_results, key=lambda t: t[1])[1] ]
                            expected_indices_to_remove = [ max(indexed_expected_results, key=lambda t: t[1])[0] ]
                        else:
                            expected_kept_results = expected_results
                            expected_indices_to_remove = []

                        if difficulty > 0:
                            if difficulty >= len(expected_kept_results):
                                expected_kept_results = []
                                expected_indices_to_remove = list(range(len(expected_results)))
                            else:
                                expected_indices_to_remove, expected_kept_results = Roll.cut_rolls(expected_results, Cut(num=difficulty, threshold=4), highest_first=False)

                        roll_made, results, indices_to_remove, kept_results, rolled_zero_pool = classless_roll(
                            base_num_dice,
                            advantages,
                            disadvantages,
                            difficulty
                        )

                        with self.subTest('Number of dice rolled', base_num_dice=base_num_dice, difficulty=difficulty, advantages=advantages, disadvantages=disadvantages):
                            self.assertEqual(
                                expected_num_dice,
                                len(results)
                            )

                        with self.subTest('Results', base_num_dice=base_num_dice, difficulty=difficulty, advantages=advantages, disadvantages=disadvantages):
                            self.assertEqual(
                                expected_results,
                                results
                            )

                        with self.subTest('Kept Results', base_num_dice=base_num_dice, difficulty=difficulty, advantages=advantages, disadvantages=disadvantages):
                            self.assertEqual(
                                expected_kept_results,
                                kept_results
                            )

                        with self.subTest('Indices to Remove', base_num_dice=base_num_dice, difficulty=difficulty, advantages=advantages, disadvantages=disadvantages):
                            self.assertEqual(
                                expected_indices_to_remove,
                                indices_to_remove
                            )

    def setUp(self) -> None:
        logging.disable(logging.ERROR)

        self.vermissian = Vermissian()

    def tearDown(self) -> None:
        logging.disable(logging.NOTSET)


if __name__ == '__main__':
    unittest.main()
