import string
import unittest
import logging

from utils.format import strikethrough, bold, underline, code, multiline_code, italics, quote, bullet, spoiler, no_embed

class TestFormat(unittest.TestCase):

    def test_strikethrough(self):
        for text in self.texts:
            expected = f'~~{text}~~'

            with self.subTest(text):
                self.assertEqual(
                    strikethrough(text),
                    expected
                )

    def test_bold(self):
        for text in self.texts:
            expected = f'**{text}**'

            with self.subTest(text):
                self.assertEqual(
                    bold(text),
                    expected
                )

    def test_underline(self):
        for text in self.texts:
            expected = f'__{text}__'

            with self.subTest(text):
                self.assertEqual(
                    underline(text),
                    expected
                )

    def test_code(self):
        for text in self.texts:
            expected = f'`{text}`'

            with self.subTest(text):
                self.assertEqual(
                    code(text),
                    expected
                )

    def test_multiline_code(self):
        for text in self.texts:
            expected = f'```{text}```'

            with self.subTest(text):
                self.assertEqual(
                    multiline_code(text),
                    expected
                )

    def test_italics(self):
        for text in self.texts:
            expected = f'*{text}*'

            with self.subTest(text):
                self.assertEqual(
                    italics(text),
                    expected
                )

    def test_quote(self):
        for text in self.texts:
            expected = f'> {text}'

            with self.subTest(text):
                self.assertEqual(
                    quote(text),
                    expected
                )

    def test_bullet(self):
        for text in self.texts:
            expected = f'* {text}'

            with self.subTest(text):
                self.assertEqual(
                    bullet(text),
                    expected
                )

    def test_spoiler(self):
        for text in self.texts:
            expected = f'||{text}||'

            with self.subTest(text):
                self.assertEqual(
                    spoiler(text),
                    expected
                )

    def test_no_embed(self):
        for text in self.texts:
            expected = f'<{text}>'

            with self.subTest(text):
                self.assertEqual(
                    no_embed(text),
                    expected
                )

    def setUp(self) -> None:
        logging.disable(logging.ERROR)

        self.texts = [
            * list(string.ascii_letters),
            'The quick dog jumps over the lazy cow',
        ]

    def tearDown(self) -> None:
        logging.disable(logging.NOTSET)

if __name__ == '__main__':
    unittest.main()