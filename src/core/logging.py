import logging
import sys
from logging.handlers import RotatingFileHandler
from src.core.config import settings

def setup_logging():
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(logging.Formatter(log_format))
    
    # File handler (rotates at 10MB, keeps 5 files)
    file_handler = RotatingFileHandler("tokflare.log", maxBytes=10*1024*1024, backupCount=5)
    file_handler.setFormatter(logging.Formatter(log_format))
    
    logging.basicConfig(
        level=logging.INFO,
        handlers=[console_handler, file_handler]
    )
    
    # Set levels for noisy libraries
    logging.getLogger("aiogram").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
