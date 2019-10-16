import logging
import sys
import os
import termios
from select import select

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


class KeyStop(Exception):
    pass


class keyboard_detection:
    """
    Use in a with statement to enable the appropriate terminal mode to detect keyboard presses
    without blocking for input.  Used this way, the with statement puts a boolean detection
    function in the target variable.  The resulting function can be called any number of times
    until a keypress is detected.  Sample code:

    with keyboard_detection() as key_pressed:
        while not key_pressed():
            sys.stdout.write('.')
            sys.stdout.flush()
            sleep(0.5)
    print 'done'

    Upon exiting the with code block, the terminal is reverted to its calling (normal) state.
    The sys.stdout.flush() is important when in the keyboard detection mode; otherwise, text
    output won't be seen.
    """

    def __enter__(self):
        # save the terminal settings
        self.fd = sys.stdin.fileno()
        self.new_term = termios.tcgetattr(self.fd)
        self.old_term = termios.tcgetattr(self.fd)

        # new terminal setting unbuffered
        self.new_term[3] = (self.new_term[3] & ~termios.ICANON & ~termios.ECHO)

        # switch to unbuffered terminal
        termios.tcsetattr(self.fd, termios.TCSAFLUSH, self.new_term)

        return self.query_keyboard

    def __exit__(self, type, value, traceback):
        # swith to normal terminal
        termios.tcsetattr(self.fd, termios.TCSAFLUSH, self.old_term)

    def query_keyboard(self, keys=(b'q',)):
        dr, dw, de = select([sys.stdin], [], [], 0)
        key = None
        if dr:
            key = os.read(sys.stdin.fileno(), 1)
        return key in keys


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
