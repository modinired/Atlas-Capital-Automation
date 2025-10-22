"""
Production-grade logging system with rotation, formatting, and multi-output support.
"""

import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from datetime import datetime
from typing import Optional
import threading


class ColoredFormatter(logging.Formatter):
    """Custom formatter with color support for terminal output."""
    
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
    }
    RESET = '\033[0m'
    
    def format(self, record):
        if hasattr(sys.stderr, 'isatty') and sys.stderr.isatty():
            levelname = record.levelname
            if levelname in self.COLORS:
                record.levelname = f"{self.COLORS[levelname]}{levelname}{self.RESET}"
        return super().format(record)


class ScriptLauncherLogger:
    """Singleton logger for the script launcher application."""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        self._initialized = True
        self.loggers = {}
        self.log_dir = Path.home() / 'script_launcher' / 'logs'
        self.log_dir.mkdir(parents=True, exist_ok=True)
    
    def get_logger(self, name: str, log_file: Optional[str] = None) -> logging.Logger:
        """
        Get or create a logger with the specified name.
        
        Args:
            name: Logger name (typically module name)
            log_file: Optional specific log file name
            
        Returns:
            Configured logger instance
        """
        if name in self.loggers:
            return self.loggers[name]
        
        logger = logging.getLogger(name)
        logger.setLevel(logging.DEBUG)
        logger.propagate = False
        
        # Console handler with colors
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_formatter = ColoredFormatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
        
        # File handler with rotation
        if log_file is None:
            log_file = f"{name}.log"
        
        file_path = self.log_dir / log_file
        file_handler = RotatingFileHandler(
            file_path,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
        
        self.loggers[name] = logger
        return logger
    
    def get_script_logger(self, script_name: str) -> logging.Logger:
        """
        Get a dedicated logger for a specific script execution.
        
        Args:
            script_name: Name of the script being executed
            
        Returns:
            Logger instance for the script
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_file = f"script_{script_name}_{timestamp}.log"
        return self.get_logger(f"script.{script_name}", log_file)
    
    def cleanup_old_logs(self, days: int = 30):
        """Remove log files older than specified days."""
        import time
        current_time = time.time()
        cutoff_time = current_time - (days * 86400)
        
        for log_file in self.log_dir.glob('*.log*'):
            if log_file.stat().st_mtime < cutoff_time:
                try:
                    log_file.unlink()
                except Exception as e:
                    print(f"Failed to delete old log {log_file}: {e}")


# Global logger instance
_logger_instance = ScriptLauncherLogger()


def get_logger(name: str) -> logging.Logger:
    """Convenience function to get a logger."""
    return _logger_instance.get_logger(name)


def get_script_logger(script_name: str) -> logging.Logger:
    """Convenience function to get a script-specific logger."""
    return _logger_instance.get_script_logger(script_name)

