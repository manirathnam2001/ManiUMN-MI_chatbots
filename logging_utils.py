"""
Centralized logging utility for MI chatbot applications.
Provides consistent logging across chat sessions, PDF generation, and error handling.
"""

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Any


class MIChatbotLogger:
    """Centralized logger for MI chatbot activities."""
    
    # Log directory configuration
    DEFAULT_LOG_DIR = os.path.join(os.path.dirname(__file__), 'logs')
    DEFAULT_LOG_FILE = 'mi_chatbot.log'
    
    def __init__(self, log_dir: Optional[str] = None, log_file: Optional[str] = None):
        """
        Initialize the MI chatbot logger.
        
        Args:
            log_dir: Directory for log files (defaults to ./logs)
            log_file: Name of the log file (defaults to mi_chatbot.log)
        """
        self.log_dir = log_dir or self.DEFAULT_LOG_DIR
        self.log_file = log_file or self.DEFAULT_LOG_FILE
        
        # Create log directory if it doesn't exist
        Path(self.log_dir).mkdir(parents=True, exist_ok=True)
        
        # Full path to log file
        self.log_path = os.path.join(self.log_dir, self.log_file)
        
        # Configure Python logging for console only (warnings and errors)
        self.logger = logging.getLogger('MIChatbot')
        self.logger.setLevel(logging.WARNING)
        
        # Remove existing handlers to avoid duplicates
        self.logger.handlers.clear()
        
        # Console handler only for warnings and errors
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.WARNING)
        
        # Add handler
        self.logger.addHandler(console_handler)
    
    def _create_log_entry(self, event_type: str, level: str, message: str, 
                         data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Create a standardized log entry."""
        entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': level,
            'event_type': event_type,
            'message': message
        }
        
        if data:
            entry['data'] = data
        
        return entry
    
    def _write_log(self, entry: Dict[str, Any]):
        """Write log entry to file in JSON format."""
        try:
            with open(self.log_path, 'a') as f:
                f.write(json.dumps(entry) + '\n')
        except Exception as e:
            # Fallback to Python logging if JSON write fails
            self.logger.error(f"Failed to write JSON log: {e}")
    
    def log_session_start(self, student_name: str, session_type: str, 
                         persona: Optional[str] = None):
        """Log the start of a chat session."""
        entry = self._create_log_entry(
            event_type='session_start',
            level='INFO',
            message=f'Chat session started for {student_name}',
            data={
                'student_name': student_name,
                'session_type': session_type,
                'persona': persona
            }
        )
        self._write_log(entry)
        self.logger.info(f"Session started: {student_name} - {session_type}")
    
    def log_session_end(self, student_name: str, session_type: str, 
                       message_count: int, end_reason: str = 'user_initiated'):
        """Log the end of a chat session."""
        entry = self._create_log_entry(
            event_type='session_end',
            level='INFO',
            message=f'Chat session ended for {student_name}',
            data={
                'student_name': student_name,
                'session_type': session_type,
                'message_count': message_count,
                'end_reason': end_reason
            }
        )
        self._write_log(entry)
        self.logger.info(f"Session ended: {student_name} - {message_count} messages")
    
    def log_feedback_generated(self, student_name: str, session_type: str,
                              total_score: float, percentage: float,
                              persona: Optional[str] = None):
        """Log successful feedback generation."""
        entry = self._create_log_entry(
            event_type='feedback_generated',
            level='INFO',
            message=f'Feedback generated for {student_name}',
            data={
                'student_name': student_name,
                'session_type': session_type,
                'persona': persona,
                'total_score': total_score,
                'percentage': percentage
            }
        )
        self._write_log(entry)
        self.logger.info(f"Feedback generated: {student_name} - Score: {total_score}/30 ({percentage}%)")
    
    def log_pdf_generation_attempt(self, student_name: str, session_type: str,
                                   persona: Optional[str] = None):
        """Log PDF generation attempt."""
        entry = self._create_log_entry(
            event_type='pdf_generation_attempt',
            level='INFO',
            message=f'PDF generation attempted for {student_name}',
            data={
                'student_name': student_name,
                'session_type': session_type,
                'persona': persona
            }
        )
        self._write_log(entry)
        self.logger.info(f"PDF generation attempt: {student_name}")
    
    def log_pdf_generation_success(self, student_name: str, session_type: str,
                                   filename: str, file_size: int,
                                   persona: Optional[str] = None):
        """Log successful PDF generation."""
        entry = self._create_log_entry(
            event_type='pdf_generation_success',
            level='INFO',
            message=f'PDF generated successfully for {student_name}',
            data={
                'student_name': student_name,
                'session_type': session_type,
                'persona': persona,
                'filename': filename,
                'file_size_bytes': file_size
            }
        )
        self._write_log(entry)
        self.logger.info(f"PDF generated: {filename} ({file_size} bytes)")
    
    def log_pdf_generation_error(self, student_name: str, session_type: str,
                                 error: str, error_type: str = 'unknown',
                                 persona: Optional[str] = None):
        """Log PDF generation error."""
        entry = self._create_log_entry(
            event_type='pdf_generation_error',
            level='ERROR',
            message=f'PDF generation failed for {student_name}: {error}',
            data={
                'student_name': student_name,
                'session_type': session_type,
                'persona': persona,
                'error': error,
                'error_type': error_type
            }
        )
        self._write_log(entry)
        self.logger.error(f"PDF generation failed: {student_name} - {error}")
    
    def log_validation_error(self, validation_type: str, error: str, 
                            data: Optional[Dict[str, Any]] = None):
        """Log data validation errors."""
        entry = self._create_log_entry(
            event_type='validation_error',
            level='WARNING',
            message=f'Validation error ({validation_type}): {error}',
            data={'validation_type': validation_type, 'error': error, **(data or {})}
        )
        self._write_log(entry)
        self.logger.warning(f"Validation error: {validation_type} - {error}")
    
    def log_end_phrase_detected(self, student_name: str, session_type: str,
                               phrase: str, message_count: int):
        """Log detection of end-of-conversation phrase."""
        entry = self._create_log_entry(
            event_type='end_phrase_detected',
            level='INFO',
            message=f'End phrase detected in conversation with {student_name}',
            data={
                'student_name': student_name,
                'session_type': session_type,
                'detected_phrase': phrase,
                'message_count': message_count
            }
        )
        self._write_log(entry)
        self.logger.info(f"End phrase detected: {phrase} at message {message_count}")
    
    def log_error(self, error_type: str, error: str, 
                 data: Optional[Dict[str, Any]] = None):
        """Log general errors."""
        entry = self._create_log_entry(
            event_type='error',
            level='ERROR',
            message=f'{error_type}: {error}',
            data={'error_type': error_type, 'error': error, **(data or {})}
        )
        self._write_log(entry)
        self.logger.error(f"{error_type}: {error}")


# Global logger instance
_global_logger = None


def get_logger(log_dir: Optional[str] = None, log_file: Optional[str] = None) -> MIChatbotLogger:
    """
    Get or create the global logger instance.
    
    Args:
        log_dir: Directory for log files (only used on first call)
        log_file: Name of the log file (only used on first call)
        
    Returns:
        MIChatbotLogger instance
    """
    global _global_logger
    if _global_logger is None:
        _global_logger = MIChatbotLogger(log_dir=log_dir, log_file=log_file)
    return _global_logger
