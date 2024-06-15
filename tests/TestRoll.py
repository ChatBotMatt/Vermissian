import unittest
import logging

from src.Roll import Roll, NoSidesError, NoDiceError, NotARollError


class TestRoll(unittest.TestCase):

    def test_parse_roll(self):
        valid_test_cases = {
            'Simple': {
                'Roll 3d6': (
                    [
                        Roll(num_dice=3, dice_size=6),
                    ],
                    None
                ),

                'Roll 3d6, 1d4': ([
                                      Roll(num_dice=3, dice_size=6),
                                      Roll(num_dice=1, dice_size=4),
                                  ], None),

                'Roll 3d6,1d4': ([
                                     Roll(num_dice=3, dice_size=6),
                                     Roll(num_dice=1, dice_size=4),
                                 ], None),

                'Roll 3d60,10d4': ([
                                       Roll(num_dice=3, dice_size=60),
                                       Roll(num_dice=10, dice_size=4),
                                   ], None),

                'Roll 3d60,10d40': ([
                                        Roll(num_dice=3, dice_size=60),
                                        Roll(num_dice=10, dice_size=40),
                                    ], None),

                'Roll 3d6 4d4': (
                    [
                        Roll(num_dice=3, dice_size=6),
                        Roll(num_dice=4, dice_size=4)
                    ],
                    None
                ),

                'Roll d6': (
                    [
                        Roll(num_dice=1, dice_size=6),
                    ],
                    None
                ),

                'Roll d6 + 2d4': (
                    [
                        Roll(num_dice=1, dice_size=6),
                        Roll(num_dice=2, dice_size=4)
                    ],
                    None
                )
            },

            'Modifiers': {
                'Roll 3d6 + 1, 1d4': ([
                                          Roll(num_dice=3, dice_size=6, bonus=1),
                                          Roll(num_dice=1, dice_size=4),
                                      ], None),

                'Roll 3d6 + 1, 1d4-2': ([
                                            Roll(num_dice=3, dice_size=6, bonus=1),
                                            Roll(num_dice=1, dice_size=4, penalty=2),
                                        ], None),

                'Roll 3d6 + 1, 1d4-2+3': ([
                                              Roll(num_dice=3, dice_size=6, bonus=1),
                                              Roll(num_dice=1, dice_size=4, penalty=2, bonus=3),
                                          ], None),

                'Roll 3d6 + 1, 1d4 - 2 +3': ([
                                                 Roll(num_dice=3, dice_size=6, bonus=1),
                                                 Roll(num_dice=1, dice_size=4, penalty=2, bonus=3),
                                             ], None),

                'Roll 3d6 + 1, 1d4 - 2 + 3': ([
                                                  Roll(num_dice=3, dice_size=6, bonus=1),
                                                  Roll(num_dice=1, dice_size=4, penalty=2, bonus=3),
                                              ], None),

                'Roll 3d6 + 1 + 2 -1, 1d4': ([
                                                 Roll(num_dice=3, dice_size=6, bonus=3, penalty=1),
                                                 Roll(num_dice=1, dice_size=4),
                                             ], None),

                'Roll 3d6 + 1, 1d4-2, 4d10': ([
                                                  Roll(num_dice=3, dice_size=6, bonus=1),
                                                  Roll(num_dice=1, dice_size=4, penalty=2),
                                                  Roll(num_dice=4, dice_size=10),
                                              ], None),

                'Roll 3d6 + 0, 1d4-2, 4d10': ([
                                                  Roll(num_dice=3, dice_size=6),
                                                  Roll(num_dice=1, dice_size=4, penalty=2),
                                                  Roll(num_dice=4, dice_size=10),
                                              ], None),

                'Roll 3d6 + 1 + 3, 1d4-2, 4d10': ([
                                                      Roll(num_dice=3, dice_size=6, bonus=4),
                                                      Roll(num_dice=1, dice_size=4, penalty=2),
                                                      Roll(num_dice=4, dice_size=10),
                                                  ], None),

                'Roll 3d6 + 51, 1d4-22, 4d10': ([
                                                    Roll(num_dice=3, dice_size=6, bonus=51),
                                                    Roll(num_dice=1, dice_size=4, penalty=22),
                                                    Roll(num_dice=4, dice_size=10),
                                                ], None)
            },

            'Cut': {
                'Roll 3d6 Cut 0': ([
                                       Roll(num_dice=3, dice_size=6, cut=0),
                                   ], None),
                'Roll 3d6 Cut 1': ([
                                       Roll(num_dice=3, dice_size=6, cut=1),
                                   ], None),

                'Roll 3d6, 1d4, Cut 0': ([
                                             Roll(num_dice=3, dice_size=6, cut=0),
                                             Roll(num_dice=1, dice_size=4, cut=0),
                                         ], None),

                'Roll 3d6, 1d4, Cut 1': ([
                                             Roll(num_dice=3, dice_size=6, cut=1),
                                             Roll(num_dice=1, dice_size=4, cut=1),
                                         ], None)
            },

            'Drop': {
                'Roll 3d6 Drop 0': (
                    [
                        Roll(num_dice=3, dice_size=6, drop=0),
                    ], 
                    None
                ),
                
                'Roll 3d6 Drop 1': (
                    [
                        Roll(num_dice=3, dice_size=6, drop=1),
                    ], 
                    None
                ),

                'Roll 3d6, 1d4, Drop 0': (
                    [
                        Roll(num_dice=3, dice_size=6, drop=0),
                        Roll(num_dice=1, dice_size=4, drop=0),
                    ], 
                    None
                ),

                'Roll 3d6, 1d4, Drop 1': (
                    [
                        Roll(num_dice=3, dice_size=6, drop=1),
                        Roll(num_dice=1, dice_size=4, drop=1),
                    ], 
                    None
                )
            },

            'Multiple Cuts': {
                'Roll 3d6 Cut 1 Cut 2': (
                    [
                        Roll(num_dice=3, dice_size=6, cut=2),
                    ],
                    None
                ),

                'Roll 3d6, 1d4, Cut 1, Cut 2': (
                    [
                        Roll(num_dice=3, dice_size=6, cut=2),
                        Roll(num_dice=1, dice_size=4, cut=2),
                    ],
                    None
                ),
            },

            'Multiple Drops': {
                'Roll 3d6 Drop 1 Drop 2': (
                    [
                        Roll(num_dice=3, dice_size=6, drop=2),
                    ],
                    None
                ),

                'Roll 3d6, 1d4, Drop 1, Drop 2': (
                    [
                        Roll(num_dice=3, dice_size=6, drop=2),
                        Roll(num_dice=1, dice_size=4, drop=2),
                    ],
                    None
                ),
            },

            'Cut and Drop': {
                'Roll 3d6 Cut 1 Drop 2': (
                    [
                        Roll(num_dice=3, dice_size=6, cut=1, drop=2),
                    ],
                    None
                ),

                'Roll 3d6, 1d4, Cut 1, Drop 1': (
                    [
                        Roll(num_dice=3, dice_size=6, cut=1, drop=1),
                        Roll(num_dice=1, dice_size=4, cut=1, drop=1),
                    ],
                    None
                ),

                'Roll 3d6, 1d4, Cut 2, Drop 1': (
                    [
                        Roll(num_dice=3, dice_size=6, cut=2, drop=1),
                        Roll(num_dice=1, dice_size=4, cut=2, drop=1),
                    ],
                    None
                ),

                'Roll 3d6, 1d4, Drop 2, Cut 1': (
                    [
                        Roll(num_dice=3, dice_size=6, cut=1, drop=2),
                        Roll(num_dice=1, dice_size=4, cut=1, drop=2),
                    ],
                    None
                ),

                'Roll 3d6 cut 5': (
                    [
                        Roll(num_dice=3, dice_size=6, cut=5),
                    ],
                    None
                ),

                'Roll 3d6 drop 5': (
                    [
                        Roll(num_dice=3, dice_size=6, drop=5),
                    ],
                    None
                ),
            },

            'Comments': {
                'Roll 3d6 + 1, 1d4-2, 4d10 # This is a roll to pick a lock': (
                    [
                        Roll(num_dice=3, dice_size=6, bonus=1),
                        Roll(num_dice=1, dice_size=4, penalty=2),
                        Roll(num_dice=4, dice_size=10),
                    ],
                    "This is a roll to pick a lock"
                ),

                'Roll 3d6 + 1, 1d4-2, 4d10 Cut 1 # This is a roll to pick a lock': (
                    [
                        Roll(num_dice=3, dice_size=6, bonus=1, cut=1),
                        Roll(num_dice=1, dice_size=4, penalty=2, cut=1),
                        Roll(num_dice=4, dice_size=10, cut=1),
                    ],
                    "This is a roll to pick a lock"
                ),

                'Roll 3d6 + 1, 1d4-2, 4d10 Cut 1# This is a roll to pick a lock': (
                    [
                        Roll(num_dice=3, dice_size=6, bonus=1, cut=1),
                        Roll(num_dice=1, dice_size=4, penalty=2, cut=1),
                        Roll(num_dice=4, dice_size=10, cut=1),
                    ],
                    "This is a roll to pick a lock"
                ),

                'Roll 3d6 + 1, 1d4-2, 4d10 Cut 1# This is a roll to # pick a lock': (
                    [
                        Roll(num_dice=3, dice_size=6, bonus=1, cut=1),
                        Roll(num_dice=1, dice_size=4, penalty=2, cut=1),
                        Roll(num_dice=4, dice_size=10, cut=1),
                    ],
                    "This is a roll to # pick a lock"
                ),
            }
        }

        invalid_test_cases = {
            'Broken up': [
                'Roll 3 d6',
                'Roll 3 d6',
                'Roll 3 d 6',
                'Roll 3d 6',
            ],

            'Bad syntax': [
                ('Roll 3d10 if you have the skill and the domain', ValueError),
                ('Roll 3d6 + 3.5, 1d4-2, 4d10', ValueError),
                ('Roll 3d6 + 3.5, 1d4-2.5, 4d10', ValueError),
                ('Roll 3d6 + a, 1d4-2, 4d10', ValueError),
                ('Roll 3d6 - a, 1d4-2, 4d10', ValueError),
                ('Roll 3d6 - a, 1d4-2, 4d10, Cut 1', ValueError),
                ('Roll 3d6, 1d4-2, 4d10, Cut 1.5', ValueError),
                ('Roll 3d6, 1d4-2, 4d10, Drop 1.5', ValueError)
            ],

            'Wrong order': [
                'Roll 1 + 3d6',
            ],

            'Missing Data': [
                'Roll 3d6, 1d4, Cut',
                'Roll 3d6, 1d4, Drop',
                ('# This is a roll to pick a lock', NotARollError),
                'Roll 3d',
                'Roll',
                'Roll ',
                ('Roll -1d6', NoDiceError),
                # 'Roll +3d6', # TODO Hugely an edge case, and can't figure out how to handle the general case without messing up the delimiters.
                ('Roll 0d6', NoDiceError),
                ('Roll 3d0', NoSidesError),
                ('Roll 0d0', NoDiceError),
                ('apples', NotARollError),
                ('Roll 3d-1', NoSidesError),
                # ('Roll 3d-', NoSidesError),  # TODO Can't get this to parse nicely, so it's a ValueError instead.
                'Roll 3d+1',
            ]
        }

        valid_transformers = {
            'identity': lambda s: s,
            'lower': lambda s: s.lower() if s is not None else None,
            'upper': lambda s: s.upper() if s is not None else None,

            'prepend_space': lambda s: ' ' + s if s is not None else None,
            'append_space': lambda s: s + ' ' if s is not None else None,
        }

        invalid_transformers = {
            'prepend': lambda s: 'Random text ' + s if s is not None else None,
            'remove_roll': lambda s: s[4:] if s is not None else None,
        }

        for label, trans in valid_transformers.items():
            invalid_transformers[label] = trans

        for group, group_cases in valid_test_cases.items():
            for roll_str, (expected_rolls, raw_expected_note) in group_cases.items():
                for transformer, transformation in valid_transformers.items():
                    with self.subTest(f'Testing "{roll_str}" with "{transformer}"', roll_str=roll_str, transformer=transformer):
                        transformed_roll_str = transformation(roll_str)

                        rolls, note = Roll.parse_roll(transformed_roll_str)

                        expected_note = transformation(raw_expected_note)

                        if expected_note is not None:
                            expected_note = expected_note.strip()

                        self.assertEqual(rolls, expected_rolls)
                        self.assertEqual(note, expected_note)

        for group, group_cases in invalid_test_cases.items():
            for roll_str in group_cases:
                for transformer, transformation in invalid_transformers.items():
                    if isinstance(roll_str, tuple):
                        if transformer in ['identity', 'lower', 'upper', 'prepend_space', 'append_space']:
                            roll_str_to_use, expected_exception_cls = roll_str
                        else:
                            roll_str_to_use, expected_exception_cls = roll_str[0], NotARollError
                    elif transformer in ['prepend', 'remove_roll']:
                        roll_str_to_use = roll_str
                        expected_exception_cls = NotARollError
                    else:
                        roll_str_to_use = roll_str
                        expected_exception_cls = ValueError

                    with self.subTest(f'Testing "{roll_str_to_use}" with "{transformer}"', roll_str=roll_str_to_use,
                                      expected_exception_cls=expected_exception_cls, transformer=transformer):
                        transformed = transformation(roll_str_to_use)

                        self.assertRaises(
                            expected_exception_cls,
                            Roll.parse_roll,
                            transformed
                        )

    def setUp(self) -> None:
        logging.disable(logging.ERROR)

    def tearDown(self) -> None:
        logging.disable(logging.NOTSET)


if __name__ == '__main__':
    unittest.main()
