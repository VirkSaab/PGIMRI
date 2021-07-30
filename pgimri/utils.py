import logging
import logging.config
import click_logging
import time
from itertools import cycle
from shutil import get_terminal_size
from threading import Thread
from pgimri.config import *


__all__ = [
    # Functions
    "get_logger",

    # Classes
    "SpinCursor"
]

# ================================== FUNCTIONS ###############################


def get_logger(name: str, log_level=LOG_LEVEL,
               to_file: str = LOG_FILENAME, file_log_level=FILE_LOG_LEVEL) -> logging.Logger:
    """A wrapper to create a logger with console and file handlers."""
    echo_kwargs = {
        'error': dict(err=True),
        'exception': dict(err=True),
        'critical': dict(err=True),
    }
    style_kwargs = {
        'error': dict(fg='red', blink=True),
        'critical': dict(fg='red', blink=True),
        'warning': dict(fg='yellow', blink=True),
        'exception': dict(fg='yellow', blink=True),
        'info': dict(fg='cyan', blink=True),
        'debug': dict(fg='green', blink=True),
        'todo': dict(fg='green', blink=True)

    }
    logger = logging.getLogger(f"logger_name: {name}")
    logger.setLevel(log_level)
    ch = click_logging.ClickHandler(echo_kwargs=echo_kwargs)
    ch.setLevel(log_level)
    ch.setFormatter(click_logging.ColorFormatter(style_kwargs=style_kwargs))
    logger.addHandler(ch)

    if to_file != '':
        fh = logging.FileHandler(to_file)
        fh.setLevel(file_log_level)
        formatter = logging.Formatter(LOGGING_FILE_FORMAT,
                                      datefmt=LOGGING_DATEFMT)
        fh.setFormatter(formatter)
        logger.addHandler(fh)

    return logger


# ============================== CLASSES ==============================
class SpinCursor:
    """A waiting animation when program is being executed. 

        `reference source (stackoverflow) <https://stackoverflow.com/questions/22029562/python-how-to-make-simple-animated-loading-while-process-is-running>`_ 

        Args:
            desc : The loader's description. Defaults to "Loading...".
            end : Final print. Defaults to "Done!".
            cursor_type : Set the animation type. Choose one out of
                'bar', 'spin', or 'django'.
            timeout : Sleep time between prints. Defaults to 0.1.

        Example:
            Using *with* context:

            .. code-block:: python

                with SpinCursor("Running...", end=f"done!!"):
                    subprocess.run(['ls', '-l'])
                    time.sleep(10)

            Using normal code:

            .. code-block:: python

                cursor = SpinCursor("Running...", end=f"done!!")
                cursor.start()
                subprocess.run(['ls', '-l'])
                time.sleep(10)
                cursor.stop()

        Returns: 
            Nothing
        """

    def __init__(self, desc:str="Loading...", end:str="Done!", cursor_type:str="bar", timeout:float=0.1) -> None:

        self.desc = desc
        self.end = end
        self.timeout = timeout

        self._thread = Thread(target=self._animate, daemon=True)

        if cursor_type == 'bar':
            self.steps = [
                "[=     ]",
                "[ =    ]",
                "[  =   ]",
                "[   =  ]",
                "[    = ]",
                "[     =]",
                "[    = ]",
                "[   =  ]",
                "[  =   ]",
                "[ =    ]",
            ]
        elif cursor_type == 'spin':
            self.steps = ['|', '/', '-', '\\']
        elif cursor_type == 'django':
            self.steps = ["⢿", "⣻", "⣽", "⣾", "⣷", "⣯", "⣟", "⡿"]
        else:
            raise NotImplementedError("choose one [`spin`, `bar`, `django`].")

        self.done = False

    def start(self):
        """Start the animation. See example above."""
        self._thread.start()
        return self

    def _animate(self):
        for c in cycle(self.steps):
            if self.done:
                break
            print(f"\r{self.desc} {c}", flush=True, end="")
            time.sleep(self.timeout)

    def __enter__(self):
        self.start()

    def stop(self):
        """Stop animation. See example above."""
        self.done = True
        cols = get_terminal_size((80, 20)).columns
        print("\r" + " " * cols, end="", flush=True)
        print(f"\r{self.end}", flush=True)

    def __exit__(self, exc_type, exc_value, tb):
        # handle exceptions with those variables ^
        self.stop()
