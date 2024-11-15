import logging
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path
from datetime import datetime


def setup_logger(name=__name__, console_level=logging.INFO, file_level=logging.INFO):
    # define format for log messages
    fmt = "{asctime} - {name} - {levelname} - {message}"
    date_fmt = "%Y-%m-%d %H:%M:%S"

    # color formatting for different log levels
    formats = {
        logging.DEBUG: fmt,
        logging.INFO: f"\033[36m{fmt}\033[0m",      # cyan for info
        logging.WARNING: f"\033[33m{fmt}\033[0m",      # yellow for warning
        logging.ERROR: f"\033[1m\033[31m{fmt}\033[0m",    # bold red for error
        logging.CRITICAL: f"\033[1m\033[31m{fmt}\033[0m"    # bold red for critical
    }

    # custom formatter class to apply the color formatting
    class CustomFormatter(logging.Formatter):
        def format(self, record):
            log_fmt = formats.get(record.levelno, fmt)
            formatter = logging.Formatter(log_fmt, datefmt=date_fmt, style="{")
            return formatter.format(record)

    # set path to log files and create 'logs' directory if it doesn't exist
    logs = Path.cwd() / 'logs'
    logs.mkdir(exist_ok=True)

    # set up console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(CustomFormatter())
    console_handler.setLevel(console_level)

    # set up timed rotating file handler
    date_str = datetime.now().strftime("%Y-%m-%d")
    time_handler = TimedRotatingFileHandler(
        logs / f'{date_str}.log',
        when='D',
        interval=1,
        backupCount=7,
        encoding="utf-8",
        delay=False
    )
    time_handler.setFormatter(CustomFormatter())
    time_handler.setLevel(file_level)

    # configure the logger
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)  # set the base level to debug for comprehensive logging

    # add handlers to the logger if they haven't been added yet
    if not logger.handlers:
        logger.addHandler(console_handler)
        logger.addHandler(time_handler)

    return logger
