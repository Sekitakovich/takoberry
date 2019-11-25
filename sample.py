import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('Log')
# logger.setLevel(logging.DEBUG)

logger.debug(msg='DEBUG')
logger.error(msg='ERROR')
logger.info(msg='INFO')