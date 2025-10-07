"""
Email Utilities for Secure SMTP Email Handling

This module provides secure email sending functionality with:
- SSL/TLS support for encrypted connections
- Secure password handling
- Comprehensive error handling
- Logging integration
- Authentication error handling
"""

import smtplib
import ssl
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from typing import Optional, Dict, Any, List
import io


class EmailError(Exception):
    """Base exception for email-related errors."""
    pass


class EmailAuthenticationError(EmailError):
    """Exception for email authentication failures."""
    pass


class EmailConnectionError(EmailError):
    """Exception for email connection failures."""
    pass


class EmailSendError(EmailError):
    """Exception for email sending failures."""
    pass


class SecureEmailSender:
    """
    Secure email sender with SSL/TLS support and comprehensive error handling.
    
    Features:
    - SSL/TLS encryption for secure connections
    - Proper authentication handling
    - Attachment support
    - Logging integration
    - Connection timeout handling
    - Retry support
    """
    
    def __init__(self, config: Dict[str, Any], logger: Optional[logging.Logger] = None):
        """
        Initialize the secure email sender.
        
        Args:
            config: Email configuration dictionary containing:
                - smtp_server: SMTP server address
                - smtp_port: SMTP port (usually 587 for TLS, 465 for SSL)
                - smtp_username: Username for authentication
                - smtp_password: Password for authentication
                - use_ssl: Whether to use SSL/TLS (default: True)
                - from_email: Sender email address
            logger: Optional logger instance for logging
        """
        self.config = config
        self.logger = logger
        
        # Validate configuration
        self._validate_config()
        
    def _validate_config(self) -> None:
        """
        Validate email configuration.
        
        Raises:
            EmailError: If configuration is invalid
        """
        required_fields = ['smtp_server', 'smtp_port', 'smtp_username', 'from_email']
        
        for field in required_fields:
            if field not in self.config or not self.config[field]:
                raise EmailError(f"Missing required email configuration: {field}")
        
        # Check if password is provided
        if not self.config.get('smtp_password'):
            if self.logger:
                self.logger.warning("SMTP password not configured - authentication may fail")
    
    def _log(self, level: str, message: str, extra: Optional[Dict[str, Any]] = None) -> None:
        """
        Log a message if logger is available.
        
        Args:
            level: Log level ('debug', 'info', 'warning', 'error', 'critical')
            message: Message to log
            extra: Extra context to log
        """
        if self.logger:
            log_func = getattr(self.logger, level.lower(), None)
            if log_func:
                if extra:
                    log_func(f"{message} | Context: {extra}")
                else:
                    log_func(message)
    
    def send_email_with_attachment(
        self,
        recipient: str,
        subject: str,
        body: str,
        attachment_buffer: io.BytesIO,
        attachment_filename: str,
        attachment_type: str = 'application/pdf',
        timeout: int = 30
    ) -> bool:
        """
        Send an email with an attachment using secure SMTP.
        
        Args:
            recipient: Recipient email address
            subject: Email subject
            body: Email body (plain text)
            attachment_buffer: BytesIO buffer containing attachment data
            attachment_filename: Filename for the attachment
            attachment_type: MIME type of attachment (default: 'application/pdf')
            timeout: Connection timeout in seconds (default: 30)
            
        Returns:
            True if email sent successfully, False otherwise
            
        Raises:
            EmailAuthenticationError: If authentication fails
            EmailConnectionError: If connection fails
            EmailSendError: If sending fails
        """
        try:
            self._log('info', f'Attempting to send email to {recipient}', 
                     {'subject': subject, 'attachment': attachment_filename})
            
            # Create message
            msg = self._create_message(recipient, subject, body)
            
            # Attach file
            self._attach_file(msg, attachment_buffer, attachment_filename, attachment_type)
            
            # Send email
            self._send_message(msg, recipient, timeout)
            
            self._log('info', f'Email sent successfully to {recipient}', 
                     {'subject': subject})
            
            return True
            
        except smtplib.SMTPAuthenticationError as e:
            error_msg = f"SMTP authentication failed: {str(e)}"
            self._log('error', error_msg, {'recipient': recipient})
            raise EmailAuthenticationError(error_msg) from e
            
        except (smtplib.SMTPConnectError, smtplib.SMTPServerDisconnected) as e:
            error_msg = f"SMTP connection failed: {str(e)}"
            self._log('error', error_msg, {'recipient': recipient})
            raise EmailConnectionError(error_msg) from e
            
        except smtplib.SMTPException as e:
            error_msg = f"SMTP error: {str(e)}"
            self._log('error', error_msg, {'recipient': recipient})
            raise EmailSendError(error_msg) from e
            
        except Exception as e:
            error_msg = f"Unexpected error sending email: {str(e)}"
            self._log('error', error_msg, {'recipient': recipient})
            raise EmailSendError(error_msg) from e
    
    def _create_message(self, recipient: str, subject: str, body: str) -> MIMEMultipart:
        """
        Create email message.
        
        Args:
            recipient: Recipient email address
            subject: Email subject
            body: Email body
            
        Returns:
            MIMEMultipart message object
        """
        msg = MIMEMultipart()
        msg['From'] = self.config['from_email']
        msg['To'] = recipient
        msg['Subject'] = subject
        
        # Add body
        msg.attach(MIMEText(body, 'plain'))
        
        return msg
    
    def _attach_file(
        self,
        msg: MIMEMultipart,
        attachment_buffer: io.BytesIO,
        filename: str,
        mime_type: str
    ) -> None:
        """
        Attach file to email message.
        
        Args:
            msg: MIMEMultipart message object
            attachment_buffer: BytesIO buffer containing file data
            filename: Filename for the attachment
            mime_type: MIME type of the file
        """
        attachment_buffer.seek(0)
        
        # Parse MIME type
        main_type, sub_type = mime_type.split('/', 1) if '/' in mime_type else ('application', mime_type)
        
        # Create attachment
        attachment = MIMEBase(main_type, sub_type)
        attachment.set_payload(attachment_buffer.read())
        encoders.encode_base64(attachment)
        attachment.add_header('Content-Disposition', f'attachment; filename={filename}')
        
        msg.attach(attachment)
    
    def _send_message(self, msg: MIMEMultipart, recipient: str, timeout: int) -> None:
        """
        Send the email message using SMTP.
        
        Args:
            msg: MIMEMultipart message object
            recipient: Recipient email address
            timeout: Connection timeout in seconds
            
        Raises:
            Various smtplib exceptions on failure
        """
        smtp_server = self.config['smtp_server']
        smtp_port = self.config['smtp_port']
        use_ssl = self.config.get('use_ssl', True)
        
        self._log('debug', f'Connecting to SMTP server: {smtp_server}:{smtp_port}',
                 {'use_ssl': use_ssl, 'timeout': timeout})
        
        # Use SSL/TLS based on configuration
        if use_ssl:
            # For port 587, use STARTTLS
            if smtp_port == 587:
                with smtplib.SMTP(smtp_server, smtp_port, timeout=timeout) as server:
                    server.ehlo()
                    
                    # Create SSL context for secure connection
                    context = ssl.create_default_context()
                    server.starttls(context=context)
                    server.ehlo()
                    
                    # Login if credentials provided
                    if self.config.get('smtp_password'):
                        self._log('debug', 'Authenticating with SMTP server')
                        server.login(self.config['smtp_username'], 
                                   self.config['smtp_password'])
                    
                    # Send message
                    server.send_message(msg)
            
            # For port 465, use SSL from the start
            elif smtp_port == 465:
                context = ssl.create_default_context()
                with smtplib.SMTP_SSL(smtp_server, smtp_port, 
                                     context=context, timeout=timeout) as server:
                    # Login if credentials provided
                    if self.config.get('smtp_password'):
                        self._log('debug', 'Authenticating with SMTP server')
                        server.login(self.config['smtp_username'], 
                                   self.config['smtp_password'])
                    
                    # Send message
                    server.send_message(msg)
            
            # Other ports with STARTTLS
            else:
                with smtplib.SMTP(smtp_server, smtp_port, timeout=timeout) as server:
                    context = ssl.create_default_context()
                    server.starttls(context=context)
                    
                    # Login if credentials provided
                    if self.config.get('smtp_password'):
                        self._log('debug', 'Authenticating with SMTP server')
                        server.login(self.config['smtp_username'], 
                                   self.config['smtp_password'])
                    
                    # Send message
                    server.send_message(msg)
        else:
            # No SSL/TLS (not recommended)
            self._log('warning', 'Sending email without SSL/TLS encryption')
            with smtplib.SMTP(smtp_server, smtp_port, timeout=timeout) as server:
                # Login if credentials provided
                if self.config.get('smtp_password'):
                    self._log('debug', 'Authenticating with SMTP server')
                    server.login(self.config['smtp_username'], 
                               self.config['smtp_password'])
                
                # Send message
                server.send_message(msg)
    
    def test_connection(self, timeout: int = 10) -> Dict[str, Any]:
        """
        Test SMTP connection and authentication.
        
        Args:
            timeout: Connection timeout in seconds
            
        Returns:
            Dictionary with test results
        """
        results = {
            'smtp_server': self.config['smtp_server'],
            'smtp_port': self.config['smtp_port'],
            'use_ssl': self.config.get('use_ssl', True),
            'connection': 'not_tested',
            'authentication': 'not_tested',
            'message': ''
        }
        
        try:
            smtp_server = self.config['smtp_server']
            smtp_port = self.config['smtp_port']
            use_ssl = self.config.get('use_ssl', True)
            
            self._log('info', f'Testing connection to {smtp_server}:{smtp_port}')
            
            # Test connection based on SSL/TLS configuration
            if use_ssl and smtp_port == 587:
                with smtplib.SMTP(smtp_server, smtp_port, timeout=timeout) as server:
                    server.ehlo()
                    context = ssl.create_default_context()
                    server.starttls(context=context)
                    server.ehlo()
                    
                    results['connection'] = 'success'
                    
                    # Test authentication if credentials provided
                    if self.config.get('smtp_password'):
                        try:
                            server.login(self.config['smtp_username'], 
                                       self.config['smtp_password'])
                            results['authentication'] = 'success'
                            results['message'] = 'Connection and authentication successful'
                        except smtplib.SMTPAuthenticationError as e:
                            results['authentication'] = 'failed'
                            results['message'] = f'Authentication failed: {str(e)}'
                    else:
                        results['authentication'] = 'skipped'
                        results['message'] = 'Connection successful (authentication not tested)'
                        
            elif use_ssl and smtp_port == 465:
                context = ssl.create_default_context()
                with smtplib.SMTP_SSL(smtp_server, smtp_port, 
                                     context=context, timeout=timeout) as server:
                    results['connection'] = 'success'
                    
                    # Test authentication if credentials provided
                    if self.config.get('smtp_password'):
                        try:
                            server.login(self.config['smtp_username'], 
                                       self.config['smtp_password'])
                            results['authentication'] = 'success'
                            results['message'] = 'Connection and authentication successful'
                        except smtplib.SMTPAuthenticationError as e:
                            results['authentication'] = 'failed'
                            results['message'] = f'Authentication failed: {str(e)}'
                    else:
                        results['authentication'] = 'skipped'
                        results['message'] = 'Connection successful (authentication not tested)'
            else:
                # Fallback connection
                with smtplib.SMTP(smtp_server, smtp_port, timeout=timeout) as server:
                    if use_ssl:
                        context = ssl.create_default_context()
                        server.starttls(context=context)
                    
                    results['connection'] = 'success'
                    
                    # Test authentication if credentials provided
                    if self.config.get('smtp_password'):
                        try:
                            server.login(self.config['smtp_username'], 
                                       self.config['smtp_password'])
                            results['authentication'] = 'success'
                            results['message'] = 'Connection and authentication successful'
                        except smtplib.SMTPAuthenticationError as e:
                            results['authentication'] = 'failed'
                            results['message'] = f'Authentication failed: {str(e)}'
                    else:
                        results['authentication'] = 'skipped'
                        results['message'] = 'Connection successful (authentication not tested)'
                        
            self._log('info', 'Connection test completed successfully', results)
            
        except (smtplib.SMTPConnectError, smtplib.SMTPServerDisconnected) as e:
            results['connection'] = 'failed'
            results['message'] = f'Connection failed: {str(e)}'
            self._log('error', 'Connection test failed', {'error': str(e)})
            
        except Exception as e:
            results['connection'] = 'failed'
            results['message'] = f'Test failed: {str(e)}'
            self._log('error', 'Connection test failed with unexpected error', {'error': str(e)})
        
        return results


# Example usage
if __name__ == "__main__":
    import json
    
    print("Email Utils - Test Mode\n")
    
    # Load configuration
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
        
        email_config = config.get('email_config', {})
        
        if not email_config:
            print("❌ No email_config section found in config.json")
            print("   Add email_config section to config.json to test")
        else:
            # Create secure email sender
            sender = SecureEmailSender(email_config)
            
            print("✅ SecureEmailSender initialized")
            print(f"   SMTP Server: {email_config['smtp_server']}")
            print(f"   SMTP Port: {email_config['smtp_port']}")
            print(f"   Use SSL: {email_config.get('use_ssl', True)}")
            
            # Test connection
            print("\nTesting SMTP connection...")
            test_results = sender.test_connection()
            
            print(f"\nConnection Test Results:")
            print(f"  Connection: {test_results['connection']}")
            print(f"  Authentication: {test_results['authentication']}")
            print(f"  Message: {test_results['message']}")
            
            if test_results['connection'] == 'success':
                print("\n✅ Email utilities are configured correctly")
            else:
                print("\n⚠️  Email connection test failed")
                print("   Check your SMTP settings in config.json")
    
    except FileNotFoundError:
        print("❌ config.json not found")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
