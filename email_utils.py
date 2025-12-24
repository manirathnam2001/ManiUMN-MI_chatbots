"""
Email Utilities Module for Secure SMTP Operations

This module provides secure email sending functionality with:
- Environment variable support for credentials
- SSL/TLS connection handling
- Comprehensive error handling and logging
- Support for PDF attachments
- Daily rotating logs with retry tracking
- Robust email delivery with queue persistence
"""

import smtplib
import ssl
import os
import logging
from logging.handlers import TimedRotatingFileHandler
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from typing import Optional, Dict, Any, Union
from pathlib import Path
import io
import time
from datetime import datetime


class EmailConfigError(Exception):
    """Exception raised for email configuration errors."""
    pass


class EmailSendError(Exception):
    """Exception raised when email sending fails."""
    pass


class SecureEmailSender:
    """
    Secure email sender with SSL/TLS support and environment variable handling.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None, 
                 logger: Optional[logging.Logger] = None):
        """
        Initialize secure email sender.
        
        Args:
            config: Email configuration dictionary (optional)
            logger: Logger instance for logging operations (optional)
        """
        self.config = config or {}
        self.logger = logger or self._setup_default_logger()
        
    def _setup_default_logger(self) -> logging.Logger:
        """Set up a default logger if none provided."""
        logger = logging.getLogger('email_utils')
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger
    
    def setup_smtp_logger(self, log_directory: str = "SMTP logs", 
                          log_filename: str = "email_backup.log") -> logging.Logger:
        """
        Set up a rotating file logger for SMTP operations.
        
        Args:
            log_directory: Directory to store log files
            log_filename: Name of the log file
            
        Returns:
            Configured logger instance
        """
        # Create log directory if it doesn't exist
        os.makedirs(log_directory, exist_ok=True)
        
        # Create logger
        smtp_logger = logging.getLogger('smtp_backup')
        smtp_logger.setLevel(logging.INFO)
        
        # Remove existing handlers to avoid duplicates
        smtp_logger.handlers = []
        
        # Create rotating file handler (rotates daily)
        log_path = os.path.join(log_directory, log_filename)
        file_handler = TimedRotatingFileHandler(
            log_path,
            when='midnight',
            interval=1,
            backupCount=30,  # Keep 30 days of logs
            encoding='utf-8'
        )
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        
        # Add handler to logger
        smtp_logger.addHandler(file_handler)
        
        # Also add console handler for immediate feedback
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        smtp_logger.addHandler(console_handler)
        
        return smtp_logger
    
    def get_smtp_credentials(self) -> Dict[str, str]:
        """
        Get SMTP credentials from environment variables or config.
        
        Priority:
        1. Environment variables (SMTP_USERNAME, SMTP_APP_PASSWORD)
        2. Config dictionary (smtp_username, smtp_app_password)
        3. Legacy config (sender_email, sender_password)
        
        Returns:
            Dictionary with 'username' and 'password'
            
        Raises:
            EmailConfigError: If credentials cannot be determined
        """
        # Try environment variables first (most secure)
        username = os.environ.get('SMTP_USERNAME')
        password = os.environ.get('SMTP_APP_PASSWORD')
        
        if username and password:
            self.logger.debug("Using SMTP credentials from environment variables")
            return {'username': username, 'password': password}
        
        # Try email_config section
        if 'email_config' in self.config:
            email_config = self.config['email_config']
            username = email_config.get('smtp_username')
            password = email_config.get('smtp_app_password')
            
            if username and password:
                self.logger.debug("Using SMTP credentials from email_config")
                return {'username': username, 'password': password}
        
        # Try legacy email section
        if 'email' in self.config:
            email_config = self.config['email']
            username = email_config.get('sender_email')
            password = email_config.get('sender_password')
            
            if username and password:
                self.logger.debug("Using SMTP credentials from legacy email config")
                return {'username': username, 'password': password}
        
        # No credentials found
        raise EmailConfigError(
            "SMTP credentials not found. Set SMTP_USERNAME and SMTP_APP_PASSWORD "
            "environment variables or configure in config file."
        )
    
    def get_smtp_settings(self) -> Dict[str, Any]:
        """
        Get SMTP server settings from config or environment variables.
        
        Returns:
            Dictionary with smtp_server, smtp_port, use_ssl, connection_timeout, 
            retry_attempts, and retry_delay settings
            
        Raises:
            EmailConfigError: If settings cannot be determined
        """
        # Default settings
        settings = {
            'smtp_server': 'smtp.gmail.com',
            'smtp_port': 587,
            'use_ssl': True,
            'connection_timeout': 30,
            'retry_attempts': 3,
            'retry_delay': 5
        }
        
        # Check environment variables
        if os.environ.get('SMTP_SERVER'):
            settings['smtp_server'] = os.environ.get('SMTP_SERVER')
        if os.environ.get('SMTP_PORT'):
            settings['smtp_port'] = int(os.environ.get('SMTP_PORT'))
        if os.environ.get('SMTP_USE_SSL'):
            settings['use_ssl'] = os.environ.get('SMTP_USE_SSL').lower() == 'true'
        if os.environ.get('CONNECTION_TIMEOUT'):
            settings['connection_timeout'] = int(os.environ.get('CONNECTION_TIMEOUT'))
        if os.environ.get('RETRY_ATTEMPTS'):
            settings['retry_attempts'] = int(os.environ.get('RETRY_ATTEMPTS'))
        if os.environ.get('RETRY_DELAY'):
            settings['retry_delay'] = int(os.environ.get('RETRY_DELAY'))
        
        # Override with config if present
        if 'email_config' in self.config:
            email_config = self.config['email_config']
            settings['smtp_server'] = email_config.get('smtp_server', settings['smtp_server'])
            settings['smtp_port'] = email_config.get('smtp_port', settings['smtp_port'])
            settings['use_ssl'] = email_config.get('smtp_use_ssl', settings['use_ssl'])
            settings['connection_timeout'] = email_config.get('connection_timeout', settings['connection_timeout'])
            settings['retry_attempts'] = email_config.get('retry_attempts', settings['retry_attempts'])
            settings['retry_delay'] = email_config.get('retry_delay', settings['retry_delay'])
        elif 'email' in self.config:
            email_config = self.config['email']
            settings['smtp_server'] = email_config.get('smtp_server', settings['smtp_server'])
            settings['smtp_port'] = email_config.get('smtp_port', settings['smtp_port'])
            # use_tls in legacy config
            if 'use_tls' in email_config:
                settings['use_ssl'] = email_config.get('use_tls', settings['use_ssl'])
        
        if not settings['smtp_server']:
            raise EmailConfigError("SMTP server not configured")
        
        return settings
    
    def send_email_with_attachment(self, 
                                   recipient: str,
                                   subject: str,
                                   body: str,
                                   attachment_buffer: io.BytesIO,
                                   attachment_filename: str,
                                   attachment_type: str = 'application/pdf',
                                   sender_email: Optional[str] = None,
                                   timeout: int = 30) -> bool:
        """
        Send an email with an attachment using secure SMTP.
        
        Args:
            recipient: Email recipient address
            subject: Email subject
            body: Email body text
            attachment_buffer: BytesIO buffer containing attachment data
            attachment_filename: Filename for the attachment
            attachment_type: MIME type of attachment (default: application/pdf)
            sender_email: Sender email (optional, uses credentials if not provided)
            timeout: SMTP connection timeout in seconds (default: 30)
            
        Returns:
            True if email sent successfully, False otherwise
            
        Raises:
            EmailSendError: If email sending fails after validation
        """
        try:
            # Get credentials and settings
            credentials = self.get_smtp_credentials()
            settings = self.get_smtp_settings()
            
            # Use provided sender or credentials username
            from_email = sender_email or credentials['username']
            
            self.logger.info(f"Preparing to send email to {recipient}")
            
            # Create message
            msg = MIMEMultipart()
            msg['From'] = from_email
            msg['To'] = recipient
            msg['Subject'] = subject
            
            # Add body
            msg.attach(MIMEText(body, 'plain'))
            
            # Attach file
            attachment_buffer.seek(0)
            attachment = MIMEBase(*attachment_type.split('/'))
            attachment.set_payload(attachment_buffer.read())
            encoders.encode_base64(attachment)
            attachment.add_header('Content-Disposition', 
                                f'attachment; filename={attachment_filename}')
            msg.attach(attachment)
            
            # Send email with SSL/TLS
            self.logger.debug(f"Connecting to SMTP server: {settings['smtp_server']}:{settings['smtp_port']}")
            
            with smtplib.SMTP(settings['smtp_server'], 
                            settings['smtp_port'], 
                            timeout=timeout) as server:
                
                # Enable debug output if logger is in DEBUG mode
                if self.logger.level == logging.DEBUG:
                    server.set_debuglevel(1)
                
                # Start TLS for secure connection
                if settings['use_ssl']:
                    context = ssl.create_default_context()
                    server.starttls(context=context)
                    self.logger.debug("TLS connection established")
                
                # Login with credentials
                server.login(credentials['username'], credentials['password'])
                self.logger.debug("SMTP authentication successful")
                
                # Send email
                server.send_message(msg)
                self.logger.info(f"Email sent successfully to {recipient}")
                
            return True
            
        except EmailConfigError as e:
            self.logger.error(f"Configuration error: {e}")
            raise EmailSendError(f"Email configuration error: {e}")
            
        except smtplib.SMTPAuthenticationError as e:
            self.logger.error(f"SMTP authentication failed: {e}")
            raise EmailSendError(f"SMTP authentication failed. Check credentials: {e}")
            
        except smtplib.SMTPException as e:
            self.logger.error(f"SMTP error occurred: {e}")
            raise EmailSendError(f"SMTP error: {e}")
            
        except Exception as e:
            self.logger.error(f"Unexpected error sending email: {e}")
            raise EmailSendError(f"Unexpected error: {e}")
    
    def send_email_with_retry(self,
                             recipient: str,
                             subject: str,
                             body: str,
                             attachment_buffer: io.BytesIO,
                             attachment_filename: str,
                             student_name: str = "Unknown",
                             session_type: str = "Unknown",
                             smtp_logger: Optional[logging.Logger] = None,
                             max_retries: int = 3,
                             retry_delay: int = 5) -> Dict[str, Any]:
        """
        Send email with retry mechanism and detailed logging.
        
        Args:
            recipient: Email recipient address
            subject: Email subject
            body: Email body text
            attachment_buffer: BytesIO buffer containing attachment data
            attachment_filename: Filename for the attachment
            student_name: Name of the student (for logging)
            session_type: Type of session (for logging)
            smtp_logger: Logger for SMTP operations (uses default if not provided)
            max_retries: Maximum number of retry attempts (default: 3)
            retry_delay: Delay between retries in seconds (default: 5)
            
        Returns:
            Dictionary with results including success status, attempt count, and error details
        """
        # Use provided logger or default
        logger = smtp_logger or self.logger
        
        result = {
            'success': False,
            'attempts': 0,
            'error': None,
            'timestamp': datetime.now().isoformat()
        }
        
        for attempt in range(1, max_retries + 1):
            result['attempts'] = attempt
            
            try:
                logger.info(f"Student: {student_name} | Session: {session_type} | "
                           f"Operation: Email Backup Attempt {attempt}/{max_retries} | "
                           f"Recipient: {recipient} | File: {attachment_filename}")
                
                # Reset buffer position before each attempt
                attachment_buffer.seek(0)
                
                # Attempt to send email
                success = self.send_email_with_attachment(
                    recipient=recipient,
                    subject=subject,
                    body=body,
                    attachment_buffer=attachment_buffer,
                    attachment_filename=attachment_filename
                )
                
                if success:
                    result['success'] = True
                    logger.info(f"Student: {student_name} | Session: {session_type} | "
                               f"Operation: SUCCESS | Details: Email backup completed successfully "
                               f"on attempt {attempt}")
                    return result
                    
            except EmailSendError as e:
                result['error'] = str(e)
                logger.warning(f"Student: {student_name} | Session: {session_type} | "
                              f"Operation: WARNING | Details: Email send failed on attempt {attempt}/{max_retries} - {e}")
                
                # If not the last attempt, wait before retrying
                if attempt < max_retries:
                    logger.info(f"Student: {student_name} | Session: {session_type} | "
                               f"Operation: RETRY | Details: Waiting {retry_delay} seconds before retry {attempt + 1}")
                    time.sleep(retry_delay)
                    
            except Exception as e:
                result['error'] = str(e)
                logger.error(f"Student: {student_name} | Session: {session_type} | "
                            f"Operation: ERROR | Details: Unexpected error on attempt {attempt}/{max_retries} - {e}")
                
                if attempt < max_retries:
                    time.sleep(retry_delay)
        
        # All retries failed
        logger.error(f"Student: {student_name} | Session: {session_type} | "
                    f"Operation: FAILURE | Details: Email backup failed after {max_retries} attempts - {result['error']}")
        
        return result
    
    def test_connection(self) -> Dict[str, Any]:
        """
        Test the SMTP connection without sending an email.
        
        Returns:
            Dictionary with test results including status and message
        """
        result = {
            'status': 'unknown',
            'message': '',
            'smtp_server': None,
            'smtp_port': None,
            'authentication': False
        }
        
        try:
            # Get credentials and settings
            credentials = self.get_smtp_credentials()
            settings = self.get_smtp_settings()
            
            result['smtp_server'] = settings['smtp_server']
            result['smtp_port'] = settings['smtp_port']
            
            self.logger.info(f"Testing connection to {settings['smtp_server']}:{settings['smtp_port']}")
            
            # Try to connect and authenticate
            with smtplib.SMTP(settings['smtp_server'], 
                            settings['smtp_port'], 
                            timeout=10) as server:
                
                if settings['use_ssl']:
                    context = ssl.create_default_context()
                    server.starttls(context=context)
                
                server.login(credentials['username'], credentials['password'])
                result['authentication'] = True
                result['status'] = 'success'
                result['message'] = 'Connection and authentication successful'
                
                self.logger.info("SMTP connection test successful")
                
        except EmailConfigError as e:
            result['status'] = 'config_error'
            result['message'] = str(e)
            self.logger.error(f"Configuration error: {e}")
            
        except smtplib.SMTPAuthenticationError as e:
            result['status'] = 'auth_failed'
            result['message'] = f"Authentication failed: {e}"
            self.logger.error(f"Authentication failed: {e}")
            
        except smtplib.SMTPException as e:
            result['status'] = 'smtp_error'
            result['message'] = f"SMTP error: {e}"
            self.logger.error(f"SMTP error: {e}")
            
        except Exception as e:
            result['status'] = 'error'
            result['message'] = f"Unexpected error: {e}"
            self.logger.error(f"Unexpected error: {e}")
        
        return result


class RobustEmailSender(SecureEmailSender):
    """
    Enhanced email sender with guaranteed delivery mechanisms.
    
    Extends SecureEmailSender with:
    - Multiple retry attempts with exponential backoff
    - Persistent queue for failed emails
    - Guaranteed delivery or queueing
    """
    
    MAX_RETRIES = 5
    RETRY_DELAYS = [5, 10, 30, 60, 120]  # Exponential backoff in seconds
    
    def __init__(self, config: Optional[Dict[str, Any]] = None, 
                 logger: Optional[logging.Logger] = None):
        """
        Initialize robust email sender.
        
        Args:
            config: Email configuration dictionary (optional)
            logger: Logger instance for logging operations (optional)
        """
        super().__init__(config, logger)
        
        # Load retry configuration from config
        if config and 'email_config' in config:
            email_config = config['email_config']
            self.MAX_RETRIES = email_config.get('max_retries', self.MAX_RETRIES)
            custom_delays = email_config.get('retry_delays')
            if custom_delays:
                self.RETRY_DELAYS = custom_delays
        
        # Initialize email queue
        from email_queue import EmailQueue
        log_dir = config.get('logging', {}).get('smtp_log_directory', 'SMTP logs') if config else 'SMTP logs'
        self.email_queue = EmailQueue(queue_dir=log_dir)
    
    def send_with_guaranteed_delivery(self, 
                                       pdf_buffer: io.BytesIO, 
                                       filename: str, 
                                       recipient: str,
                                       student_name: str, 
                                       session_type: str,
                                       progress_callback: Optional[callable] = None) -> Dict:
        """
        Send email with multiple retry attempts and queue for later if fails.
        
        This method ensures guaranteed delivery by:
        1. Attempting to send with exponential backoff retries
        2. Queuing the email persistently if all retries fail
        3. Returning detailed status information
        4. Calling progress callback for UI updates
        
        Args:
            pdf_buffer: BytesIO buffer containing PDF data
            filename: Name of the PDF file
            recipient: Email recipient address (Box email)
            student_name: Name of the student
            session_type: Type of MI session
            progress_callback: Optional callback(attempt, max_attempts, status)
            
        Returns:
            Dictionary with:
                - success: Boolean indicating if email was sent
                - attempts: Number of attempts made
                - queued: Boolean indicating if email was queued
                - error: Error message if failed (None if successful)
        """
        from time_utils import get_cst_timestamp
        
        self.logger.info(f"Starting guaranteed delivery for {filename} to {recipient}")
        
        # Prepare email content
        subject = f"{session_type} MI Practice Report - {student_name}"
        body = f"""MI Practice Report Backup

Student: {student_name}
Session Type: {session_type}
Report File: {filename}
Timestamp: {get_cst_timestamp()}

This is an automated backup of the MI practice feedback report.
"""
        
        last_error = None
        
        # Attempt sending with retries
        for attempt in range(self.MAX_RETRIES):
            if progress_callback:
                progress_callback(attempt + 1, self.MAX_RETRIES, 'trying')
            
            try:
                self.logger.info(f"Attempt {attempt + 1}/{self.MAX_RETRIES} to send email")
                
                # Create a fresh buffer copy for each attempt
                email_buffer = io.BytesIO(pdf_buffer.getvalue())
                
                # Try to send email
                success = self.send_email_with_attachment(
                    recipient=recipient,
                    subject=subject,
                    body=body,
                    attachment_buffer=email_buffer,
                    attachment_filename=filename,
                    attachment_type='application/pdf'
                )
                
                if success:
                    self.logger.info(f"Email sent successfully on attempt {attempt + 1}")
                    if progress_callback:
                        progress_callback(attempt + 1, self.MAX_RETRIES, 'success')
                    return {
                        'success': True,
                        'attempts': attempt + 1,
                        'queued': False,
                        'error': None
                    }
                else:
                    last_error = "Email sending returned False"
                    
            except Exception as e:
                last_error = str(e)
                self.logger.warning(f"Attempt {attempt + 1} failed: {e}")
                
                # If not the last attempt, wait before retrying
                if attempt < self.MAX_RETRIES - 1:
                    delay = self.RETRY_DELAYS[min(attempt, len(self.RETRY_DELAYS) - 1)]
                    self.logger.info(f"Waiting {delay} seconds before retry...")
                    if progress_callback:
                        progress_callback(attempt + 1, self.MAX_RETRIES, f'waiting {delay}s')
                    time.sleep(delay)
        
        # All retries failed - queue for later
        self.logger.error(f"All {self.MAX_RETRIES} attempts failed. Queueing email for later.")
        
        if progress_callback:
            progress_callback(self.MAX_RETRIES, self.MAX_RETRIES, 'queuing')
        
        try:
            # Get PDF data
            pdf_data = pdf_buffer.getvalue()
            
            # Add to persistent queue
            entry_id = self.email_queue.add(
                pdf_data=pdf_data,
                filename=filename,
                recipient=recipient,
                student_name=student_name,
                session_type=session_type
            )
            
            self.logger.info(f"Email queued with ID: {entry_id}")
            
            return {
                'success': False,
                'attempts': self.MAX_RETRIES,
                'queued': True,
                'queue_id': entry_id,
                'error': last_error or f'All {self.MAX_RETRIES} retry attempts failed. Email queued for later delivery.'
            }
            
        except Exception as queue_error:
            self.logger.error(f"Failed to queue email: {queue_error}")
            return {
                'success': False,
                'attempts': self.MAX_RETRIES,
                'queued': False,
                'error': f'All retries failed and queueing failed: {queue_error}'
            }
    
    def process_failed_queue(self) -> Dict[str, Any]:
        """
        Process all failed emails in the queue.
        
        This should be called on application startup to retry previously failed emails.
        
        Returns:
            Dictionary with:
                - total_pending: Number of emails in queue
                - processed: Number of emails attempted
                - succeeded: Number successfully sent
                - still_failed: Number still in queue
                - results: List of individual results
        """
        self.logger.info("Processing failed email queue...")
        
        pending_emails = self.email_queue.get_pending()
        results = {
            'total_pending': len(pending_emails),
            'processed': 0,
            'succeeded': 0,
            'still_failed': 0,
            'results': []
        }
        
        for entry in pending_emails:
            results['processed'] += 1
            entry_id = entry['id']
            
            try:
                # Load PDF data
                pdf_path = Path(entry['pdf_path'])
                if not pdf_path.exists():
                    self.logger.error(f"PDF file not found for queue entry {entry_id}: {pdf_path}")
                    results['still_failed'] += 1
                    continue
                
                with open(pdf_path, 'rb') as f:
                    pdf_data = f.read()
                
                # Create buffer
                pdf_buffer = io.BytesIO(pdf_data)
                
                # Attempt to send (with reduced retries for queued emails)
                old_max_retries = self.MAX_RETRIES
                self.MAX_RETRIES = 3  # Use fewer retries for queued emails
                
                result = self.send_with_guaranteed_delivery(
                    pdf_buffer=pdf_buffer,
                    filename=entry['filename'],
                    recipient=entry['recipient'],
                    student_name=entry['student_name'],
                    session_type=entry['session_type']
                )
                
                self.MAX_RETRIES = old_max_retries  # Restore original retry count
                
                if result['success']:
                    # Remove from queue
                    self.email_queue.remove(entry_id)
                    results['succeeded'] += 1
                    self.logger.info(f"Successfully sent queued email {entry_id}")
                else:
                    # Increment retry count
                    self.email_queue.increment_retry_count(entry_id)
                    results['still_failed'] += 1
                    self.logger.warning(f"Failed to send queued email {entry_id}")
                
                results['results'].append({
                    'entry_id': entry_id,
                    'filename': entry['filename'],
                    'success': result['success']
                })
                
            except Exception as e:
                self.logger.error(f"Error processing queue entry {entry_id}: {e}")
                results['still_failed'] += 1
        
        self.logger.info(f"Queue processing complete: {results['succeeded']}/{results['processed']} succeeded")
        return results


def send_box_backup_email(pdf_buffer: io.BytesIO,
                         filename: str,
                         student_name: str,
                         session_type: str,
                         config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Convenience function to send PDF backup to Box email.
    
    Args:
        pdf_buffer: BytesIO buffer containing PDF data
        filename: Name of the PDF file
        student_name: Name of the student
        session_type: Type of session ('OHI' or 'HPV Vaccine')
        config: Configuration dictionary (loads from config.json if not provided)
        
    Returns:
        Dictionary with results including success status and error details
    """
    # Load config if not provided
    if config is None:
        try:
            import json
            with open('config.json', 'r') as f:
                config = json.load(f)
        except Exception as e:
            return {
                'success': False,
                'error': f"Failed to load configuration: {e}",
                'attempts': 0
            }
    
    # Get Box email address based on session type with strict validation
    email_config = config.get('email_config', {})
    session_type_upper = session_type.upper()
    
    # Get logger instance at the beginning of the function
    logger = logging.getLogger(__name__)
    
    # Strict mapping for email selection - ensures correct routing
    recipient = None
    bot_type = None
    
    if 'OHI' in session_type_upper or 'ORAL' in session_type_upper or 'DENTAL' in session_type_upper:
        recipient = email_config.get('ohi_box_email')
        bot_type = 'OHI'
    elif 'HPV' in session_type_upper:
        recipient = email_config.get('hpv_box_email')
        bot_type = 'HPV'
    elif 'TOBACCO' in session_type_upper or 'SMOK' in session_type_upper or 'CESSATION' in session_type_upper:
        recipient = email_config.get('tobacco_box_email')
        bot_type = 'TOBACCO'
    elif 'PERIO' in session_type_upper or 'GUM' in session_type_upper or 'PERIODON' in session_type_upper:
        recipient = email_config.get('perio_box_email')
        bot_type = 'PERIO'
    else:
        # Log warning for unrecognized session type
        logger.warning(f"Unrecognized session type: '{session_type}'. Using HPV as default.")
        recipient = email_config.get('hpv_box_email')
        bot_type = 'HPV (default)'
    
    # Validate recipient email is configured
    if not recipient:
        logger.error(f"Box email not configured for {session_type} (bot_type: {bot_type})")
        return {
            'success': False,
            'error': f"Box email not configured for {session_type} (bot_type: {bot_type})",
            'attempts': 0
        }
    
    # Validate recipient email format (basic check)
    if '@u.box.com' not in recipient:
        logger.error(f"Invalid Box email format for {bot_type}: {recipient}")
        return {
            'success': False,
            'error': f"Invalid Box email format for {bot_type}: {recipient}",
            'attempts': 0
        }
    
    logger.info(f"Email mapping: Session='{session_type}' -> Bot={bot_type} -> Email={recipient}")
    
    # Set up SMTP logger
    logging_config = config.get('logging', {})
    log_dir = logging_config.get('smtp_log_directory', 'SMTP logs')
    log_file = logging_config.get('smtp_log_file', 'email_backup.log')
    
    # Create sender instance
    sender = SecureEmailSender(config)
    smtp_logger = sender.setup_smtp_logger(log_dir, os.path.basename(log_file))
    
    # Prepare email content
    from time_utils import get_cst_timestamp
    subject = f"{session_type} MI Practice Report - {student_name}"
    body = f"""MI Practice Report Backup

Student: {student_name}
Session Type: {session_type}
Report File: {filename}
Timestamp: {get_cst_timestamp()}

This is an automated backup of the MI practice feedback report.
"""
    
    # Get retry settings with validation
    max_retries = email_config.get('retry_attempts', 3)
    retry_delay = email_config.get('retry_delay', 5)
    
    # Ensure at least 1 attempt when config is valid
    if max_retries < 1:
        logger.warning(f"Invalid retry_attempts value ({max_retries}). Using default of 3.")
        max_retries = 3
    
    # Send with retry
    result = sender.send_email_with_retry(
        recipient=recipient,
        subject=subject,
        body=body,
        attachment_buffer=pdf_buffer,
        attachment_filename=filename,
        student_name=student_name,
        session_type=session_type,
        smtp_logger=smtp_logger,
        max_retries=max_retries,
        retry_delay=retry_delay
    )
    
    return result


# Example usage and testing
if __name__ == "__main__":
    import json
    
    print("Email Utils - Test Mode\n")
    
    # Test configuration loading
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
        
        sender = SecureEmailSender(config)
        
        print("Testing SMTP connection...")
        result = sender.test_connection()
        
        print(f"\nConnection Test Results:")
        print(f"  Status: {result['status']}")
        print(f"  Server: {result['smtp_server']}:{result['smtp_port']}")
        print(f"  Authentication: {'✅' if result['authentication'] else '❌'}")
        print(f"  Message: {result['message']}")
        
        if result['status'] == 'success':
            print("\n✅ Email utilities configured correctly!")
        else:
            print(f"\n⚠️  Configuration issue: {result['message']}")
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
