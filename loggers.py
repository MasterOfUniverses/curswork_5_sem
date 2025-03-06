import logging
import json
from datetime import datetime

DEBUG_FILE_NAME = "debug.log"
OUTPUT_FILE_NAME = "output.txt"
ERROR_FILE_NAME = "error.log"
IS_DEBUG_MODE = False
OUTPUT_FORMATTER = logging.Formatter(fmt = '%(message)s',datefmt = '%d/%m/%Y %H:%M:%S')

def setup_logger(name:str, file_path:str, level = logging.INFO, formatter:logging.Formatter = logging.Formatter(fmt = '%(levelname)s:%(asctime)s: ___ %(message)s',datefmt = '%d/%m/%Y %H:%M:%S')):
    logger = logging.getLogger(name)
    handler = logging.FileHandler(file_path)
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    now = datetime.now().strftime("%H:%M:%S")
    logger.critical(f"{name}: new run : {now}")
    logger.setLevel(level)
    return logger

ERROR_LOGGER = setup_logger(name ="error",file_path = ERROR_FILE_NAME, level=logging.ERROR)

DEBUG_LOGGER = setup_logger(name ="debug",file_path = DEBUG_FILE_NAME, level=logging.DEBUG)

OUTPUT_LOGGER = setup_logger(name ="output",file_path = OUTPUT_FILE_NAME, formatter=OUTPUT_FORMATTER)
