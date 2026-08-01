import logging
import sys
from typing import Optional

class CustomFormatter(logging.Formatter):
    """Formatador personalizado para logs com cores."""
    
    FORMATS = {
        logging.INFO: "\033[0;32m{}\033[0m",      # Green
        logging.WARNING: "\033[0;33m{}\033[0m",   # Yellow
        logging.ERROR: "\033[0;31m{}\033[0m",     # Red
        logging.CRITICAL: "\033[0;41m{}\033[0m"   # Red background
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno, "\033[0m{}\033[0m")  # Default sem cor
        formatter = logging.Formatter(
            log_fmt.format("[%(asctime)s] %(message)s"),
            "%Y-%m-%d %H:%M:%S"
        )
        return formatter.format(record)

def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Retorna um logger configurado com o formatador personalizado.
    
    Args:
        name: Nome do logger. Se None, usa o nome do módulo chamador.
        
    Returns:
        logging.Logger: Logger configurado
    """
    logger = logging.getLogger(name or __name__)
    
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(CustomFormatter())
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    
    return logger 