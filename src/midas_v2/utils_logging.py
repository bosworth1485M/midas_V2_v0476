import logging, os
from logging.handlers import RotatingFileHandler

def setup_logging(level: str = "INFO", log_dir: str = "logs", rotate_bytes: int = 1_048_576, backup_count: int = 5):
    os.makedirs(log_dir, exist_ok=True)
    logger = logging.getLogger("midas_v2")
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")

    ch = logging.StreamHandler()
    ch.setFormatter(fmt)
    logger.addHandler(ch)

    fh = RotatingFileHandler(os.path.join(log_dir, "midas.log"), maxBytes=rotate_bytes, backupCount=backup_count)
    fh.setFormatter(fmt)
    logger.addHandler(fh)
    return logger
