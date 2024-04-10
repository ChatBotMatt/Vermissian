import logging
import sys

class VermissianLogFormatter(logging.Formatter):
    fmts = {
        'error': '%(asctime)s %(name)s - %(levelname)s - %(pathname)s %(lineno)s - %(message)s - %(sinfo)s',
        'debug': '%(asctime)s %(name)s - %(levelname)s - %(pathname)s %(lineno)s - %(message)s - %(sinfo)s',
        'info':  '%(asctime)s %(name)s - %(levelname)s - %(pathname)s %(lineno)s - %(message)s'
    }

    def __init__(self):
        super().__init__(self.fmts['info'])

    def format(self, record: logging.LogRecord):
        original_format = self._fmt

        # Replace the original format with one customized by logging level
        if record.levelno == logging.DEBUG:
            self._fmt = VermissianLogFormatter.fmts['debug']

        elif record.levelno == logging.INFO:
            self._fmt = VermissianLogFormatter.fmts['info']

        elif record.levelno in [logging.WARNING, logging.ERROR, logging.CRITICAL]:
            self._fmt = VermissianLogFormatter.fmts['error']

        # Call the original formatter class to do the grunt work
        result = logging.Formatter.format(self, record)

        self._fmt = original_format

        return result

def get_logger(level: str = 'INFO'):
    if not hasattr(get_logger, 'logger'):
        logger = logging.getLogger('Vermissian')

        logger.root.addHandler(logging.FileHandler('vermissian.log', mode='w', encoding='utf-8'))
        logger.root.addHandler(logging.StreamHandler(sys.stdout))

        formatter = VermissianLogFormatter()

        get_logger.logger = logger
        get_logger.level = None
        get_logger.formatter = formatter

    if get_logger.level != level:
        get_logger.logger.root.setLevel(level)

        for handler in get_logger.logger.root.handlers:
            handler.setLevel(level)
            handler.setFormatter(get_logger.formatter)

        get_logger.level = level

    return get_logger.logger
