import logging
from pythonjsonlogger import jsonlogger

def configure_logging(level: str):
    logger = logging.getLogger()
    logger.setLevel(level)
    for h in list(logger.handlers):
        logger.removeHandler(h)
    handler = logging.StreamHandler()
    formatter = jsonlogger.JsonFormatter(fmt='%(asctime)s %(levelname)s %(name)s %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger
