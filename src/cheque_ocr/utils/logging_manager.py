git commit -m "Initial commit: Set up project structure and basic OCR functionality""""Logging configuration and management for cheque OCR system."""

import logging
import logging.config
import os
from pathlib import Path
from typing import Optional, Dict, Any


class LoggingManager:
    """Manages logging configuration for the cheque OCR system."""
    
    def __init__(self):
        self._configured = False
    
    def setup_logging(
        self, 
        log_level: str = "INFO",
        log_file: Optional[Path] = None,
        console_output: bool = True
    ) -> None:
        """
        Configure logging for the application.
        
        Args:
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_file: Optional path to log file
            console_output: Whether to output logs to console
        """
        if self._configured:
            return
            
        config = self._create_logging_config(log_level, log_file, console_output)
        logging.config.dictConfig(config)
        self._configured = True
        
        logger = logging.getLogger(__name__)
        logger.info("Logging system initialized")
    
    def _create_logging_config(
        self, 
        log_level: str, 
        log_file: Optional[Path], 
        console_output: bool
    ) -> Dict[str, Any]:
        """Create logging configuration dictionary."""
        
        formatters = {
            "detailed": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S"
            },
            "simple": {
                "format": "%(levelname)s - %(message)s"
            }
        }
        
        handlers = {}
        
        if console_output:
            handlers["console"] = {
                "class": "logging.StreamHandler",
                "level": log_level,
                "formatter": "simple",
                "stream": "ext://sys.stdout"
            }
        
        if log_file:
            # Ensure log directory exists
            log_file.parent.mkdir(parents=True, exist_ok=True)
            
            handlers["file"] = {
                "class": "logging.FileHandler",
                "level": log_level,
                "formatter": "detailed",
                "filename": str(log_file),
                "mode": "a",
                "encoding": "utf-8"
            }
        
        return {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": formatters,
            "handlers": handlers,
            "loggers": {
                "cheque_ocr": {
                    "level": log_level,
                    "handlers": list(handlers.keys()),
                    "propagate": False
                }
            },
            "root": {
                "level": log_level,
                "handlers": list(handlers.keys())
            }
        }
    
    @staticmethod
    def get_logger(name: str) -> logging.Logger:
        """Get a logger instance for the given name."""
        return logging.getLogger(f"cheque_ocr.{name}")


# Global logging manager instance
logging_manager = LoggingManager()
