"""
Logging setup for AutoSorter.

Provides rotating file logger that writes to AppData\\Local\\AutoSorter\\logs\\.
Logs are rotated at 5MB with 5 backup files retained.
"""

import logging
import os
from logging.handlers import RotatingFileHandler

from src.config import LOG_DIR, load_config

_logger = None


def setup_logging():
    """Initialize the application-wide logger.
    
    Creates the log directory if needed and configures a rotating file handler
    with console output for development/debugging.
    
    Returns:
        logging.Logger: Configured logger instance.
    """
    global _logger
    if _logger is not None:
        return _logger

    os.makedirs(LOG_DIR, exist_ok=True)
    config = load_config()

    logger = logging.getLogger('AutoSorter')
    logger.setLevel(logging.DEBUG)

    # Rotating file handler
    log_file = os.path.join(LOG_DIR, 'autosorter.log')
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=config.get('log_max_bytes', 5242880),
        backupCount=config.get('log_backup_count', 5),
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)

    # Format
    formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    _logger = logger
    return logger


def get_logger():
    """Get the application logger, initializing if necessary.
    
    Returns:
        logging.Logger: The AutoSorter logger instance.
    """
    global _logger
    if _logger is None:
        return setup_logging()
    return _logger


def log_file_result(filename, file_type, prediction, score, action, processing_time, error=None):
    """Log a structured file processing result.
    
    Args:
        filename: Name of the processed file.
        file_type: Type category (PDF, DOCX, etc.).
        prediction: Predicted subject category.
        score: Confidence/similarity score.
        action: Action taken (MOVED or KEPT).
        processing_time: Time taken in seconds.
        error: Optional error message.
    """
    logger = get_logger()
    
    msg_lines = [
        f"File: {filename}",
        f"Type: {file_type}",
        f"Prediction: {prediction}",
        f"Score: {score:.4f}",
        f"Action: {action}",
        f"Time: {processing_time:.2f}s",
    ]
    if error:
        msg_lines.append(f"Error: {error}")

    logger.info(" | ".join(msg_lines))
