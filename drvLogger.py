import logging
import sys

#init the logger configuration, TO CHANGE -- Log File Path !
def initLogger():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(message)s')

    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setLevel(logging.DEBUG)
    stdout_handler.setFormatter(formatter)

    file_handler = logging.FileHandler('logs.log')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)


    logger.addHandler(file_handler)
    logger.addHandler(stdout_handler)

    
    logger.info('----------------------------------')
    logger.info('logger set up corretly')
    #return logger

## this is for testings, probably no longer needed.
## just add the import in the module needed and use :
#
#   import logging
#   logger = logging.getLogger(__name__)

def log(logger):
    logger.info('This is a log message!')
    logger.error('This is an error message.')