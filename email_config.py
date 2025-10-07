"""
Email Configuration Module for MI Chatbots

This module provides secure handling of SMTP credentials and email configuration.
It loads settings from config.json and retrieves sensitive credentials from
environment variables for enhanced security.

Features:
- Load SMTP settings from config.json
- Get password from environment variable
- Secure credential handling
- Email sending functionality with SSL/TLS support
"""

import os
import json
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from typing import Dict, Any, Optional
import io


class EmailConfigError(Exception):
    """Exception for email configuration errors."""
    pass


class EmailConfig:
    """
    Handler for secure email configuration and SMTP operations.
    
    Loads configuration from config.json and retrieves sensitive credentials
    from environment variables.
    """
    
    def __init__(self, config_path: str = "config.json"):
        """
        Initialize email configuration.
        
        Args:
            config_path: Path to configuration file
        """
        self.config_path = config_path
        self.config = self._load_config()
        
    def _load_config(self) -> Dict[str, Any]:
        """
        Load configuration from JSON file.
        
        Returns:
            Configuration dictionary
            
        Raises:
            EmailConfigError: If configuration cannot be loaded
        """
        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)
                
            if 'email_config' not in config:
                raise EmailConfigError("'email_config' section not found in config.json")
                
            return config['email_config']
        except FileNotFoundError:
            raise EmailConfigError(f"Configuration file not found: {self.config_path}")
        except json.JSONDecodeError as e:
            raise EmailConfigError(f"Invalid JSON in configuration file: {e}")
        except Exception as e:
            raise EmailConfigError(f"Failed to load configuration: {e}")
    
    def get_smtp_password(self) -> str:
        """
        Get SMTP password from environment variable.
        
        Returns:
            SMTP password
            
        Raises:
            EmailConfigError: If password is not set in environment
        """
        password = os.environ.get('SMTP_PASSWORD')
        
        if not password:
            raise EmailConfigError(
                "SMTP_PASSWORD environment variable is not set. "
                "Please set it before using email functionality."
            )
            
        return password
    
    def get_smtp_config(self) -> Dict[str, Any]:
        """
        Get complete SMTP configuration with password from environment.
        
        Returns:
            Dictionary with SMTP configuration
            
        Raises:
            EmailConfigError: If required configuration is missing
        """
        required_keys = ['smtp_server', 'smtp_port', 'smtp_user']
        
        for key in required_keys:
            if key not in self.config:
                raise EmailConfigError(f"Required configuration '{key}' not found")
        
        return {
            'smtp_server': self.config['smtp_server'],
            'smtp_port': self.config['smtp_port'],
            'smtp_ssl': self.config.get('smtp_ssl', True),
            'smtp_user': self.config['smtp_user'],
            'smtp_password': self.get_smtp_password()
        }
    
    def get_box_email(self, bot_type: str) -> str:
        """
        Get Box upload email address for specified bot type.
        
        Args:
            bot_type: Type of bot ('OHI' or 'HPV')
            
        Returns:
            Box upload email address
            
        Raises:
            EmailConfigError: If bot type is invalid or email not configured
        """
        bot_type = bot_type.upper()
        
        if bot_type == 'OHI':
            email = self.config.get('ohi_box_email')
            if not email:
                raise EmailConfigError("OHI Box email not configured")
            return email
        elif bot_type == 'HPV':
            email = self.config.get('hpv_box_email')
            if not email:
                raise EmailConfigError("HPV Box email not configured")
            return email
        else:
            raise EmailConfigError(f"Unknown bot type: {bot_type}")
    
    def send_email(self, recipient: str, subject: str, body: str, 
                   attachment_data: Optional[io.BytesIO] = None,
                   attachment_filename: Optional[str] = None,
                   attachment_type: str = 'application/pdf') -> None:
        """
        Send email with optional attachment using configured SMTP settings.
        
        Args:
            recipient: Email recipient address
            subject: Email subject
            body: Email body text
            attachment_data: Optional BytesIO buffer containing attachment data
            attachment_filename: Optional filename for attachment
            attachment_type: MIME type for attachment (default: application/pdf)
            
        Raises:
            EmailConfigError: If configuration is invalid
            smtplib.SMTPException: If email sending fails
        """
        smtp_config = self.get_smtp_config()
        
        # Create message
        msg = MIMEMultipart()
        msg['From'] = smtp_config['smtp_user']
        msg['To'] = recipient
        msg['Subject'] = subject
        
        # Add body
        msg.attach(MIMEText(body, 'plain'))
        
        # Add attachment if provided
        if attachment_data and attachment_filename:
            attachment_data.seek(0)
            mime_base, mime_subtype = attachment_type.split('/')
            attachment = MIMEBase(mime_base, mime_subtype)
            attachment.set_payload(attachment_data.read())
            encoders.encode_base64(attachment)
            attachment.add_header('Content-Disposition', 
                                f'attachment; filename={attachment_filename}')
            msg.attach(attachment)
        
        # Send email
        with smtplib.SMTP(smtp_config['smtp_server'], 
                         smtp_config['smtp_port'], 
                         timeout=30) as server:
            if smtp_config['smtp_ssl']:
                server.starttls()
            
            server.login(smtp_config['smtp_user'], 
                        smtp_config['smtp_password'])
            
            server.send_message(msg)
    
    def test_connection(self) -> Dict[str, Any]:
        """
        Test SMTP connection with configured settings.
        
        Returns:
            Dictionary with test results
        """
        result = {
            'success': False,
            'message': '',
            'smtp_server': self.config.get('smtp_server'),
            'smtp_port': self.config.get('smtp_port'),
            'smtp_user': self.config.get('smtp_user')
        }
        
        try:
            smtp_config = self.get_smtp_config()
            
            with smtplib.SMTP(smtp_config['smtp_server'], 
                             smtp_config['smtp_port'], 
                             timeout=30) as server:
                if smtp_config['smtp_ssl']:
                    server.starttls()
                
                server.login(smtp_config['smtp_user'], 
                           smtp_config['smtp_password'])
                
                result['success'] = True
                result['message'] = 'Connection successful'
                
        except EmailConfigError as e:
            result['message'] = f'Configuration error: {e}'
        except smtplib.SMTPAuthenticationError:
            result['message'] = 'Authentication failed - check credentials'
        except smtplib.SMTPException as e:
            result['message'] = f'SMTP error: {e}'
        except Exception as e:
            result['message'] = f'Unexpected error: {e}'
        
        return result


# Convenience function for backward compatibility
def get_email_config(config_path: str = "config.json") -> EmailConfig:
    """
    Get EmailConfig instance.
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        EmailConfig instance
    """
    return EmailConfig(config_path)


if __name__ == "__main__":
    """Test email configuration."""
    print("Email Configuration Test\n")
    
    try:
        email_config = EmailConfig()
        print("✅ Configuration loaded successfully")
        print(f"   SMTP Server: {email_config.config.get('smtp_server')}")
        print(f"   SMTP Port: {email_config.config.get('smtp_port')}")
        print(f"   SMTP User: {email_config.config.get('smtp_user')}")
        print(f"   SMTP SSL: {email_config.config.get('smtp_ssl')}")
        
        # Test Box emails
        print("\n📧 Box Email Addresses:")
        try:
            ohi_email = email_config.get_box_email('OHI')
            print(f"   OHI: {ohi_email}")
        except EmailConfigError as e:
            print(f"   ⚠️  OHI: {e}")
        
        try:
            hpv_email = email_config.get_box_email('HPV')
            print(f"   HPV: {hpv_email}")
        except EmailConfigError as e:
            print(f"   ⚠️  HPV: {e}")
        
        # Test password retrieval
        print("\n🔐 Password Configuration:")
        try:
            password = email_config.get_smtp_password()
            print(f"   ✅ SMTP password found (length: {len(password)})")
        except EmailConfigError as e:
            print(f"   ⚠️  {e}")
        
        # Test connection
        print("\n🔌 Testing SMTP Connection:")
        test_result = email_config.test_connection()
        if test_result['success']:
            print(f"   ✅ {test_result['message']}")
        else:
            print(f"   ❌ {test_result['message']}")
        
    except EmailConfigError as e:
        print(f"❌ Configuration error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
