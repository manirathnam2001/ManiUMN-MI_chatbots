"""
Configuration Loader for MI Chatbots

This module handles loading configuration from environment variables and config files.
Environment variables take precedence over config file values for security.
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

# Try to import python-dotenv for .env file support
try:
    from dotenv import load_dotenv
    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False
    logging.warning("python-dotenv not installed. .env file support disabled.")


class ConfigLoader:
    """Load and manage configuration from environment variables and config files."""
    
    def __init__(self, config_path: Optional[str] = None, load_dotenv_file: bool = True):
        """
        Initialize configuration loader.
        
        Args:
            config_path: Path to config.json file (default: ./config.json)
            load_dotenv_file: Whether to load .env file if it exists (default: True)
        """
        self.config_path = config_path or os.path.join(os.path.dirname(__file__), 'config.json')
        self.config = {}
        self.logger = self._setup_logger()
        
        # Load .env file if available and requested
        if load_dotenv_file and DOTENV_AVAILABLE:
            env_path = os.path.join(os.path.dirname(__file__), '.env')
            if os.path.exists(env_path):
                load_dotenv(env_path)
                self.logger.info("Loaded environment variables from .env file")
        
        # Load config.json
        self._load_config_file()
    
    def _setup_logger(self) -> logging.Logger:
        """Set up logger for config loader."""
        logger = logging.getLogger('config_loader')
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger
    
    def _load_config_file(self) -> None:
        """Load configuration from JSON file."""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    self.config = json.load(f)
                self.logger.info(f"Loaded configuration from {self.config_path}")
            else:
                self.logger.warning(f"Config file not found: {self.config_path}")
                self.config = {}
        except json.JSONDecodeError as e:
            self.logger.error(f"Error parsing config file: {e}")
            self.config = {}
        except Exception as e:
            self.logger.error(f"Error loading config file: {e}")
            self.config = {}
    
    def get_groq_api_key(self) -> Optional[str]:
        """
        Get GROQ API key from environment variable.
        
        Returns:
            GROQ API key or None if not found
        """
        api_key = os.environ.get('GROQ_API_KEY')
        if api_key:
            self.logger.debug("Using GROQ API key from environment variable")
            return api_key
        
        # Check config file (legacy support, not recommended)
        if 'GROQ_API_KEY' in self.config:
            self.logger.warning(
                "GROQ_API_KEY found in config file. "
                "For security, use environment variable instead."
            )
            return self.config.get('GROQ_API_KEY')
        
        return None
    
    def get_smtp_config(self) -> Dict[str, Any]:
        """
        Get SMTP configuration with environment variables taking precedence.
        
        Returns:
            Dictionary with SMTP configuration
        """
        smtp_config = {}
        
        # Get from environment variables (preferred)
        smtp_config['smtp_username'] = os.environ.get('SMTP_USERNAME')
        smtp_config['smtp_app_password'] = os.environ.get('SMTP_APP_PASSWORD')
        smtp_config['smtp_server'] = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
        smtp_config['smtp_port'] = int(os.environ.get('SMTP_PORT', '587'))
        smtp_config['smtp_use_ssl'] = os.environ.get('SMTP_USE_SSL', 'true').lower() == 'true'
        
        # Get advanced settings
        smtp_config['connection_timeout'] = int(os.environ.get('CONNECTION_TIMEOUT', '30'))
        smtp_config['retry_attempts'] = int(os.environ.get('RETRY_ATTEMPTS', '3'))
        smtp_config['retry_delay'] = int(os.environ.get('RETRY_DELAY', '5'))
        
        # Override with config file values if env vars not set
        if 'email_config' in self.config:
            email_config = self.config['email_config']
            for key in ['smtp_username', 'smtp_app_password', 'smtp_server', 
                       'smtp_port', 'smtp_use_ssl', 'connection_timeout',
                       'retry_attempts', 'retry_delay']:
                if not smtp_config.get(key):
                    smtp_config[key] = email_config.get(key)
        
        return smtp_config
    
    def get_box_email(self, bot_type: str) -> Optional[str]:
        """
        Get Box email address for the specified bot type.
        
        Args:
            bot_type: 'OHI' or 'HPV'
            
        Returns:
            Box email address or None if not found
        """
        bot_type = bot_type.upper()
        
        # Check environment variables first
        if bot_type == 'OHI':
            box_email = os.environ.get('OHI_BOX_EMAIL')
        elif bot_type == 'HPV':
            box_email = os.environ.get('HPV_BOX_EMAIL')
        else:
            raise ValueError(f"Unknown bot type: {bot_type}")
        
        if box_email:
            self.logger.debug(f"Using {bot_type} Box email from environment variable")
            return box_email
        
        # Check config file
        if 'email_config' in self.config:
            if bot_type == 'OHI':
                box_email = self.config['email_config'].get('ohi_box_email')
            elif bot_type == 'HPV':
                box_email = self.config['email_config'].get('hpv_box_email')
            
            if box_email:
                self.logger.warning(
                    f"{bot_type} Box email found in config file. "
                    "For security, use environment variable instead."
                )
                return box_email
        
        # Check legacy box_upload section
        if 'box_upload' in self.config:
            if bot_type == 'OHI':
                box_email = self.config['box_upload'].get('ohi_email')
            elif bot_type == 'HPV':
                box_email = self.config['box_upload'].get('hpv_email')
            
            if box_email:
                self.logger.warning(
                    f"{bot_type} Box email found in legacy config. "
                    "For security, use environment variable instead."
                )
                return box_email
        
        return None
    
    def get_config(self) -> Dict[str, Any]:
        """
        Get the full configuration dictionary.
        
        Returns:
            Configuration dictionary
        """
        return self.config
    
    def validate_required_env_vars(self, required_vars: list) -> Dict[str, bool]:
        """
        Validate that required environment variables are set.
        
        Args:
            required_vars: List of required environment variable names
            
        Returns:
            Dictionary mapping variable names to whether they are set
        """
        results = {}
        for var in required_vars:
            results[var] = bool(os.environ.get(var))
        return results
    
    def get_missing_env_vars(self, required_vars: list) -> list:
        """
        Get list of missing required environment variables.
        
        Args:
            required_vars: List of required environment variable names
            
        Returns:
            List of missing variable names
        """
        validation = self.validate_required_env_vars(required_vars)
        return [var for var, is_set in validation.items() if not is_set]


def load_config(config_path: Optional[str] = None) -> ConfigLoader:
    """
    Convenience function to load configuration.
    
    Args:
        config_path: Path to config.json file (optional)
        
    Returns:
        ConfigLoader instance
    """
    return ConfigLoader(config_path)


if __name__ == '__main__':
    # Test configuration loading
    print("Configuration Loader - Test Mode\n")
    
    loader = ConfigLoader()
    
    print("=== Environment Variables Check ===")
    required_vars = ['GROQ_API_KEY', 'SMTP_USERNAME', 'SMTP_APP_PASSWORD', 
                    'OHI_BOX_EMAIL', 'HPV_BOX_EMAIL']
    validation = loader.validate_required_env_vars(required_vars)
    
    for var, is_set in validation.items():
        status = "✅ SET" if is_set else "❌ NOT SET"
        print(f"{var}: {status}")
    
    missing = loader.get_missing_env_vars(required_vars)
    if missing:
        print(f"\n⚠️  Missing environment variables: {', '.join(missing)}")
        print("Please set these in your .env file or system environment.")
    else:
        print("\n✅ All required environment variables are set!")
    
    print("\n=== Configuration Summary ===")
    groq_key = loader.get_groq_api_key()
    print(f"GROQ API Key: {'✅ Configured' if groq_key else '❌ Not configured'}")
    
    smtp_config = loader.get_smtp_config()
    print(f"SMTP Server: {smtp_config.get('smtp_server', 'Not configured')}")
    print(f"SMTP Credentials: {'✅ Configured' if smtp_config.get('smtp_username') else '❌ Not configured'}")
    
    ohi_email = loader.get_box_email('OHI')
    hpv_email = loader.get_box_email('HPV')
    print(f"OHI Box Email: {'✅ Configured' if ohi_email else '❌ Not configured'}")
    print(f"HPV Box Email: {'✅ Configured' if hpv_email else '❌ Not configured'}")
