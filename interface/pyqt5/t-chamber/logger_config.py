import logging
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path
from datetime import datetime
import coloredlogs

def setup_logger(name=__name__, console_level=logging.INFO, file_level=logging.INFO):

    coloredlogs.install()

    logs = (Path.cwd()) / 'logs' # set path to log files
    logs.mkdir(exist_ok=True)  # create 'logs' directory if it doesn't already exist

    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    console_handler = logging.StreamHandler()  # console display logs updates
    console_handler.setLevel(console_level)

    date_str = datetime.now().strftime("%Y-%m-%d")  # create datetime string for file names
    # create the date-named files (one per day) and keep them for 30 days, then rotate the oldest ones out
    time_handler = TimedRotatingFileHandler(logs / f'{date_str}.log', when='D', interval=1, backupCount=30, encoding="utf-8", delay=False)

    # define format for log messages
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                                  datefmt='%Y-%m-%d %H:%M:%S')

    # apply the format to both kinds of log handlers
    console_handler.setFormatter(formatter)
    time_handler.setFormatter(formatter)

    # create logger handlers, if they do not already exist
    if not logger.handlers:
        logger.addHandler(console_handler)
        logger.addHandler(time_handler)

    return logger