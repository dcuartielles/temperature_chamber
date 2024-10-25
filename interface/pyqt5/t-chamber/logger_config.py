import logging
from datetime import datetime
from pathlib import Path


def setup_logger(name=__name__, console_level=logging.INFO, file_level=logging.INFO):

    logs = str(Path.cwd())  # set

    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(console_level)
    time_handler = TimedRotatingFileHandler(f'{logs}/app_daily.log', when='D', interval=1, backupCount=30, encoding="utf-8", delay=False)

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                                  datefmt='%Y-%m-%d %H:%M:%S')

    console_handler.setFormatter(formatter)
    time_handler.setFormatter(formatter)

    if not logger.handlers:
        logger.addHandler(console_handler)
        logger.addHandler(time_handler)

    return logger
