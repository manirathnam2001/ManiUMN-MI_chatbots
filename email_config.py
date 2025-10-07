"""
Email Configuration Management for MI Chatbots

This module provides utilities for managing email configuration settings
used for Box integration and email delivery.

Features:
- Load and validate email configuration
- Manage SMTP settings
- Handle Box email addresses
- Configuration validation
"""

import json
from typing import Dict, Any, Optional


class EmailConfig:
    """
    Email configuration manager for Box integration.
    
    Handles loading, validation, and access to email-related configuration
    settings including SMTP server details and Box email addresses.
    """
    
    def __init__(self, config_path: str = "config.json"):
        """
        Initialize email configuration.
        
        Args:
            config_path: Path to configuration file (default: config.json)
        """
        self.config_path = config_path
        self.config = self._load_config()
        
    def _load_config(self) -> Dict[str, Any]:
        """
        Load configuration from JSON file.
        
        Returns:
            Configuration dictionary
            
        Raises:
            FileNotFoundError: If config file doesn't exist
            json.JSONDecodeError: If config file is invalid JSON
        """
        with open(self.config_path, 'r') as f:
            return json.load(f)
    
    def get_smtp_server(self) -> str:
        """
        Get SMTP server address.
        
        Returns:
            SMTP server address (default: smtp.gmail.com)
        """
        # Try email_config first, fallback to email
        smtp_server = self.config.get('email_config', {}).get('smtp_server')
        if not smtp_server:
            smtp_server = self.config.get('email', {}).get('smtp_server', 'smtp.gmail.com')
        return smtp_server
    
    def get_smtp_port(self) -> int:
        """
        Get SMTP server port.
        
        Returns:
            SMTP port number (default: 587)
        """
        # Try email_config first, fallback to email
        smtp_port = self.config.get('email_config', {}).get('smtp_port')
        if not smtp_port:
            smtp_port = self.config.get('email', {}).get('smtp_port', 587)
        return smtp_port
    
    def get_sender_email(self) -> Optional[str]:
        """
        Get sender email address.
        
        Returns:
            Sender email address or None if not configured
        """
        # Try email_config first, fallback to email
        sender_email = self.config.get('email_config', {}).get('sender_email')
        if not sender_email:
            sender_email = self.config.get('email', {}).get('sender_email')
        return sender_email
    
    def get_sender_password(self) -> Optional[str]:
        """
        Get sender email password.
        
        Returns:
            Sender password or None if not configured
        """
        # Try email_config first, fallback to email
        sender_password = self.config.get('email_config', {}).get('sender_password')
        if not sender_password:
            sender_password = self.config.get('email', {}).get('sender_password')
        return sender_password
    
    def use_tls(self) -> bool:
        """
        Check if TLS should be used for SMTP connection.
        
        Returns:
            True if TLS should be used (default: True)
        """
        # Try email_config first, fallback to email
        use_tls = self.config.get('email_config', {}).get('use_tls')
        if use_tls is None:
            use_tls = self.config.get('email', {}).get('use_tls', True)
        return use_tls
    
    def get_ohi_box_email(self) -> str:
        """
        Get OHI bot Box email address.
        
        Returns:
            OHI Box email address
        """
        # Try email_config first, fallback to box_upload
        ohi_email = self.config.get('email_config', {}).get('ohi_box_email')
        if not ohi_email:
            ohi_email = self.config.get('box_upload', {}).get('ohi_email', 
                                                              'OHI_dir.zcdwwmukjr9ab546@u.box.com')
        return ohi_email
    
    def get_hpv_box_email(self) -> str:
        """
        Get HPV bot Box email address.
        
        Returns:
            HPV Box email address
        """
        # Try email_config first, fallback to box_upload
        hpv_email = self.config.get('email_config', {}).get('hpv_box_email')
        if not hpv_email:
            hpv_email = self.config.get('box_upload', {}).get('hpv_email', 
                                                              'HPV_Dir.yqz3brxlhcurhp2l@u.box.com')
        return hpv_email
    
    def get_box_email(self, bot_type: str) -> str:
        """
        Get Box email address for a specific bot type.
        
        Args:
            bot_type: Type of bot ('OHI' or 'HPV')
            
        Returns:
            Box email address for the specified bot
            
        Raises:
            ValueError: If bot_type is not 'OHI' or 'HPV'
        """
        bot_type = bot_type.upper()
        if bot_type == 'OHI':
            return self.get_ohi_box_email()
        elif bot_type == 'HPV':
            return self.get_hpv_box_email()
        else:
            raise ValueError(f"Invalid bot type: {bot_type}. Must be 'OHI' or 'HPV'")
    
    def is_box_enabled(self) -> bool:
        """
        Check if Box upload is enabled.
        
        Returns:
            True if Box upload is enabled, False otherwise
        """
        return self.config.get('box_upload', {}).get('enabled', False)
    
    def is_configured(self) -> bool:
        """
        Check if email is properly configured with required settings.
        
        Returns:
            True if SMTP server and sender email are configured
        """
        smtp_server = self.get_smtp_server()
        sender_email = self.get_sender_email()
        return bool(smtp_server and sender_email)
    
    def get_log_directory(self) -> str:
        """
        Get log directory path.
        
        Returns:
            Log directory path (default: 'logs')
        """
        return self.config.get('logging', {}).get('log_directory', 'logs')
    
    def get_max_log_size_mb(self) -> int:
        """
        Get maximum log file size in MB.
        
        Returns:
            Maximum log size in MB (default: 10)
        """
        return self.config.get('logging', {}).get('max_log_size_mb', 10)
    
    def get_backup_count(self) -> int:
        """
        Get number of backup log files to keep.
        
        Returns:
            Number of backup files (default: 5)
        """
        return self.config.get('logging', {}).get('backup_count', 5)
    
    def get_log_level(self) -> str:
        """
        Get logging level.
        
        Returns:
            Log level string (default: 'INFO')
        """
        return self.config.get('logging', {}).get('log_level', 'INFO')
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Get all configuration as a dictionary.
        
        Returns:
            Complete configuration dictionary
        """
        return {
            'smtp_server': self.get_smtp_server(),
            'smtp_port': self.get_smtp_port(),
            'sender_email': self.get_sender_email(),
            'use_tls': self.use_tls(),
            'ohi_box_email': self.get_ohi_box_email(),
            'hpv_box_email': self.get_hpv_box_email(),
            'box_enabled': self.is_box_enabled(),
            'configured': self.is_configured(),
            'log_directory': self.get_log_directory(),
            'max_log_size_mb': self.get_max_log_size_mb(),
            'backup_count': self.get_backup_count(),
            'log_level': self.get_log_level()
        }


# Example usage and testing
if __name__ == "__main__":
    print("Email Configuration - Test Mode\n")
    
    try:
        config = EmailConfig()
        
        print("Email Configuration:")
        print(f"  SMTP Server: {config.get_smtp_server()}")
        print(f"  SMTP Port: {config.get_smtp_port()}")
        print(f"  Sender Email: {config.get_sender_email() or '(not configured)'}")
        print(f"  Use TLS: {config.use_tls()}")
        
        print("\nBox Configuration:")
        print(f"  OHI Email: {config.get_ohi_box_email()}")
        print(f"  HPV Email: {config.get_hpv_box_email()}")
        print(f"  Box Enabled: {config.is_box_enabled()}")
        
        print("\nLogging Configuration:")
        print(f"  Log Directory: {config.get_log_directory()}")
        print(f"  Max Log Size: {config.get_max_log_size_mb()} MB")
        print(f"  Backup Count: {config.get_backup_count()}")
        print(f"  Log Level: {config.get_log_level()}")
        
        print(f"\nConfiguration Status:")
        print(f"  Properly Configured: {config.is_configured()}")
        
        print("\n✅ Email configuration loaded successfully!")
        
    except Exception as e:
        print(f"\n❌ Error loading configuration: {e}")
        import traceback
        traceback.print_exc()
