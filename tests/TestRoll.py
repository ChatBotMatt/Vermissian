import unittest

from Roll import Roll, NoSidesError, NoDiceError, WrongDifficultyError, NotARollError

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

                'Roll 3d6 + 3.5, 1d4-2, 4d10': ([
                    Roll(num_dice=3, dice_size=6),
                    Roll(num_dice=1, dice_size=4, penalty=2),
                    Roll(num_dice=4, dice_size=10),
                    ], None),

                'Roll 3d6 + 3.5, 1d4-2.5, 4d10': ([
                    Roll(num_dice=3, dice_size=6),
                    Roll(num_dice=1, dice_size=4),
                    Roll(num_dice=4, dice_size=10),
                    ], None),

                'Roll 3d6 + a, 1d4-2, 4d10': ([
                    Roll(num_dice=3, dice_size=6),
                    Roll(num_dice=1, dice_size=4, penalty=2),
                    Roll(num_dice=4, dice_size=10),
                    ], None),

                'Roll 3d6 - a, 1d4-2, 4d10': ([
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

            'Difficulty': {
                'Roll 3d6 Difficulty 0': (
                    [
                      Roll(num_dice=3, dice_size=6, difficulty=0),
                    ],
                    None
                ),
                'Roll 3d6 Difficulty 1': ([
                    Roll(num_dice=3, dice_size=6, difficulty=1),
                    ], None),

                'Roll 3d6 Difficulty 1 Difficulty 2': ([
                    Roll(num_dice=3, dice_size=6, difficulty=2),
                    ], None),

                'Roll 3d6, 1d4, Difficulty 0': ([
                    Roll(num_dice=3, dice_size=6, difficulty=0),
                    Roll(num_dice=1, dice_size=4, difficulty=0),
                    ], None),

                'Roll 3d6, 1d4, Difficulty 1': ([
                    Roll(num_dice=3, dice_size=6, difficulty=1),
                    Roll(num_dice=1, dice_size=4, difficulty=1),
                    ], None)
            },

            'Multiple Difficulties': {
                'Roll 3d6, 1d4, Difficulty 1, Difficulty 2': ([
                    Roll(num_dice=3, dice_size=6, difficulty=2),
                    Roll(num_dice=1, dice_size=4, difficulty=2),
                    ], None),

                'Roll 3d6, 1d4, Difficulty 1 Difficulty 2': ([
                    Roll(num_dice=3, dice_size=6, difficulty=2),
                    Roll(num_dice=1, dice_size=4, difficulty=2),
                    ], None)
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

                'Roll 3d6 + 1, 1d4-2, 4d10 Difficulty 1 # This is a roll to pick a lock': (
                    [
                        Roll(num_dice=3, dice_size=6, bonus=1, difficulty=1),
                        Roll(num_dice=1, dice_size=4, penalty=2, difficulty=1),
                        Roll(num_dice=4, dice_size=10, difficulty=1),
                    ],
                    "This is a roll to pick a lock"
                ),

                'Roll 3d6 + 1, 1d4-2, 4d10 Difficulty 1# This is a roll to pick a lock': (
                    [
                        Roll(num_dice=3, dice_size=6, bonus=1, difficulty=1),
                        Roll(num_dice=1, dice_size=4, penalty=2, difficulty=1),
                        Roll(num_dice=4, dice_size=10, difficulty=1),
                    ],
                    "This is a roll to pick a lock"
                ),

                'Roll 3d6 + 1, 1d4-2, 4d10 Difficulty 1# This is a roll to # pick a lock': (
                    [
                        Roll(num_dice=3, dice_size=6, bonus=1, difficulty=1),
                        Roll(num_dice=1, dice_size=4, penalty=2, difficulty=1),
                        Roll(num_dice=4, dice_size=10, difficulty=1),
                    ],
                    "This is a roll to # pick a lock"
                ),

                'roll 3d6 + 1, 1d4-2, 4d10 Difficulty 1# This is a roll to # pick a lock': (
                    [
                        Roll(num_dice=3, dice_size=6, bonus=1, difficulty=1),
                        Roll(num_dice=1, dice_size=4, penalty=2, difficulty=1),
                        Roll(num_dice=4, dice_size=10, difficulty=1),
                    ],
                    "This is a roll to # pick a lock"
                )
            }
        }

        invalid_test_cases = {
            'Broken up': [
                'Roll 3 d6',
                'Roll 3 d6',
                'Roll 3 d 6',
                'Roll 3d 6',
            ],

            'Wrong order': [
                'Roll 1 + 3d6',
            ],

            'Missing Data': [
                'Roll 3d6, 1d4, Difficulty',
                'Roll 3d6, 1d4, Diff',
                ('# This is a roll to pick a lock', NotARollError),
                'Roll 3d',
                'Roll',
                'Roll ',
                ('Roll 0d6', NoDiceError),
                ('Roll 3d0', NoSidesError),
                ('Roll 0d0', NoDiceError),
                ('Roll 3d6 Difficulty 3', WrongDifficultyError),
                ('apples', NotARollError),
                # ('Roll 3d-1', NoSidesError) # TODO Can't get this to parse nicely
                'Roll 3d-1',
                'Roll 3d+1'
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

                    with self.subTest(f'Testing "{roll_str_to_use}" with "{transformer}"', roll_str=roll_str_to_use, expected_exception_cls=expected_exception_cls, transformer=transformer):
                        transformed = transformation(roll_str_to_use)

                        self.assertRaises(
                            expected_exception_cls,
                            Roll.parse_roll,
                            transformed
                        )

    def setUp(self) -> None:
        pass

if __name__ == '__main__':
    unittest.main()
