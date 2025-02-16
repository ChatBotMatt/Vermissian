import discord

import unittest.mock
import logging

from src.System import System
from vermissian.Vermissian import Vermissian
from src.commands import get_donate, get_privacy_policy, should_respond, BOT_USER_IDS
from vermissian.commands import get_credits, get_ability, get_about, get_legal, get_debugging_page_content, \
    get_getting_started_page_content, format_ability
from extract_abilities import Ability

class TestCommands(unittest.TestCase):

    def test_should_respond(self):
        vermissian_mock_member = unittest.mock.MagicMock(discord.Member)
        vermissian_mock_member.id = BOT_USER_IDS['Vermissian']

        ghost_detector_mock_member = unittest.mock.MagicMock(discord.Member)
        ghost_detector_mock_member.id = BOT_USER_IDS['Ghost Detector']

        other_mock_member = unittest.mock.MagicMock(discord.Member)
        other_mock_member.id = 50

        with self.subTest('Vermissian is prioritised over Ghost Detector'):
            vermissian_should = should_respond(
                'Vermissian',
                [
                    vermissian_mock_member,
                    ghost_detector_mock_member,
                    other_mock_member
                ]
            )

            self.assertTrue(vermissian_should)

            ghost_detector_should = should_respond(
                'Ghost Detector',
                [
                    vermissian_mock_member,
                    ghost_detector_mock_member,
                    other_mock_member
                ]
            )

            self.assertFalse(ghost_detector_should)

        with self.subTest('Vermissian doesn\'t talk if not in the channel'):
            vermissian_should = should_respond(
                'Vermissian',
                [
                    ghost_detector_mock_member,
                    other_mock_member
                ]
            )

            self.assertFalse(vermissian_should)

        with self.subTest('Ghost Detector can talk if Vermissian isn\'t there'):
            ghost_detector_should = should_respond(
                'Ghost Detector',
                [
                    ghost_detector_mock_member,
                    other_mock_member
                ]
            )

            self.assertTrue(ghost_detector_should)

    def test_message_limits(self):
        """
        Test that no command's response will exceed 2000 characters.
        """

        discord_character_limit = 2000

        command_responders = [
            get_credits,
            get_about,
            get_debugging_page_content,
            get_getting_started_page_content,
            get_privacy_policy,
            get_legal,
            get_donate
        ]

        for responder in command_responders:
            name = responder.__name__
            response = responder()

            with self.subTest(f'Testing message limit for {name}'):
                self.assertLessEqual(
                    len(response),
                    discord_character_limit
                )

    def test_get_ability(self):

        # TODO Don't love this, but unit testing lazy loads is a pain.
        # TODO Can I mock the attribute?
        get_ability('Arbitrary', None) # Make it lazy-load the abilities.

        with self.subTest('Has abilities attribute'):
            self.assertTrue(hasattr(get_ability, 'abilities'))

        with self.subTest('Spire Ability'):
            expected_spire_ability_name = 'Cut a Deal'
            expected_spire_ability = Ability.from_json({
                "class_calling": "Azurite",
                "name": "Cut A Deal",
                "description": "Once per session, set up a meet with an NPC who can acquire you pretty much anything available in Spire. It won\u2019t be free, though, and odds are they\u2019ll want a favour or a cut too.",
                "source": "Core Book",
                "tier": "Core"
            })

            response = get_ability(expected_spire_ability_name, None)

            self.assertEqual(
                format_ability(expected_spire_ability, System.SPIRE.value),
                response
            )

        with self.subTest('Heart Ability'):
            expected_heart_ability_name = 'Heartsblood'
            expected_heart_ability = Ability.from_json({
                "class_calling": "Cleaver",
                "name": "Heartsblood",
                "description": "Your minimum protection value for all resistances is equal to the tier of the Heart you are currently on. This value doesn\u2019t add to other sources of protection, but your base protection can\u2019t be lower than your current tier unless you specifically lose access to it due to fallout.",
                "source": "Core Book",
                "tier": "Core"
            })

            response = get_ability(expected_heart_ability_name, None)

            self.assertEqual(
                format_ability(expected_heart_ability, System.HEART.value),
                response
            )

        with self.subTest('Ability in Both'):
            expected_ability_name = 'Sacrifice'

            expected_spire_ability = Ability.from_json({
                "class_calling": "Shadow Agent",
                "name": "Sacrifice",
                "description": "You can \u201ckill\u201d a cover \u2013 removing access to it \u2013 by sacrificing it upon an altar to Our Hidden Mistress in a night-long ritual. When you do so, clear all your current stress and any fallout you suffered whilst inhabiting the cover. If it\u2019s unclear what fallout you suffered when you were inhabiting the cover, the fallout stays with you.",
                "source": "Strata",
                "tier": "Medium"
            })

            expected_heart_ability = Ability.from_json({
                "class_calling": "Junk Mage",
                "name": "Sacrifice",
                "description": "Before you cast a spell from this class, you can opt to destroy a resource with the Occult domain.\n\nRoll the resource\u2019s dice; the amount rolled is added to your Protection value against any stress incurred as a result of casting the spell.",
                "source": "Core Book",
                "tier": "Core"
            })

            response = get_ability(expected_ability_name, None)
            expected_response = format_ability(expected_spire_ability, System.SPIRE.value) + '\n------------\n' + format_ability(expected_heart_ability, System.HEART.value)

            self.assertEqual(
                response,
                expected_response
            )

        with self.subTest('Overly-long ability'):
            lengthy_ability_description = 'abc' * 2000

            lengthy_ability = Ability(
                name='Lengthy Fake Ability',
                description=lengthy_ability_description,
                class_calling='Test',
                source='Test',
                tier='Test'
            )

            get_ability.abilities[System.SPIRE.value][lengthy_ability.name.lower()] = lengthy_ability

            response = get_ability(lengthy_ability.name, None)
            expected_response = f'The ability is very long so some of it is cut off\n\n' + format_ability(lengthy_ability, System.SPIRE.value)
            expected_response = expected_response[:2000]

            self.assertEqual(
                response,
                expected_response
            )

        for system in [None, System.HEART, System.SPIRE]:
            with self.subTest(f'Test missing abilities - {system}'):
                fake_ability_name = 'Ability that does not exist'
                response = get_ability(fake_ability_name, system)

                self.assertRegex(
                    response,
                    f'Cannot find ability "{fake_ability_name}"'
                )

    def setUp(self) -> None:
        logging.disable(logging.ERROR)

        self.vermissian = Vermissian()

    def tearDown(self) -> None:
        logging.disable(logging.NOTSET)


if __name__ == '__main__':
    unittest.main()
