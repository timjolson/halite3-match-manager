import logging

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

from .keyboard_detection import keyboard_detection, KeyStop


class MultilineFormatter(logging.Formatter):
    """
    Isnpired by https://stackoverflow.com/a/45217732
    """

    def format(self, record: logging.LogRecord):
        save_msg = record.msg
        if not isinstance(save_msg, str):
            save_msg = str(save_msg)
        output = ""
        for line in save_msg.splitlines():
            record.msg = line
            output += super().format(record) + "\n"
        output = output[:-1]
        record.msg = save_msg
        record.message = output
        return output
