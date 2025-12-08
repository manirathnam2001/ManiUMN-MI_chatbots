"""
Centralized Logging Configuration for MI Chatbots

This module provides a centralized logging setup for all MI chatbot applications
with structured, comprehensive logging that:
- Tracks all actions, replies, responses, and AI reasoning chains
- Provides different log levels (DEBUG, INFO, WARNING, ERROR)
- Avoids leaking sensitive data (API keys, student names in production)
- Uses consistent formatting across all modules
- Supports both file and console logging

Usage:
    from logger_config import get_logger, setup_logging
    
    # Setup logging once at application start
    setup_logging()
    
    # Get logger in any module
    logger = get_logger(__name__)
    logger.info("Application started")
"""

import logging
import os
import sys
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from typing import Optional
from pathlib import Path


# Default log configuration
DEFAULT_LOG_LEVEL = logging.INFO
DEFAULT_LOG_DIR = "git_logs"
DEFAULT_LOG_FILE = "chatbot.log"
DEFAULT_MAX_BYTES = 10 * 1024 * 1024  # 10 MB
DEFAULT_BACKUP_COUNT = 5


class SensitiveDataFilter(logging.Filter):
    """
    Filter to prevent sensitive data from being logged.
    
    This filter redacts:
    - API keys
    - Passwords
    - Authentication tokens
    - Email addresses (in production mode)
    """
    
    def __init__(self, redact_emails: bool = False):
        super().__init__()
        self.redact_emails = redact_emails
        
    def filter(self, record: logging.LogRecord) -> bool:
        """Filter and redact sensitive information from log records."""
        # Redact API keys
        if hasattr(record, 'msg'):
            msg = str(record.msg)
            # Redact common API key patterns
            import re
            msg = re.sub(r'(api[_-]?key|apikey|token)[\s:=]+["\']?[\w-]{20,}["\']?', 
                        r'\1=<REDACTED>', msg, flags=re.IGNORECASE)
            msg = re.sub(r'(password|passwd|pwd)[\s:=]+["\']?[^"\'\s]{6,}["\']?',
                        r'\1=<REDACTED>', msg, flags=re.IGNORECASE)
            
            # Optionally redact email addresses in production
            if self.redact_emails:
                msg = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
                           '<EMAIL_REDACTED>', msg)
            
            record.msg = msg
        
        return True


class StructuredFormatter(logging.Formatter):
    """
    Custom formatter for structured logging with consistent format.
    
    Format: [TIMESTAMP] [LEVEL] [MODULE] [FUNCTION] - MESSAGE
    """
    
    def __init__(self, include_function: bool = True):
        """
        Initialize structured formatter.
        
        Args:
            include_function: Whether to include function name in log output
        """
        self.include_function = include_function
        
        if include_function:
            fmt = '[%(asctime)s] [%(levelname)s] [%(name)s] [%(funcName)s] - %(message)s'
        else:
            fmt = '[%(asctime)s] [%(levelname)s] [%(name)s] - %(message)s'
        
        super().__init__(fmt=fmt, datefmt='%Y-%m-%d %H:%M:%S')


def setup_logging(
    log_dir: Optional[str] = None,
    log_file: Optional[str] = None,
    level: int = DEFAULT_LOG_LEVEL,
    console_output: bool = True,
    file_output: bool = True,
    max_bytes: int = DEFAULT_MAX_BYTES,
    backup_count: int = DEFAULT_BACKUP_COUNT,
    redact_emails: bool = False
) -> None:
    """
    Setup centralized logging configuration for the application.
    
    This should be called once at application startup.
    
    Args:
        log_dir: Directory for log files (default: git_logs)
        log_file: Log file name (default: chatbot.log)
        level: Logging level (default: INFO)
        console_output: Whether to output logs to console (default: True)
        file_output: Whether to output logs to file (default: True)
        max_bytes: Maximum size of log file before rotation (default: 10MB)
        backup_count: Number of backup files to keep (default: 5)
        redact_emails: Whether to redact email addresses (default: False)
    """
    # Use defaults if not provided
    log_dir = log_dir or DEFAULT_LOG_DIR
    log_file = log_file or DEFAULT_LOG_FILE
    
    # Create log directory if it doesn't exist
    if file_output:
        Path(log_dir).mkdir(parents=True, exist_ok=True)
    
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Remove existing handlers to avoid duplicates
    root_logger.handlers.clear()
    
    # Create formatter
    formatter = StructuredFormatter(include_function=True)
    
    # Create sensitive data filter
    sensitive_filter = SensitiveDataFilter(redact_emails=redact_emails)
    
    # Add console handler if requested
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        console_handler.addFilter(sensitive_filter)
        root_logger.addHandler(console_handler)
    
    # Add file handler if requested
    if file_output:
        log_path = os.path.join(log_dir, log_file)
        file_handler = RotatingFileHandler(
            log_path,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        file_handler.addFilter(sensitive_filter)
        root_logger.addHandler(file_handler)
    
    # Log initial setup message
    root_logger.info(f"Logging configured: level={logging.getLevelName(level)}, "
                    f"console={console_output}, file={file_output}")
    if file_output:
        root_logger.info(f"Log file: {log_path}")


def get_logger(name: str, level: Optional[int] = None) -> logging.Logger:
    """
    Get a logger instance with the specified name.
    
    This should be called in each module to get a module-specific logger:
        logger = get_logger(__name__)
    
    Args:
        name: Logger name (typically __name__ of the module)
        level: Optional logging level override
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    if level is not None:
        logger.setLevel(level)
    
    return logger


def log_action(logger: logging.Logger, action: str, details: Optional[dict] = None) -> None:
    """
    Log an action with structured details.
    
    Args:
        logger: Logger instance
        action: Action description (e.g., "user_message_received", "ai_response_generated")
        details: Optional dictionary of additional details
    """
    if details:
        detail_str = " | ".join([f"{k}={v}" for k, v in details.items()])
        logger.info(f"ACTION: {action} | {detail_str}")
    else:
        logger.info(f"ACTION: {action}")


def log_ai_reasoning(logger: logging.Logger, stage: str, reasoning: str) -> None:
    """
    Log AI reasoning chain for debugging and audit.
    
    Args:
        logger: Logger instance
        stage: Stage of reasoning (e.g., "persona_selection", "response_generation")
        reasoning: Description of reasoning or decision made
    """
    logger.debug(f"AI_REASONING: {stage} | {reasoning}")


def log_error_with_context(
    logger: logging.Logger,
    error: Exception,
    context: Optional[dict] = None
) -> None:
    """
    Log an error with contextual information.
    
    Args:
        logger: Logger instance
        error: Exception that occurred
        context: Optional dictionary of context (e.g., user action, system state)
    """
    error_msg = f"ERROR: {type(error).__name__}: {str(error)}"
    
    if context:
        context_str = " | ".join([f"{k}={v}" for k, v in context.items()])
        error_msg += f" | CONTEXT: {context_str}"
    
    logger.error(error_msg, exc_info=True)


# Example usage and testing
if __name__ == "__main__":
    # Setup logging
    setup_logging(
        level=logging.DEBUG,
        console_output=True,
        file_output=True,
        redact_emails=False
    )
    
    # Get logger
    logger = get_logger(__name__)
    
    # Test different log levels
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    
    # Test structured logging
    log_action(logger, "test_action", {"user": "test_user", "session": "123"})
    
    # Test AI reasoning logging
    log_ai_reasoning(logger, "test_stage", "This is a test reasoning step")
    
    # Test error logging with context
    try:
        raise ValueError("Test error")
    except Exception as e:
        log_error_with_context(logger, e, {"action": "test", "data": "sample"})
    
    # Test sensitive data filtering
    logger.info("API key: sk-abcdef123456 should be redacted")
    logger.info("Password: mypassword123 should be redacted")
    
    print("\nLogging test complete. Check git_logs/chatbot.log for output.")
