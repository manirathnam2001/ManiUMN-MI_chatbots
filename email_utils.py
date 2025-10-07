"""
Email Utilities Module for Secure SMTP Operations

This module provides secure email sending functionality with:
- Environment variable support for credentials
- SSL/TLS connection handling
- Comprehensive error handling and logging
- Support for PDF attachments
"""

import smtplib
import ssl
import os
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from typing import Optional, Dict, Any, Union
import io


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


def send_box_upload_email(config: Dict[str, Any],
                          bot_type: str,
                          student_name: str,
                          pdf_buffer: io.BytesIO,
                          filename: str,
                          logger: Optional[logging.Logger] = None) -> bool:
    """
    Convenience function to send a Box upload email.
    
    Args:
        config: Configuration dictionary
        bot_type: Type of bot ('OHI' or 'HPV')
        student_name: Name of the student
        pdf_buffer: PDF data buffer
        filename: PDF filename
        logger: Optional logger instance
        
    Returns:
        True if successful, False otherwise
    """
    sender = SecureEmailSender(config, logger)
    
    # Determine recipient email
    bot_type = bot_type.upper()
    recipient = None
    
    # Check environment variables first
    if bot_type == 'OHI':
        recipient = os.environ.get('OHI_BOX_EMAIL')
    elif bot_type == 'HPV':
        recipient = os.environ.get('HPV_BOX_EMAIL')
    else:
        raise ValueError(f"Unknown bot type: {bot_type}")
    
    # Fall back to config if env var not set
    if not recipient and 'email_config' in config:
        if bot_type == 'OHI':
            recipient = config['email_config'].get('ohi_box_email')
        elif bot_type == 'HPV':
            recipient = config['email_config'].get('hpv_box_email')
    
    # Fall back to box_upload config
    if not recipient and 'box_upload' in config:
        if bot_type == 'OHI':
            recipient = config['box_upload'].get('ohi_email')
        elif bot_type == 'HPV':
            recipient = config['box_upload'].get('hpv_email')
    
    if not recipient:
        raise EmailConfigError(
            f"Box email not configured for {bot_type}. "
            f"Set {bot_type}_BOX_EMAIL environment variable or configure in config file."
        )
    
    # Create email content
    subject = f'MI Assessment Report - {student_name} - {bot_type}'
    body = f"""
MI Assessment Report

Bot Type: {bot_type}
Student: {student_name}
Filename: {filename}

This is an automated upload to Box.
"""
    
    try:
        return sender.send_email_with_attachment(
            recipient=recipient,
            subject=subject,
            body=body,
            attachment_buffer=pdf_buffer,
            attachment_filename=filename,
            attachment_type='application/pdf'
        )
    except EmailSendError:
        return False


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
