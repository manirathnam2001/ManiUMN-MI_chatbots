"""
Email Utilities Module for Secure SMTP Operations

This module provides secure email sending functionality with:
- Environment variable support for credentials
- SSL/TLS connection handling
- Comprehensive error handling and logging
- Support for PDF attachments
- Daily rotating logs with retry tracking
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
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Unrecognized session type: '{session_type}'. Using HPV as default.")
        recipient = email_config.get('hpv_box_email')
        bot_type = 'HPV (default)'
    
    # Validate recipient email is configured
    if not recipient:
        return {
            'success': False,
            'error': f"Box email not configured for {session_type} (bot_type: {bot_type})",
            'attempts': 0
        }
    
    # Validate recipient email format (basic check)
    if '@u.box.com' not in recipient:
        return {
            'success': False,
            'error': f"Invalid Box email format for {bot_type}: {recipient}",
            'attempts': 0
        }
    
    # Log the email mapping for audit trail
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"Email mapping: Session='{session_type}' -> Bot={bot_type} -> Email={recipient}")
    
    # Set up SMTP logger
    logging_config = config.get('logging', {})
    log_dir = logging_config.get('smtp_log_directory', 'SMTP logs')
    log_file = logging_config.get('smtp_log_file', 'email_backup.log')
    
    # Create sender instance
    sender = SecureEmailSender(config)
    smtp_logger = sender.setup_smtp_logger(log_dir, os.path.basename(log_file))
    
    # Prepare email content
    subject = f"{session_type} MI Practice Report - {student_name}"
    body = f"""MI Practice Report Backup

Student: {student_name}
Session Type: {session_type}
Report File: {filename}
Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

This is an automated backup of the MI practice feedback report.
"""
    
    # Get retry settings
    max_retries = email_config.get('retry_attempts', 3)
    retry_delay = email_config.get('retry_delay', 5)
    
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
