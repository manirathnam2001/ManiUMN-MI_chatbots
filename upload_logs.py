"""
Box Upload Logging System for MI Chatbots

This module provides comprehensive logging functionality for tracking Box upload
activities including email delivery, success/failure status, and error tracking.

Features:
- Separate logs for OHI and HPV bots
- UTC timestamps for all log entries
- JSON-formatted structured logging
- Automatic log rotation
- Error tracking and reporting
- Upload statistics and monitoring
"""

import json
import logging
import logging.handlers
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import traceback


class BoxUploadLogger:
    """
    Logger for tracking Box upload activities with structured JSON logging.
    
    Features:
    - Separate log files for each bot (OHI, HPV)
    - UTC timestamps
    - JSON structured format
    - Automatic rotation (10MB per file, keep 5 backups)
    - Error tracking and statistics
    """
    
    # Log levels
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL
    
    def __init__(self, bot_type: str, log_directory: str = "logs", 
                 max_bytes: int = 10 * 1024 * 1024, backup_count: int = 5):
        """
        Initialize the Box upload logger.
        
        Args:
            bot_type: Type of bot ('OHI' or 'HPV')
            log_directory: Directory to store log files
            max_bytes: Maximum size of each log file before rotation (default: 10MB)
            backup_count: Number of backup files to keep (default: 5)
        """
        self.bot_type = bot_type.upper()
        self.log_directory = log_directory
        self.max_bytes = max_bytes
        self.backup_count = backup_count
        
        # Create log directory if it doesn't exist
        Path(self.log_directory).mkdir(parents=True, exist_ok=True)
        
        # Setup logger
        self.logger = self._setup_logger()
        
    def _setup_logger(self) -> logging.Logger:
        """
        Setup the logger with rotating file handler.
        
        Returns:
            Configured logger instance
        """
        logger_name = f"box_upload_{self.bot_type.lower()}"
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.DEBUG)
        
        # Remove existing handlers to avoid duplicates
        logger.handlers = []
        
        # Create log file path
        log_file = os.path.join(self.log_directory, 
                                f"box_uploads_{self.bot_type.lower()}.log")
        
        # Create rotating file handler
        handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=self.max_bytes,
            backupCount=self.backup_count,
            encoding='utf-8'
        )
        
        # Set format to JSON
        formatter = logging.Formatter('%(message)s')
        handler.setFormatter(formatter)
        
        logger.addHandler(handler)
        
        return logger
    
    def _get_utc_timestamp(self) -> str:
        """
        Get current UTC timestamp in ISO format.
        
        Returns:
            UTC timestamp string in ISO 8601 format
        """
        from datetime import timezone
        return datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
    
    def _log_entry(self, level: int, event_type: str, message: str, 
                   metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Create a structured log entry.
        
        Args:
            level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            event_type: Type of event being logged
            message: Log message
            metadata: Additional metadata to include in log
        """
        log_data = {
            'timestamp': self._get_utc_timestamp(),
            'bot_type': self.bot_type,
            'level': logging.getLevelName(level),
            'event_type': event_type,
            'message': message
        }
        
        if metadata:
            log_data['metadata'] = metadata
            
        # Log as JSON
        self.logger.log(level, json.dumps(log_data))
    
    def log_upload_attempt(self, student_name: str, filename: str, 
                          box_email: str, file_size: Optional[int] = None) -> None:
        """
        Log an upload attempt to Box.
        
        Args:
            student_name: Name of the student
            filename: Name of the PDF file
            box_email: Box upload email address
            file_size: Size of the file in bytes (optional)
        """
        metadata = {
            'student_name': student_name,
            'filename': filename,
            'box_email': box_email
        }
        
        if file_size is not None:
            metadata['file_size_bytes'] = file_size
            
        self._log_entry(
            self.INFO,
            'upload_attempt',
            f'Attempting to upload {filename} for {student_name}',
            metadata
        )
    
    def log_upload_success(self, student_name: str, filename: str, 
                          box_email: str, delivery_time: Optional[float] = None) -> None:
        """
        Log a successful upload to Box.
        
        Args:
            student_name: Name of the student
            filename: Name of the PDF file
            box_email: Box upload email address
            delivery_time: Time taken for delivery in seconds (optional)
        """
        metadata = {
            'student_name': student_name,
            'filename': filename,
            'box_email': box_email,
            'status': 'success'
        }
        
        if delivery_time is not None:
            metadata['delivery_time_seconds'] = delivery_time
            
        self._log_entry(
            self.INFO,
            'upload_success',
            f'Successfully uploaded {filename} for {student_name}',
            metadata
        )
    
    def log_upload_failure(self, student_name: str, filename: str, 
                          box_email: str, error_message: str, 
                          error_type: Optional[str] = None) -> None:
        """
        Log a failed upload to Box.
        
        Args:
            student_name: Name of the student
            filename: Name of the PDF file
            box_email: Box upload email address
            error_message: Error message describing the failure
            error_type: Type of error (optional)
        """
        metadata = {
            'student_name': student_name,
            'filename': filename,
            'box_email': box_email,
            'status': 'failure',
            'error_message': error_message
        }
        
        if error_type:
            metadata['error_type'] = error_type
            
        self._log_entry(
            self.ERROR,
            'upload_failure',
            f'Failed to upload {filename} for {student_name}: {error_message}',
            metadata
        )
    
    def log_email_delivery_status(self, recipient: str, status: str, 
                                  message_id: Optional[str] = None) -> None:
        """
        Log email delivery status.
        
        Args:
            recipient: Email recipient address
            status: Delivery status (e.g., 'sent', 'failed', 'queued')
            message_id: Email message ID (optional)
        """
        metadata = {
            'recipient': recipient,
            'status': status
        }
        
        if message_id:
            metadata['message_id'] = message_id
            
        level = self.INFO if status == 'sent' else self.WARNING
        
        self._log_entry(
            level,
            'email_delivery',
            f'Email delivery status: {status} to {recipient}',
            metadata
        )
    
    def log_error(self, error_type: str, error_message: str, 
                 context: Optional[Dict[str, Any]] = None) -> None:
        """
        Log a general error.
        
        Args:
            error_type: Type of error
            error_message: Error message
            context: Additional context information
        """
        metadata = {
            'error_type': error_type,
            'error_message': error_message
        }
        
        if context:
            metadata['context'] = context
            
        self._log_entry(
            self.ERROR,
            'error',
            f'{error_type}: {error_message}',
            metadata
        )
    
    def log_warning(self, warning_type: str, warning_message: str, 
                   context: Optional[Dict[str, Any]] = None) -> None:
        """
        Log a warning.
        
        Args:
            warning_type: Type of warning
            warning_message: Warning message
            context: Additional context information
        """
        metadata = {
            'warning_type': warning_type,
            'warning_message': warning_message
        }
        
        if context:
            metadata['context'] = context
            
        self._log_entry(
            self.WARNING,
            'warning',
            f'{warning_type}: {warning_message}',
            metadata
        )
    
    def log_critical(self, error_type: str, error_message: str, 
                    context: Optional[Dict[str, Any]] = None) -> None:
        """
        Log a critical error that requires immediate attention.
        
        Args:
            error_type: Type of critical error
            error_message: Error message
            context: Additional context information
        """
        metadata = {
            'error_type': error_type,
            'error_message': error_message
        }
        
        if context:
            metadata['context'] = context
            
        self._log_entry(
            self.CRITICAL,
            'critical_error',
            f'CRITICAL - {error_type}: {error_message}',
            metadata
        )


class LogAnalyzer:
    """
    Utilities for analyzing and reporting on Box upload logs.
    """
    
    def __init__(self, log_directory: str = "logs"):
        """
        Initialize the log analyzer.
        
        Args:
            log_directory: Directory containing log files
        """
        self.log_directory = log_directory
    
    def _read_log_file(self, bot_type: str) -> List[Dict[str, Any]]:
        """
        Read and parse log file for a specific bot.
        
        Args:
            bot_type: Type of bot ('OHI' or 'HPV')
            
        Returns:
            List of parsed log entries
        """
        log_file = os.path.join(self.log_directory, 
                               f"box_uploads_{bot_type.lower()}.log")
        
        if not os.path.exists(log_file):
            return []
        
        entries = []
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            entries.append(json.loads(line))
                        except json.JSONDecodeError:
                            continue
        except Exception as e:
            print(f"Error reading log file: {e}")
            
        return entries
    
    def get_upload_statistics(self, bot_type: str, 
                             days: Optional[int] = None) -> Dict[str, Any]:
        """
        Get upload statistics for a specific bot.
        
        Args:
            bot_type: Type of bot ('OHI' or 'HPV')
            days: Number of days to analyze (None for all)
            
        Returns:
            Dictionary containing upload statistics
        """
        entries = self._read_log_file(bot_type)
        
        if days:
            from datetime import timezone
            cutoff_time = datetime.now(timezone.utc)
            cutoff_time = cutoff_time.replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            cutoff_time = cutoff_time.timestamp() - (days * 86400)
            
            # Filter entries by date
            entries = [
                e for e in entries 
                if datetime.strptime(e['timestamp'], '%Y-%m-%d %H:%M:%S').timestamp() >= cutoff_time
            ]
        
        total_attempts = sum(1 for e in entries if e.get('event_type') == 'upload_attempt')
        total_successes = sum(1 for e in entries if e.get('event_type') == 'upload_success')
        total_failures = sum(1 for e in entries if e.get('event_type') == 'upload_failure')
        total_errors = sum(1 for e in entries if e.get('level') == 'ERROR')
        total_warnings = sum(1 for e in entries if e.get('level') == 'WARNING')
        total_critical = sum(1 for e in entries if e.get('level') == 'CRITICAL')
        
        success_rate = (total_successes / total_attempts * 100) if total_attempts > 0 else 0
        
        return {
            'bot_type': bot_type.upper(),
            'period': f'Last {days} days' if days else 'All time',
            'total_attempts': total_attempts,
            'total_successes': total_successes,
            'total_failures': total_failures,
            'success_rate': round(success_rate, 2),
            'total_errors': total_errors,
            'total_warnings': total_warnings,
            'total_critical': total_critical
        }
    
    def get_error_summary(self, bot_type: str, 
                         limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get a summary of recent errors.
        
        Args:
            bot_type: Type of bot ('OHI' or 'HPV')
            limit: Maximum number of errors to return
            
        Returns:
            List of error entries
        """
        entries = self._read_log_file(bot_type)
        
        errors = [
            e for e in entries 
            if e.get('level') in ['ERROR', 'CRITICAL']
        ]
        
        # Sort by timestamp (most recent first)
        errors.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return errors[:limit]
    
    def get_recent_uploads(self, bot_type: str, 
                          limit: int = 20) -> List[Dict[str, Any]]:
        """
        Get recent upload activities.
        
        Args:
            bot_type: Type of bot ('OHI' or 'HPV')
            limit: Maximum number of uploads to return
            
        Returns:
            List of recent upload entries
        """
        entries = self._read_log_file(bot_type)
        
        uploads = [
            e for e in entries 
            if e.get('event_type') in ['upload_attempt', 'upload_success', 'upload_failure']
        ]
        
        # Sort by timestamp (most recent first)
        uploads.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return uploads[:limit]
    
    def cleanup_old_logs(self, days: int = 90) -> Dict[str, int]:
        """
        Clean up log entries older than specified days.
        
        This creates new log files without old entries for both OHI and HPV bots.
        
        Args:
            days: Number of days to keep (default: 90)
            
        Returns:
            Dictionary with cleanup statistics
        """
        from datetime import timezone
        cutoff_time = datetime.now(timezone.utc)
        cutoff_time = cutoff_time.replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        cutoff_time = cutoff_time.timestamp() - (days * 86400)
        
        results = {}
        
        for bot_type in ['OHI', 'HPV']:
            log_file = os.path.join(self.log_directory, 
                                   f"box_uploads_{bot_type.lower()}.log")
            
            if not os.path.exists(log_file):
                results[bot_type] = 0
                continue
            
            entries = self._read_log_file(bot_type)
            
            # Filter to keep only recent entries
            kept_entries = [
                e for e in entries 
                if datetime.strptime(e['timestamp'], '%Y-%m-%d %H:%M:%S').timestamp() >= cutoff_time
            ]
            
            removed_count = len(entries) - len(kept_entries)
            
            # Rewrite log file with kept entries
            try:
                with open(log_file, 'w', encoding='utf-8') as f:
                    for entry in kept_entries:
                        f.write(json.dumps(entry) + '\n')
                
                results[bot_type] = removed_count
            except Exception as e:
                print(f"Error cleaning up log file for {bot_type}: {e}")
                results[bot_type] = 0
        
        return results


class BoxUploadMonitor:
    """
    Real-time monitoring and alerting for Box upload activities.
    """
    
    def __init__(self, log_directory: str = "logs"):
        """
        Initialize the monitor.
        
        Args:
            log_directory: Directory containing log files
        """
        self.log_directory = log_directory
        self.analyzer = LogAnalyzer(log_directory)
    
    def check_health(self, bot_type: str, 
                    threshold: float = 80.0) -> Dict[str, Any]:
        """
        Check the health status of Box uploads.
        
        Args:
            bot_type: Type of bot ('OHI' or 'HPV')
            threshold: Minimum success rate percentage (default: 80%)
            
        Returns:
            Dictionary with health status
        """
        stats = self.analyzer.get_upload_statistics(bot_type, days=7)
        
        success_rate = stats['success_rate']
        is_healthy = success_rate >= threshold
        
        status = 'healthy' if is_healthy else 'unhealthy'
        
        return {
            'bot_type': bot_type.upper(),
            'status': status,
            'success_rate': success_rate,
            'threshold': threshold,
            'recent_errors': stats['total_errors'],
            'recent_critical': stats['total_critical'],
            'message': f'Success rate: {success_rate}% (threshold: {threshold}%)'
        }
    
    def generate_status_report(self, bot_type: str) -> str:
        """
        Generate a human-readable status report.
        
        Args:
            bot_type: Type of bot ('OHI' or 'HPV')
            
        Returns:
            Formatted status report string
        """
        stats_week = self.analyzer.get_upload_statistics(bot_type, days=7)
        stats_all = self.analyzer.get_upload_statistics(bot_type)
        recent_errors = self.analyzer.get_error_summary(bot_type, limit=5)
        
        report = f"""
Box Upload Status Report - {bot_type.upper()} Bot
{'=' * 60}

Last 7 Days:
  - Total Attempts: {stats_week['total_attempts']}
  - Successes: {stats_week['total_successes']}
  - Failures: {stats_week['total_failures']}
  - Success Rate: {stats_week['success_rate']}%
  - Errors: {stats_week['total_errors']}
  - Warnings: {stats_week['total_warnings']}
  - Critical: {stats_week['total_critical']}

All Time:
  - Total Attempts: {stats_all['total_attempts']}
  - Successes: {stats_all['total_successes']}
  - Failures: {stats_all['total_failures']}
  - Success Rate: {stats_all['success_rate']}%

Recent Errors (Last 5):
"""
        
        if recent_errors:
            for i, error in enumerate(recent_errors, 1):
                report += f"  {i}. [{error['timestamp']}] {error.get('message', 'N/A')}\n"
        else:
            report += "  No recent errors\n"
        
        report += "\n" + "=" * 60
        
        return report


# Example usage and testing
if __name__ == "__main__":
    # Example: Create logger and log some events
    print("Box Upload Logger - Test Mode\n")
    
    # Test OHI logger
    ohi_logger = BoxUploadLogger("OHI", log_directory="./logs")
    ohi_logger.log_upload_attempt("John Doe", "feedback_report.pdf", 
                                  "OHI_dir.zcdwwmukjr9ab546@u.box.com", 
                                  file_size=52000)
    ohi_logger.log_upload_success("John Doe", "feedback_report.pdf", 
                                  "OHI_dir.zcdwwmukjr9ab546@u.box.com", 
                                  delivery_time=1.5)
    
    # Test HPV logger
    hpv_logger = BoxUploadLogger("HPV", log_directory="./logs")
    hpv_logger.log_upload_attempt("Jane Smith", "assessment.pdf", 
                                  "HPV_Dir.yqz3brxlhcurhp2l@u.box.com")
    hpv_logger.log_upload_failure("Jane Smith", "assessment.pdf", 
                                  "HPV_Dir.yqz3brxlhcurhp2l@u.box.com",
                                  "Network timeout", "NETWORK_ERROR")
    
    # Test monitoring
    print("\nGenerating statistics...")
    analyzer = LogAnalyzer("./logs")
    ohi_stats = analyzer.get_upload_statistics("OHI")
    print(f"\nOHI Statistics: {json.dumps(ohi_stats, indent=2)}")
    
    hpv_stats = analyzer.get_upload_statistics("HPV")
    print(f"\nHPV Statistics: {json.dumps(hpv_stats, indent=2)}")
    
    # Test monitoring
    monitor = BoxUploadMonitor("./logs")
    print("\n" + monitor.generate_status_report("OHI"))
    print("\n" + monitor.generate_status_report("HPV"))
    
    print("\n✅ Test completed successfully!")
