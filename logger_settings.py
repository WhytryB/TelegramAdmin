import sys

import config
import logging


logging.basicConfig(filename='logfile_' + config.PROJECT_NAME + '.log', level=logging.ERROR)
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(config.PROJECT_NAME)
logger.addHandler(logging.StreamHandler(sys.stdout))
