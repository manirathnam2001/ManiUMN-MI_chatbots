"""
Box Integration Module for MI Chatbots

This module provides functionality to send PDF reports to Box via email upload addresses.
Includes error handling for various failure scenarios and integration with the logging system.

Features:
- Email sending to Box upload addresses
- Separate handling for OHI and HPV bots
- Comprehensive error handling
- Integration with upload_logs.py for tracking
- Network timeout handling
- Retry logic for transient failures
"""

import smtplib
import json
import os
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from typing import Optional, Dict, Any
import io

from upload_logs import BoxUploadLogger


class BoxIntegrationError(Exception):
    """Base exception for Box integration errors."""
    pass


class EmailDeliveryError(BoxIntegrationError):
    """Exception for email delivery failures."""
    pass


class NetworkTimeoutError(BoxIntegrationError):
    """Exception for network timeout issues."""
    pass


class InvalidFileFormatError(BoxIntegrationError):
    """Exception for invalid file format issues."""
    pass


class StorageQuotaError(BoxIntegrationError):
    """Exception for storage quota issues."""
    pass


class BoxUploader:
    """
    Handler for uploading PDF reports to Box via email.
    
    Integrates with BoxUploadLogger for comprehensive tracking and monitoring.
    """
    
    def __init__(self, bot_type: str, config_path: str = "config.json"):
        """
        Initialize the Box uploader.
        
        Args:
            bot_type: Type of bot ('OHI' or 'HPV')
            config_path: Path to configuration file
        """
        self.bot_type = bot_type.upper()
        self.config = self._load_config(config_path)
        self.logger = BoxUploadLogger(self.bot_type, 
                                      log_directory=self.config['logging']['log_directory'])
        
        # Validate configuration
        self._validate_config()
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """
        Load configuration from JSON file.
        
        Args:
            config_path: Path to configuration file
            
        Returns:
            Configuration dictionary
        """
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            raise BoxIntegrationError(f"Failed to load configuration: {e}")
    
    def _validate_config(self) -> None:
        """
        Validate that required configuration is present.
        
        Raises:
            BoxIntegrationError: If configuration is invalid
        """
        required_keys = ['box_upload', 'logging', 'email']
        
        for key in required_keys:
            if key not in self.config:
                raise BoxIntegrationError(f"Missing required config section: {key}")
        
        # Check Box upload emails
        if self.bot_type == 'OHI':
            if not self.config['box_upload'].get('ohi_email'):
                raise BoxIntegrationError("OHI Box email not configured")
        elif self.bot_type == 'HPV':
            if not self.config['box_upload'].get('hpv_email'):
                raise BoxIntegrationError("HPV Box email not configured")
        
        # Check email settings (only if enabled)
        if self.config['box_upload'].get('enabled', False):
            email_config = self.config['email']
            if not email_config.get('smtp_server') or not email_config.get('sender_email'):
                self.logger.log_warning(
                    'CONFIG_WARNING',
                    'Email settings incomplete. Box upload disabled.',
                    {'smtp_server': email_config.get('smtp_server'),
                     'sender_email': email_config.get('sender_email')}
                )
    
    def _get_box_email(self) -> str:
        """
        Get the Box upload email address for this bot type.
        
        Returns:
            Box upload email address
        """
        if self.bot_type == 'OHI':
            return self.config['box_upload']['ohi_email']
        elif self.bot_type == 'HPV':
            return self.config['box_upload']['hpv_email']
        else:
            raise BoxIntegrationError(f"Unknown bot type: {self.bot_type}")
    
    def _validate_pdf(self, pdf_buffer: io.BytesIO) -> bool:
        """
        Validate that the buffer contains a valid PDF file.
        
        Args:
            pdf_buffer: BytesIO buffer containing PDF data
            
        Returns:
            True if valid PDF, False otherwise
        """
        try:
            # Check PDF magic number
            pdf_buffer.seek(0)
            header = pdf_buffer.read(5)
            pdf_buffer.seek(0)
            
            return header == b'%PDF-'
        except Exception:
            return False
    
    def upload_pdf_to_box(self, student_name: str, pdf_buffer: io.BytesIO, 
                         filename: str, max_retries: int = 3, 
                         retry_delay: int = 2) -> bool:
        """
        Upload a PDF report to Box via email.
        
        Args:
            student_name: Name of the student
            pdf_buffer: BytesIO buffer containing PDF data
            filename: Name for the PDF file
            max_retries: Maximum number of retry attempts (default: 3)
            retry_delay: Delay between retries in seconds (default: 2)
            
        Returns:
            True if upload successful, False otherwise
            
        Raises:
            InvalidFileFormatError: If PDF format is invalid
            EmailDeliveryError: If email delivery fails after retries
            NetworkTimeoutError: If network timeout occurs
        """
        # Check if Box upload is enabled
        if not self.config['box_upload'].get('enabled', False):
            self.logger.log_warning(
                'UPLOAD_DISABLED',
                'Box upload is disabled in configuration',
                {'student_name': student_name, 'filename': filename}
            )
            return False
        
        # Validate PDF
        if not self._validate_pdf(pdf_buffer):
            error_msg = "Invalid PDF format"
            self.logger.log_upload_failure(
                student_name, filename, self._get_box_email(), 
                error_msg, 'INVALID_FORMAT'
            )
            raise InvalidFileFormatError(error_msg)
        
        # Get file size
        pdf_buffer.seek(0, 2)  # Seek to end
        file_size = pdf_buffer.tell()
        pdf_buffer.seek(0)  # Reset to beginning
        
        # Get Box email address
        box_email = self._get_box_email()
        
        # Log upload attempt
        self.logger.log_upload_attempt(student_name, filename, box_email, file_size)
        
        # Try sending email with retries
        attempt = 0
        last_error = None
        
        while attempt < max_retries:
            attempt += 1
            
            try:
                start_time = time.time()
                
                # Send email
                self._send_email(student_name, pdf_buffer, filename, box_email)
                
                delivery_time = time.time() - start_time
                
                # Log success
                self.logger.log_upload_success(
                    student_name, filename, box_email, delivery_time
                )
                self.logger.log_email_delivery_status(box_email, 'sent')
                
                return True
                
            except smtplib.SMTPServerDisconnected as e:
                last_error = NetworkTimeoutError(f"SMTP server disconnected: {e}")
                self.logger.log_warning(
                    'NETWORK_ERROR',
                    f'Attempt {attempt}/{max_retries} failed: {str(e)}',
                    {'student_name': student_name, 'filename': filename}
                )
                
            except smtplib.SMTPException as e:
                last_error = EmailDeliveryError(f"SMTP error: {e}")
                self.logger.log_warning(
                    'EMAIL_ERROR',
                    f'Attempt {attempt}/{max_retries} failed: {str(e)}',
                    {'student_name': student_name, 'filename': filename}
                )
                
            except Exception as e:
                last_error = BoxIntegrationError(f"Unexpected error: {e}")
                self.logger.log_error(
                    'UNKNOWN_ERROR',
                    f'Attempt {attempt}/{max_retries} failed: {str(e)}',
                    {'student_name': student_name, 'filename': filename}
                )
            
            # Wait before retry (except on last attempt)
            if attempt < max_retries:
                time.sleep(retry_delay * attempt)  # Exponential backoff
        
        # All retries failed
        error_msg = str(last_error) if last_error else "Unknown error"
        self.logger.log_upload_failure(
            student_name, filename, box_email, error_msg,
            type(last_error).__name__ if last_error else 'UNKNOWN'
        )
        self.logger.log_email_delivery_status(box_email, 'failed')
        
        return False
    
    def _send_email(self, student_name: str, pdf_buffer: io.BytesIO, 
                   filename: str, recipient: str) -> None:
        """
        Send email with PDF attachment.
        
        Args:
            student_name: Name of the student
            pdf_buffer: BytesIO buffer containing PDF data
            filename: Name for the PDF file
            recipient: Email recipient address
            
        Raises:
            smtplib.SMTPException: If email sending fails
        """
        email_config = self.config['email']
        
        # Create message
        msg = MIMEMultipart()
        msg['From'] = email_config['sender_email']
        msg['To'] = recipient
        msg['Subject'] = f'MI Assessment Report - {student_name} - {self.bot_type}'
        
        # Add body
        body = f"""
MI Assessment Report

Bot Type: {self.bot_type}
Student: {student_name}
Filename: {filename}

This is an automated upload to Box.
"""
        msg.attach(MIMEText(body, 'plain'))
        
        # Attach PDF
        pdf_buffer.seek(0)
        attachment = MIMEBase('application', 'pdf')
        attachment.set_payload(pdf_buffer.read())
        encoders.encode_base64(attachment)
        attachment.add_header('Content-Disposition', f'attachment; filename={filename}')
        msg.attach(attachment)
        
        # Send email
        with smtplib.SMTP(email_config['smtp_server'], 
                         email_config['smtp_port'], 
                         timeout=30) as server:
            if email_config.get('use_tls', True):
                server.starttls()
            
            # Login only if credentials provided
            if email_config.get('sender_password'):
                server.login(email_config['sender_email'], 
                           email_config['sender_password'])
            
            server.send_message(msg)
    
    def test_connection(self) -> Dict[str, Any]:
        """
        Test the email connection and configuration.
        
        Returns:
            Dictionary with test results
        """
        results = {
            'box_upload_enabled': self.config['box_upload'].get('enabled', False),
            'bot_type': self.bot_type,
            'box_email': self._get_box_email(),
            'smtp_configured': bool(self.config['email'].get('smtp_server')),
            'connection_test': 'not_attempted'
        }
        
        if not results['box_upload_enabled']:
            results['message'] = 'Box upload is disabled in configuration'
            return results
        
        if not results['smtp_configured']:
            results['message'] = 'SMTP server not configured'
            return results
        
        # Try to connect to SMTP server
        try:
            email_config = self.config['email']
            with smtplib.SMTP(email_config['smtp_server'], 
                            email_config['smtp_port'], 
                            timeout=10) as server:
                if email_config.get('use_tls', True):
                    server.starttls()
                
                results['connection_test'] = 'success'
                results['message'] = 'SMTP connection successful'
        except Exception as e:
            results['connection_test'] = 'failed'
            results['message'] = f'SMTP connection failed: {str(e)}'
            
            self.logger.log_error(
                'CONNECTION_TEST_FAILED',
                str(e),
                {'smtp_server': email_config['smtp_server']}
            )
        
        return results


# Example usage and testing
if __name__ == "__main__":
    print("Box Uploader - Test Mode\n")
    
    # Test configuration loading
    try:
        ohi_uploader = BoxUploader("OHI")
        print(f"✅ OHI uploader initialized")
        print(f"   Box email: {ohi_uploader._get_box_email()}")
        
        hpv_uploader = BoxUploader("HPV")
        print(f"✅ HPV uploader initialized")
        print(f"   Box email: {hpv_uploader._get_box_email()}")
        
        # Test connection
        print("\nTesting connections...")
        ohi_test = ohi_uploader.test_connection()
        print(f"\nOHI Connection Test:")
        print(f"  Enabled: {ohi_test['box_upload_enabled']}")
        print(f"  Box Email: {ohi_test['box_email']}")
        print(f"  Status: {ohi_test['connection_test']}")
        print(f"  Message: {ohi_test['message']}")
        
        hpv_test = hpv_uploader.test_connection()
        print(f"\nHPV Connection Test:")
        print(f"  Enabled: {hpv_test['box_upload_enabled']}")
        print(f"  Box Email: {hpv_test['box_email']}")
        print(f"  Status: {hpv_test['connection_test']}")
        print(f"  Message: {hpv_test['message']}")
        
        print("\n✅ Tests completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
