import logging
import logging.config
import click_logging
import sys
import time
from itertools import cycle
from shutil import get_terminal_size
from threading import Thread

__all__ = [
    "get_logger",
    "SpinCursor", "SpinCursor2"

]

# ================================== FUNCTIONS ###############################
def get_logger(name: str, log_level="DEBUG",
               to_file: str = '', file_log_level="DEBUG") -> logging.Logger:
    echo_kwargs = {
        'error': dict(err=True),
        'exception': dict(err=True),
        'critical': dict(err=True),
    }
    style_kwargs = {
        'error': dict(fg='red', blink=True),
        'critical': dict(fg='red', blink=True),
        'warning': dict(fg='orange', blink=True),
        'exception': dict(fg='yellow', blink=True),        
        'info': dict(fg='cyan', blink=True),
        'debug': dict(fg='green', blink=True)
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
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - [%(levelname)s] - %(message)s',
            datefmt='%d/%B/%Y %I:%M:%S %p')
        fh.setFormatter(formatter)
        logger.addHandler(fh)

    return logger


# ============================== CLASSES ==============================
class SpinCursor(Thread):
    """ A console spin cursor class 
    """
    
    def __init__(self, cursor_type:str="bar"):
        """Choose one of `spin` and `bar`"""
        self.t = Thread(target=self.animate)
        # This will make the thread stop if the main process
        # is killed (i.e. from a KeyboardInterrupt)
        self.t.daemon=True

        if cursor_type == 'bar':
            self.bar = [
                " [=     ]",
                " [ =    ]",
                " [  =   ]",
                " [   =  ]",
                " [    = ]",
                " [     =]",
                " [    = ]",
                " [   =  ]",
                " [  =   ]",
                " [ =    ]",
            ]
        elif cursor_type == 'spin':
            self.bar = ['|', '/', '-', '\\']
        else:
            raise NotImplementedError("choose one [`spin`, `bar`].")

        self.bar_len = len(self.bar)
        self.flag = True
        
    def animate(self):
        i = 0
        while self.flag:
            # print(self.bar[i % self.bar_len], end="\r")
            sys.stdout.write('\r' + self.bar[i % self.bar_len])
            sys.stdout.flush()
            time.sleep(.15)
            i += 1
        sys.stdout.write('              \ndone!             ')
        sys.stdout.write('\n')

    def start(self):
        self.t.start()

    def stop(self):
        self.flag = False


class SpinCursor2:
    def __init__(self, desc="Loading...", end="Done!", timeout=0.1):
        """
        A loader-like context manager
        source: https://stackoverflow.com/questions/22029562/python-how-to-make-simple-animated-loading-while-process-is-running

        Args:
            desc (str, optional): The loader's description. Defaults to "Loading...".
            end (str, optional): Final print. Defaults to "Done!".
            timeout (float, optional): Sleep time between prints. Defaults to 0.1.
        """
        self.desc = desc
        self.end = end
        self.timeout = timeout

        self._thread = Thread(target=self._animate, daemon=True)
        self.steps = ["⢿", "⣻", "⣽", "⣾", "⣷", "⣯", "⣟", "⡿"]
        self.done = False

    def start(self):
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
        self.done = True
        cols = get_terminal_size((80, 20)).columns
        print("\r" + " " * cols, end="", flush=True)
        print(f"\r{self.end}", flush=True)

    def __exit__(self, exc_type, exc_value, tb):
        # handle exceptions with those variables ^
        self.stop()