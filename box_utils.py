"""
Box Email Integration Utilities for MI Chatbots

This module provides a simplified interface for Box email integration,
wrapping the core functionality from box_integration.py with easy-to-use
functions for sending PDF reports to Box via email.

Features:
- Simple function-based interface for Box uploads
- Automatic bot type detection
- Integration with logging system
- Error handling and status reporting
"""

import io
from typing import Optional, Dict, Any
from box_integration import BoxUploader, BoxIntegrationError
from email_config import EmailConfig


def send_to_box(
    student_name: str,
    pdf_buffer: io.BytesIO,
    filename: str,
    bot_type: str,
    config_path: str = "config.json"
) -> Dict[str, Any]:
    """
    Send a PDF report to Box via email.
    
    Args:
        student_name: Name of the student
        pdf_buffer: BytesIO buffer containing PDF data
        filename: Name for the PDF file
        bot_type: Type of bot ('OHI' or 'HPV')
        config_path: Path to configuration file (default: config.json)
        
    Returns:
        Dictionary with upload status:
        - success: bool - Whether upload was successful
        - message: str - Status message
        - box_email: str - Box email address used (if available)
        - error: str - Error message (if failed)
    """
    result = {
        'success': False,
        'message': '',
        'box_email': None,
        'error': None
    }
    
    try:
        # Initialize uploader
        uploader = BoxUploader(bot_type, config_path)
        result['box_email'] = uploader._get_box_email()
        
        # Attempt upload
        success = uploader.upload_pdf_to_box(student_name, pdf_buffer, filename)
        
        if success:
            result['success'] = True
            result['message'] = f'Successfully uploaded {filename} to Box'
        else:
            result['message'] = 'Upload failed - check logs for details'
            result['error'] = 'Upload returned False'
            
    except BoxIntegrationError as e:
        result['message'] = f'Box integration error: {str(e)}'
        result['error'] = str(e)
    except Exception as e:
        result['message'] = f'Unexpected error: {str(e)}'
        result['error'] = str(e)
    
    return result


def get_box_email(bot_type: str, config_path: str = "config.json") -> Optional[str]:
    """
    Get the Box email address for a specific bot type.
    
    Args:
        bot_type: Type of bot ('OHI' or 'HPV')
        config_path: Path to configuration file (default: config.json)
        
    Returns:
        Box email address string, or None if not configured
    """
    try:
        uploader = BoxUploader(bot_type, config_path)
        return uploader._get_box_email()
    except Exception:
        return None


def is_box_enabled(config_path: str = "config.json") -> bool:
    """
    Check if Box upload is enabled in the configuration.
    
    Args:
        config_path: Path to configuration file (default: config.json)
        
    Returns:
        True if Box upload is enabled, False otherwise
    """
    try:
        email_config = EmailConfig(config_path)
        return email_config.is_box_enabled()
    except Exception:
        return False


def test_box_connection(bot_type: str, config_path: str = "config.json") -> Dict[str, Any]:
    """
    Test the Box email connection for a specific bot type.
    
    Args:
        bot_type: Type of bot ('OHI' or 'HPV')
        config_path: Path to configuration file (default: config.json)
        
    Returns:
        Dictionary with connection test results
    """
    try:
        uploader = BoxUploader(bot_type, config_path)
        return uploader.test_connection()
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'message': f'Failed to test connection: {str(e)}'
        }


# Example usage
if __name__ == "__main__":
    print("Box Utils - Test Mode\n")
    
    # Test getting Box emails
    print("Box Email Addresses:")
    ohi_email = get_box_email("OHI")
    hpv_email = get_box_email("HPV")
    print(f"  OHI: {ohi_email}")
    print(f"  HPV: {hpv_email}")
    
    # Test if Box is enabled
    print(f"\nBox Upload Enabled: {is_box_enabled()}")
    
    # Test connections
    print("\nConnection Tests:")
    for bot_type in ["OHI", "HPV"]:
        result = test_box_connection(bot_type)
        print(f"\n  {bot_type}:")
        print(f"    Status: {result.get('connection_test', 'unknown')}")
        print(f"    Message: {result.get('message', 'N/A')}")
