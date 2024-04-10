import unittest
import logging

if __name__ == '__main__':
    logging.disable(logging.ERROR)

    discovered_tests = unittest.TestLoader().discover('tests', pattern='Test*.py')

    suite = unittest.TestSuite([discovered_tests])

    unittest.TextTestRunner(verbosity=2).run(suite)

    logging.disable(logging.NOTSET)
