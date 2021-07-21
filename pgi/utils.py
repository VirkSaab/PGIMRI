import logging
import logging.config
import click_logging


__all__ = ["get_logger"]


def get_logger(name: str, log_level="DEBUG",
               to_file: str = '', file_log_level="DEBUG") -> logging.Logger:
    echo_kwargs = {
        'error': dict(err=True),
        'exception': dict(err=True),
        'critical': dict(err=True),
    }
    style_kwargs = {
        'error': dict(fg='red', blink=True),
        'exception': dict(fg='red', blink=True),
        'critical': dict(fg='red', blink=True),
        'info': dict(fg='cyan', blink=True)
    }
    logger = logging.getLogger(f"logger_name: {name}")
    ch = click_logging.ClickHandler(echo_kwargs=echo_kwargs)
    ch.setLevel(eval(f"logging.{log_level}"))
    ch.setFormatter(click_logging.ColorFormatter(style_kwargs=style_kwargs))
    logger.addHandler(ch)

    if to_file != '':
        fh = logging.FileHandler(to_file)
        fh.setLevel(eval(f"logging.{file_log_level}"))
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%d/%B/%Y %I:%M:%S %p')
        fh.setFormatter(formatter)
        logger.addHandler(fh)

    return logger
