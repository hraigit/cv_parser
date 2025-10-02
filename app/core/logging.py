"""Async-safe singleton logger implementation."""
import asyncio
import logging
import sys
from pathlib import Path
from typing import Optional

from app.core.config import settings


class AsyncSafeLoggerSingleton:
    """Thread-safe and async-safe singleton logger."""
    
    _instance: Optional["AsyncSafeLoggerSingleton"] = None
    _lock = asyncio.Lock()
    _thread_lock = None  # Will be initialized in __init__
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize logger only once."""
        if hasattr(self, "_initialized"):
            return
            
        import threading
        self._thread_lock = threading.Lock()
        self._initialized = True
        self._logger = self._setup_logger()
    
    def _setup_logger(self) -> logging.Logger:
        """Setup and configure logger."""
        logger = logging.getLogger(settings.APP_NAME)
        logger.setLevel(getattr(logging, settings.LOG_LEVEL))
        logger.handlers.clear()
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, settings.LOG_LEVEL))
        
        # Format setup
        if settings.LOG_FORMAT == "json":
            formatter = logging.Formatter(
                "%(asctime)s %(name)s %(levelname)s %(message)s %(pathname)s %(lineno)d"
            )
        else:
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s - [%(pathname)s:%(lineno)d]"
            )
        
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # File handler (optional)
        if settings.LOG_FILE_PATH:
            log_path = Path(settings.LOG_FILE_PATH)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            file_handler = logging.FileHandler(log_path)
            file_handler.setLevel(getattr(logging, settings.LOG_LEVEL))
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        
        return logger
    
    @property
    def logger(self) -> logging.Logger:
        """Get logger instance."""
        return self._logger
    
    def debug(self, msg: str, *args, **kwargs):
        """Log debug message."""
        self._logger.debug(msg, *args, **kwargs)
    
    def info(self, msg: str, *args, **kwargs):
        """Log info message."""
        self._logger.info(msg, *args, **kwargs)
    
    def warning(self, msg: str, *args, **kwargs):
        """Log warning message."""
        self._logger.warning(msg, *args, **kwargs)
    
    def error(self, msg: str, *args, **kwargs):
        """Log error message."""
        self._logger.error(msg, *args, **kwargs)
    
    def critical(self, msg: str, *args, **kwargs):
        """Log critical message."""
        self._logger.critical(msg, *args, **kwargs)
    
    def exception(self, msg: str, *args, **kwargs):
        """Log exception with traceback."""
        self._logger.exception(msg, *args, **kwargs)


def get_logger() -> AsyncSafeLoggerSingleton:
    """Get singleton logger instance."""
    return AsyncSafeLoggerSingleton()


# Global logger instance
logger = get_logger()